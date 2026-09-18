from datetime import timedelta
import uuid

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .exports import csv_response, pdf_response, xlsx_response
from .cognitive_bank import CognitiveDomain, DOMAIN_LABELS, questions_for
from .forms import ConsentForm, InvitationForm, ResponseForm
from .mailer import send_invitation
from .models import Attempt, AuditEvent, Invitation, Response
from .question_bank import ANSWER_SCALE, QUESTIONS
from .reports import build_report
from .services import complete_attempt


def home(request):
    return redirect("assessment:dashboard")


@login_required
@require_http_methods(["GET", "POST"])
def dashboard(request):
    created_link = None
    form = InvitationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        invitation, token = Invitation.issue(
            email=form.cleaned_data["email"],
            expires_at=timezone.now() + timedelta(days=form.cleaned_data["validity_days"]),
            full_name=form.cleaned_data["full_name"],
            participant_type=form.cleaned_data["participant_type"],
            department=form.cleaned_data["department"],
            position=form.cleaned_data["position"],
            position_level=form.cleaned_data["position_level"],
        )
        created_link = request.build_absolute_uri(
            reverse("assessment:open_invitation", args=(invitation.public_id, token))
        )
        if invitation.email:
            send_invitation(invitation.email, created_link)
            invitation.status = Invitation.Status.SENT
            invitation.sent_at = timezone.now()
            invitation.save(update_fields=("status", "sent_at"))
        AuditEvent.objects.create(actor=request.user, invitation=invitation, event_type="invitation_created")
        form = InvitationForm()
    invitations = Invitation.objects.select_related("attempt").order_by("-created_at")
    status = request.GET.get("status", "")
    email = request.GET.get("email", "").strip()
    if status in Invitation.Status.values:
        invitations = invitations.filter(status=status)
    if email:
        invitations = invitations.filter(email__icontains=email)
    return render(request, "assessment/dashboard.html", {
        "form": form, "invitations": invitations[:100], "created_link": created_link,
        "statuses": Invitation.Status.choices, "selected_status": status, "email_filter": email,
    })


@transaction.atomic
def open_invitation(request, public_id, token):
    invitation = get_object_or_404(Invitation.objects.select_for_update(), public_id=public_id)
    if not invitation.accepts(token):
        return render(request, "assessment/link_unavailable.html", status=410)
    attempt, _ = Attempt.objects.get_or_create(invitation=invitation)
    if invitation.status != Invitation.Status.STARTED:
        invitation.status = Invitation.Status.STARTED
        invitation.save(update_fields=("status",))
        AuditEvent.objects.create(invitation=invitation, event_type="assessment_started")
    request.session["assessment_attempt"] = str(attempt.public_id)
    return redirect("assessment:welcome", attempt_id=attempt.public_id)


@require_http_methods(["GET", "POST"])
def welcome(request, attempt_id):
    attempt = _session_attempt(request, attempt_id)
    if attempt is None:
        return redirect("assessment:completed")
    if attempt.consented_at:
        return redirect("assessment:question", attempt_id=attempt.public_id, number=1)
    form = ConsentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        attempt.consented_at = timezone.now()
        attempt.save(update_fields=("consented_at", "updated_at"))
        AuditEvent.objects.create(invitation=attempt.invitation, event_type="assessment_consented")
        return redirect("assessment:question", attempt_id=attempt.public_id, number=1)
    return render(request, "assessment/welcome.html", {"attempt": attempt, "form": form})


def _session_attempt(request, attempt_id):
    if request.session.get("assessment_attempt") != str(attempt_id):
        raise Http404
    attempt = get_object_or_404(Attempt.objects.select_related("invitation"), public_id=attempt_id)
    if attempt.completed_at is not None:
        return None
    return attempt


@require_http_methods(["GET", "POST"])
def question(request, attempt_id, number):
    attempt = _session_attempt(request, attempt_id)
    if attempt is None:
        return redirect("assessment:completed")
    if not attempt.consented_at:
        return redirect("assessment:welcome", attempt_id=attempt.public_id)
    questions = list(QUESTIONS) if attempt.invitation.bank_version == "1.0.0-draft" else [*questions_for(attempt.invitation.bank_version, attempt.invitation.position_level), *QUESTIONS]
    if not 1 <= number <= len(questions):
        raise Http404
    item = questions[number - 1]
    existing = Response.objects.filter(attempt=attempt, question_id=item.id).first()
    initial = {"value": existing.value} if existing else None
    answer_scale = item.choices if hasattr(item, "choices") else ANSWER_SCALE
    form = ResponseForm(request.POST or None, initial=initial, answer_scale=answer_scale)
    if request.method == "POST" and form.is_valid():
        Response.objects.update_or_create(
            attempt=attempt,
            question_id=item.id,
            defaults={"value": form.cleaned_data["value"]},
        )
        direction = request.POST.get("direction")
        if direction == "back" and number > 1:
            return redirect("assessment:question", attempt_id=attempt.public_id, number=number - 1)
        if number < len(questions):
            return redirect("assessment:question", attempt_id=attempt.public_id, number=number + 1)
        answered = set(attempt.responses.values_list("question_id", flat=True))
        first_missing = next(
            (index for index, question_item in enumerate(questions, 1) if question_item.id not in answered),
            None,
        )
        if first_missing is not None:
            return redirect("assessment:question", attempt_id=attempt.public_id, number=first_missing)
        complete_attempt(attempt.pk)
        request.session.pop("assessment_attempt", None)
        return redirect("assessment:completed")
    return render(request, "assessment/question.html", {
        "form": form,
        "question": item,
        "number": number,
        "total": len(questions),
        "progress": round(number / len(questions) * 100),
        "attempt": attempt,
        "module_label": "Когнитивные способности" if hasattr(item, "choices") else "Рабочее поведение",
    })


def completed(request):
    return render(request, "assessment/completed.html")


def _completed_invitation(public_id):
    invitation = get_object_or_404(
        Invitation.objects.select_related("attempt"), public_id=public_id, status=Invitation.Status.COMPLETED
    )
    report = build_report(invitation.attempt.results.all())
    cognitive = []
    for item in invitation.attempt.cognitive_results.all():
        label = "Общий показатель" if item.domain == "overall" else DOMAIN_LABELS[CognitiveDomain(item.domain)]
        if item.percentage >= 80:
            interpretation = "Высокая точность решения задач этого типа. Результат стоит проверить на более сложных рабочих кейсах."
        elif item.percentage >= 60:
            interpretation = "Уверенный базовый результат. Большинство задач решено верно."
        elif item.percentage >= 40:
            interpretation = "Базовый уровень проявляется неравномерно. Полезно уточнить стратегию решения задач на интервью."
        else:
            interpretation = "Задания этого типа вызвали затруднения. Результат следует сопоставить с опытом, языком и условиями прохождения."
        cognitive.append({"label": label, "percentage": item.percentage, "correct": item.correct, "total": item.total, "interpretation": interpretation})
    cognitive.sort(key=lambda row: (row["label"] != "Общий показатель", row["label"]))
    event = invitation.auditevent_set.filter(event_type="assessment_completed").order_by("-occurred_at").first()
    quality_warnings = []
    if event and event.metadata.get("low_variability"):
        quality_warnings.append("Ответы имеют очень низкую вариативность; профиль следует проверить на интервью.")
    if event and event.metadata.get("extreme_positive_pattern"):
        quality_warnings.append("Профиль содержит почти исключительно социально предпочтительные ответы.")
    report.update({"cognitive": cognitive, "quality_warnings": quality_warnings})
    return invitation, report


@login_required
def result(request, public_id):
    invitation, report = _completed_invitation(public_id)
    AuditEvent.objects.create(actor=request.user, invitation=invitation, event_type="result_viewed")
    chart_data = [{"label": row.label, "value": row.percentage} for row in report["rows"]]
    return render(request, "assessment/result.html", {"invitation": invitation, "chart_data": chart_data, **report})


@login_required
@require_POST
@transaction.atomic
def delete_invitation(request, public_id):
    invitation = get_object_or_404(Invitation.objects.select_for_update(), public_id=public_id)
    _delete_invitations([invitation.pk])
    return redirect("assessment:dashboard")


def _delete_invitations(invitation_ids):
    AuditEvent.objects.filter(invitation_id__in=invitation_ids).delete()
    Attempt.objects.filter(invitation_id__in=invitation_ids).delete()
    Invitation.objects.filter(pk__in=invitation_ids).delete()


@login_required
@require_POST
@transaction.atomic
def delete_selected_invitations(request):
    public_ids = []
    for raw_value in request.POST.getlist("selected"):
        try:
            public_ids.append(uuid.UUID(raw_value))
        except (ValueError, AttributeError):
            continue
    invitation_ids = list(
        Invitation.objects.select_for_update().filter(public_id__in=public_ids).values_list("pk", flat=True)
    )
    if invitation_ids:
        _delete_invitations(invitation_ids)
    return redirect("assessment:dashboard")


@login_required
def export_result(request, public_id, format_name):
    invitation, report = _completed_invitation(public_id)
    exporters = {"csv": csv_response, "xlsx": xlsx_response, "pdf": pdf_response}
    if format_name not in exporters:
        raise Http404
    AuditEvent.objects.create(actor=request.user, invitation=invitation, event_type=f"result_exported_{format_name}")
    return exporters[format_name](invitation, report)
