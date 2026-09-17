from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import InvitationForm, ResponseForm
from .models import Attempt, AuditEvent, Invitation, Response
from .question_bank import ANSWER_SCALE, QUESTIONS
from .services import complete_attempt


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
        AuditEvent.objects.create(actor=request.user, invitation=invitation, event_type="invitation_created")
        form = InvitationForm()
    invitations = Invitation.objects.order_by("-created_at")[:100]
    return render(request, "assessment/dashboard.html", {
        "form": form, "invitations": invitations, "created_link": created_link,
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
