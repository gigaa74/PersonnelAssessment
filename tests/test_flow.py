from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assessment.models import Attempt, CompetencyResult, Invitation, Response
from assessment.question_bank import QUESTIONS
from assessment.scoring import Competency


class AdministratorFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("admin", password="strong-test-password")

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("assessment:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_administrator_can_create_invitation(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("assessment:dashboard"), {
            "email": "person@example.com", "validity_days": 7,
        })
        self.assertEqual(response.status_code, 200)
        invitation = Invitation.objects.get()
        self.assertContains(response, str(invitation.public_id))
        self.assertNotContains(response, invitation.token_hash)


class RespondentFlowTests(TestCase):
    def setUp(self):
        self.invitation, self.token = Invitation.issue(
            email="person@example.com",
            expires_at=timezone.now() + timedelta(days=7),
        )

    def test_invalid_token_returns_gone(self):
        url = reverse("assessment:open_invitation", args=(self.invitation.public_id, "wrong"))
        self.assertEqual(self.client.get(url).status_code, 410)

    def test_question_url_requires_bound_session(self):
        attempt = Attempt.objects.create(invitation=self.invitation)
        url = reverse("assessment:question", args=(attempt.public_id, 1))
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_cannot_finish_with_missing_answers(self):
        open_url = reverse("assessment:open_invitation", args=(self.invitation.public_id, self.token))
        self.client.get(open_url)
        attempt = Attempt.objects.get(invitation=self.invitation)
        last_url = reverse("assessment:question", args=(attempt.public_id, len(QUESTIONS)))
        response = self.client.post(last_url, {"value": 3, "direction": "next"})
        self.assertRedirects(response, reverse("assessment:question", args=(attempt.public_id, 1)))
        self.assertFalse(CompetencyResult.objects.exists())

    def test_complete_assessment_is_single_use_and_creates_results(self):
        open_url = reverse("assessment:open_invitation", args=(self.invitation.public_id, self.token))
        response = self.client.get(open_url)
        attempt = Attempt.objects.get(invitation=self.invitation)
        self.assertRedirects(response, reverse("assessment:question", args=(attempt.public_id, 1)))

        for number, _question in enumerate(QUESTIONS, 1):
            url = reverse("assessment:question", args=(attempt.public_id, number))
            response = self.client.post(url, {"value": 3, "direction": "next"})

        self.assertRedirects(response, reverse("assessment:completed"))
        self.assertEqual(Response.objects.filter(attempt=attempt).count(), 54)
        self.assertEqual(CompetencyResult.objects.filter(attempt=attempt).count(), len(Competency))
        self.invitation.refresh_from_db()
        attempt.refresh_from_db()
        self.assertEqual(self.invitation.status, Invitation.Status.COMPLETED)
        self.assertIsNotNone(attempt.completed_at)
        self.assertEqual(self.client.get(open_url).status_code, 410)
