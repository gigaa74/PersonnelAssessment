import unittest

from assessment.question_bank import BANK_VERSION, QUESTIONS, scoring_items, validate_bank
from assessment.response_quality import evaluate_response_quality
from assessment.scoring import Competency, score_assessment


class MethodologyTests(unittest.TestCase):
    def test_bank_is_structurally_valid(self):
        self.assertEqual(validate_bank(), ())
        self.assertEqual(BANK_VERSION, "1.0.0-draft")

    def test_bank_has_six_items_per_competency(self):
        for competency in Competency:
            self.assertEqual(sum(q.competency == competency for q in QUESTIONS), 6)

    def test_complete_neutral_attempt_scores_every_competency(self):
        responses = {question.id: 3 for question in QUESTIONS}
        scores = score_assessment(scoring_items(), responses)
        self.assertEqual(set(scores), set(Competency))
        self.assertTrue(all(score.percentage == 50 for score in scores.values()))

    def test_straight_line_responses_are_flagged(self):
        responses = {question.id: 3 for question in QUESTIONS}
        quality = evaluate_response_quality(responses)
        self.assertTrue(quality.low_variability)
        self.assertTrue(quality.warnings)

    def test_balanced_responses_are_not_flagged(self):
        responses = {
            question.id: (index % 5) + 1
            for index, question in enumerate(QUESTIONS)
        }
        quality = evaluate_response_quality(responses)
        self.assertFalse(quality.low_variability)


if __name__ == "__main__":
    unittest.main()

