from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .question_bank import BANK_VERSION
from .scoring import Competency, Level


class Invitation(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Создано"
        SENT = "sent", "Приглашение отправлено"
        STARTED = "started", "В процессе"
        COMPLETED = "completed", "Завершено"
        EXPIRED = "expired", "Срок истёк"
        REVOKED = "revoked", "Отозвано"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(db_index=True)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    status = models.CharField(max_length=16, choices=Status, default=Status.CREATED, db_index=True)
    bank_version = models.CharField(max_length=32, default=BANK_VERSION, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    @classmethod
    def issue(cls, *, email: str, expires_at):
        raw_token = secrets.token_urlsafe(32)
        invitation = cls.objects.create(
            email=email,
            token_hash=cls.hash_token(raw_token),
            expires_at=expires_at,
        )
        return invitation, raw_token

    def accepts(self, raw_token: str, *, now=None) -> bool:
        now = now or timezone.now()
        valid_status = self.status in {self.Status.CREATED, self.Status.SENT, self.Status.STARTED}
        return valid_status and self.expires_at > now and hmac.compare_digest(
            self.token_hash, self.hash_token(raw_token)
        )


class Attempt(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invitation = models.OneToOneField(Invitation, on_delete=models.PROTECT, related_name="attempt")
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)


class Response(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="responses")
    question_id = models.CharField(max_length=8)
    value = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("attempt", "question_id"), name="one_answer_per_question")]


class CompetencyResult(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="results")
    competency = models.CharField(max_length=32, choices=[(item.value, item.name) for item in Competency])
    percentage = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    level = models.CharField(max_length=16, choices=[(item.value, item.name) for item in Level])

    class Meta:
        constraints = [models.UniqueConstraint(fields=("attempt", "competency"), name="one_result_per_competency")]


class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    invitation = models.ForeignKey(Invitation, null=True, blank=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=48, db_index=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

