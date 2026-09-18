from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assessment.cognitive_bank import QUESTIONS as COGNITIVE_QUESTIONS, validate_bank
from assessment.models import Attempt, CognitiveResult, CompetencyResult, Invitation, Response
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
            "full_name": "Иван Петров", "email": "person@example.com",
            "participant_type": "employee", "department": "unit_1",
            "position": "Мастер", "position_level": "leader", "validity_days": 7,
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

    def start(self):
        open_url = reverse("assessment:open_invitation", args=(self.invitation.public_id, self.token))
        response = self.client.get(open_url)
        attempt = Attempt.objects.get(invitation=self.invitation)
        self.assertRedirects(response, reverse("assessment:welcome", args=(attempt.public_id,)))
        response = self.client.post(reverse("assessment:welcome", args=(attempt.public_id,)), {"consent": "on"})
        self.assertRedirects(response, reverse("assessment:question", args=(attempt.public_id, 1)))
        return attempt

    def test_invalid_token_returns_gone(self):
        url = reverse("assessment:open_invitation", args=(self.invitation.public_id, "wrong"))
        self.assertEqual(self.client.get(url).status_code, 410)

    def test_question_url_requires_bound_session(self):
        attempt = Attempt.objects.create(invitation=self.invitation)
        url = reverse("assessment:question", args=(attempt.public_id, 1))
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_cannot_finish_with_missing_answers(self):
        attempt = self.start()
        all_questions = [*COGNITIVE_QUESTIONS, *QUESTIONS]
        last_url = reverse("assessment:question", args=(attempt.public_id, len(all_questions)))
        response = self.client.post(last_url, {"value": 3, "direction": "next"})
        self.assertRedirects(response, reverse("assessment:question", args=(attempt.public_id, 1)))
        self.assertFalse(CompetencyResult.objects.exists())

    def test_complete_assessment_is_single_use_and_creates_results(self):
        open_url = reverse("assessment:open_invitation", args=(self.invitation.public_id, self.token))
        attempt = self.start()
        all_questions = [*COGNITIVE_QUESTIONS, *QUESTIONS]
        for number, question in enumerate(all_questions, 1):
            url = reverse("assessment:question", args=(attempt.public_id, number))
            value = question.correct if hasattr(question, "correct") else 3
            response = self.client.post(url, {"value": value, "direction": "next"})

        self.assertRedirects(response, reverse("assessment:completed"))
        self.assertEqual(Response.objects.filter(attempt=attempt).count(), 84)
        self.assertEqual(CompetencyResult.objects.filter(attempt=attempt).count(), len(Competency))
        self.assertEqual(CognitiveResult.objects.filter(attempt=attempt).count(), 5)
        self.invitation.refresh_from_db()
        attempt.refresh_from_db()
        self.assertEqual(self.invitation.status, Invitation.Status.COMPLETED)
        self.assertIsNotNone(attempt.completed_at)
        self.assertEqual(self.client.get(open_url).status_code, 410)

    def test_cognitive_bank_is_complete(self):
        self.assertEqual(validate_bank(), ())
        self.assertEqual(len(COGNITIVE_QUESTIONS), 30)


class ResultAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("admin", password="strong-test-password")
        self.invitation, token = Invitation.issue(
            email="result@example.com", expires_at=timezone.now() + timedelta(days=1)
        )
        self.client.get(reverse("assessment:open_invitation", args=(self.invitation.public_id, token)))
        self.attempt = Attempt.objects.get(invitation=self.invitation)
        self.client.post(reverse("assessment:welcome", args=(self.attempt.public_id,)), {"consent": "on"})
        all_questions = [*COGNITIVE_QUESTIONS, *QUESTIONS]
        for number, question in enumerate(all_questions, 1):
            self.client.post(
                reverse("assessment:question", args=(self.attempt.public_id, number)),
                {"value": question.correct if hasattr(question, "correct") else (number % 5) + 1, "direction": "next"},
            )

    def test_result_and_exports_require_login(self):
        result_url = reverse("assessment:result", args=(self.invitation.public_id,))
        self.assertEqual(self.client.get(result_url).status_code, 302)
        for kind in ("csv", "xlsx", "pdf"):
            url = reverse("assessment:export_result", args=(self.invitation.public_id, kind))
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_authenticated_administrator_can_view_and_export(self):
        self.client.force_login(self.user)
        result = self.client.get(reverse("assessment:result", args=(self.invitation.public_id,)))
        self.assertContains(result, "Результаты оценки")
        self.assertContains(result, "Стратегическое мышление")
        self.assertContains(result, "Стрессоустойчивость")
        self.assertContains(result, "Проявление в работе")
        self.assertContains(result, "Возможный риск")
        self.assertContains(result, "Вопросы для интервью")
        self.assertContains(result, "Когнитивные задачи")
        self.assertContains(result, "не стандартизированный тест IQ")
        self.assertContains(result, "Время прохождения")
        signatures = {"csv": b"\xef\xbb\xbf", "xlsx": b"PK", "pdf": b"%PDF"}
        for kind, signature in signatures.items():
            response = self.client.get(
                reverse("assessment:export_result", args=(self.invitation.public_id, kind))
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.content.startswith(signature), kind)
