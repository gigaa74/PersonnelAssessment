from django.db import transaction
from django.utils import timezone

from .cognitive_bank import DOMAIN_LABELS, questions_for
from .models import Attempt, AuditEvent, CognitiveResult, CompetencyResult, Invitation
from .question_bank import scoring_items
from .response_quality import evaluate_response_quality
from .scoring import score_assessment


@transaction.atomic
def complete_attempt(attempt_id: int):
    attempt = Attempt.objects.select_for_update().select_related("invitation").get(pk=attempt_id)
    if attempt.completed_at is not None:
        return attempt
    responses = {row.question_id: row.value for row in attempt.responses.all()}
    behavior_ids = {item.question_id for item in scoring_items()}
    behavior_responses = {key: value for key, value in responses.items() if key in behavior_ids}
    scores = score_assessment(scoring_items(), behavior_responses)
    quality = evaluate_response_quality(behavior_responses)
    CompetencyResult.objects.bulk_create([
        CompetencyResult(
            attempt=attempt,
            competency=competency.value,
            percentage=score.percentage,
            level=score.level.value,
        )
        for competency, score in scores.items()
    ])
    cognitive_rows = []
    if attempt.invitation.bank_version != "1.0.0-draft":
        cognitive_questions = questions_for(attempt.invitation.bank_version, attempt.invitation.position_level)
        for domain in DOMAIN_LABELS:
            items = [item for item in cognitive_questions if item.domain == domain]
            correct = sum(responses.get(item.id) == item.correct for item in items)
            cognitive_rows.append(CognitiveResult(
                attempt=attempt, domain=domain.value, correct=correct, total=len(items),
                percentage=round(correct / len(items) * 100),
            ))
        correct = sum(responses.get(item.id) == item.correct for item in cognitive_questions)
        cognitive_rows.append(CognitiveResult(
            attempt=attempt, domain="overall", correct=correct, total=len(cognitive_questions),
            percentage=round(correct / len(cognitive_questions) * 100),
        ))
        CognitiveResult.objects.bulk_create(cognitive_rows)
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
            "cognitive_completed": bool(cognitive_rows),
        },
    )
    return attempt, quality
