from django.db import transaction
from django.utils import timezone

from .models import Attempt, AuditEvent, CompetencyResult, Invitation
from .question_bank import scoring_items
from .response_quality import evaluate_response_quality
from .scoring import score_assessment


@transaction.atomic
def complete_attempt(attempt_id: int):
    attempt = Attempt.objects.select_for_update().select_related("invitation").get(pk=attempt_id)
    if attempt.completed_at is not None:
        return attempt
    responses = {row.question_id: row.value for row in attempt.responses.all()}
    scores = score_assessment(scoring_items(), responses)
    quality = evaluate_response_quality(responses)
    CompetencyResult.objects.bulk_create([
        CompetencyResult(
            attempt=attempt,
            competency=competency.value,
            percentage=score.percentage,
            level=score.level.value,
        )
        for competency, score in scores.items()
    ])
    now = timezone.now()
    attempt.completed_at = now
    attempt.save(update_fields=("completed_at", "updated_at"))
    invitation = attempt.invitation
    invitation.status = Invitation.Status.COMPLETED
    invitation.completed_at = now
    invitation.save(update_fields=("status", "completed_at"))
    AuditEvent.objects.create(
        invitation=invitation,
        event_type="assessment_completed",
        metadata={
            "low_variability": quality.low_variability,
            "extreme_positive_pattern": quality.extreme_positive_pattern,
        },
    )
    return attempt, quality
