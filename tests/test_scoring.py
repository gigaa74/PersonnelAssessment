import unittest

from assessment.scoring import Competency, Level, ScoringItem, level_for, score_assessment


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.items = (
            ScoringItem("q1", Competency.DELEGATION),
            ScoringItem("q2", Competency.DELEGATION, reverse_keyed=True),
            ScoringItem("q3", Competency.COMPOSURE),
        )

    def test_scale_bounds_and_reverse_key(self):
        result = score_assessment(self.items, {"q1": 1, "q2": 5, "q3": 5})
        self.assertEqual(result[Competency.DELEGATION].percentage, 0)
        self.assertEqual(result[Competency.COMPOSURE].percentage, 100)
        result = score_assessment(self.items, {"q1": 5, "q2": 1, "q3": 3})
        self.assertEqual(result[Competency.DELEGATION].percentage, 100)

    def test_incomplete_attempt_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing responses"):
            score_assessment(self.items, {"q1": 3, "q2": 3})

    def test_level_boundaries(self):
        pairs = ((20, Level.VERY_LOW), (21, Level.LOW), (40, Level.LOW),
                 (41, Level.MEDIUM), (60, Level.MEDIUM), (61, Level.HIGH),
                 (80, Level.HIGH), (81, Level.VERY_HIGH))
        for value, expected in pairs:
            self.assertEqual(level_for(value), expected)


if __name__ == "__main__":
    unittest.main()

