from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from assessment.models import Invitation
from assessment.question_bank import BANK_VERSION


class InvitationModelTests(TestCase):
    def test_raw_token_is_returned_but_never_stored(self):
        invitation, raw_token = Invitation.issue(
            email="respondent@example.com",
            expires_at=timezone.now() + timedelta(days=3),
        )
        self.assertNotEqual(invitation.token_hash, raw_token)
        self.assertEqual(len(invitation.token_hash), 64)
        self.assertTrue(invitation.accepts(raw_token))
        self.assertEqual(invitation.bank_version, BANK_VERSION)

    def test_wrong_or_expired_token_is_rejected(self):
        invitation, raw_token = Invitation.issue(
            email="respondent@example.com",
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        self.assertFalse(invitation.accepts(raw_token))
        invitation.expires_at = timezone.now() + timedelta(days=1)
        self.assertFalse(invitation.accepts("wrong-token"))

    def test_completed_invitation_cannot_be_reused(self):
        invitation, raw_token = Invitation.issue(
            email="respondent@example.com",
            expires_at=timezone.now() + timedelta(days=1),
        )
        invitation.status = Invitation.Status.COMPLETED
        self.assertFalse(invitation.accepts(raw_token))
