from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .exports import csv_response, pdf_response, xlsx_response
from .forms import InvitationForm, ResponseForm
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
        )
        created_link = request.build_absolute_uri(
            reverse("assessment:open_invitation", args=(invitation.public_id, token))
        )
        send_invitation(invitation.email, created_link)
        invitation.status = Invitation.Status.SENT
        invitation.sent_at = timezone.now()
        invitation.save(update_fields=("status", "sent_at"))
        AuditEvent.objects.create(actor=request.user, invitation=invitation, event_type="invitation_created")
        form = InvitationForm()
    invitations = Invitation.objects.order_by("-created_at")
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
    return redirect("assessment:question", attempt_id=attempt.public_id, number=1)


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
    if not 1 <= number <= len(QUESTIONS):
        raise Http404
    item = QUESTIONS[number - 1]
    existing = Response.objects.filter(attempt=attempt, question_id=item.id).first()
    initial = {"value": existing.value} if existing else None
    form = ResponseForm(request.POST or None, initial=initial, answer_scale=ANSWER_SCALE)
    if request.method == "POST" and form.is_valid():
        Response.objects.update_or_create(
            attempt=attempt,
            question_id=item.id,
            defaults={"value": form.cleaned_data["value"]},
        )
        direction = request.POST.get("direction")
        if direction == "back" and number > 1:
            return redirect("assessment:question", attempt_id=attempt.public_id, number=number - 1)
        if number < len(QUESTIONS):
            return redirect("assessment:question", attempt_id=attempt.public_id, number=number + 1)
        answered = set(attempt.responses.values_list("question_id", flat=True))
        first_missing = next(
            (index for index, question_item in enumerate(QUESTIONS, 1) if question_item.id not in answered),
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
        "total": len(QUESTIONS),
        "progress": round(number / len(QUESTIONS) * 100),
        "attempt": attempt,
    })


def completed(request):
    return render(request, "assessment/completed.html")


def _completed_invitation(public_id):
    invitation = get_object_or_404(
        Invitation.objects.select_related("attempt"), public_id=public_id, status=Invitation.Status.COMPLETED
    )
    report = build_report(invitation.attempt.results.all())
    return invitation, report


@login_required
def result(request, public_id):
    invitation, report = _completed_invitation(public_id)
    AuditEvent.objects.create(actor=request.user, invitation=invitation, event_type="result_viewed")
    chart_data = [{"label": row.label, "value": row.percentage} for row in report["rows"]]
    return render(request, "assessment/result.html", {"invitation": invitation, "chart_data": chart_data, **report})


@login_required
def export_result(request, public_id, format_name):
    invitation, report = _completed_invitation(public_id)
    exporters = {"csv": csv_response, "xlsx": xlsx_response, "pdf": pdf_response}
    if format_name not in exporters:
        raise Http404
    AuditEvent.objects.create(actor=request.user, invitation=invitation, event_type=f"result_exported_{format_name}")
    return exporters[format_name](invitation, report)
