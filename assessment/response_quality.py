from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import pvariance
from typing import Mapping

from .question_bank import QUESTIONS


@dataclass(frozen=True, slots=True)
class ResponseQuality:
    low_variability: bool
    extreme_positive_pattern: bool
    warnings: tuple[str, ...]


def evaluate_response_quality(responses: Mapping[str, int]) -> ResponseQuality:
    expected = {question.id for question in QUESTIONS}
    if set(responses) != expected:
        raise ValueError("response-quality analysis requires a complete attempt")
    values = list(responses.values())
    if any(isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5 for value in values):
        raise ValueError("responses must be integers from 1 to 5")

    low_variability = pvariance(values) < 0.20 or Counter(values).most_common(1)[0][1] >= 49
    positive_share = sum(value >= 4 for value in values) / len(values)
    negative_share_on_reverse = sum(
        responses[q.id] <= 2 for q in QUESTIONS if q.reverse_keyed
    ) / sum(q.reverse_keyed for q in QUESTIONS)
    extreme_positive = positive_share >= 0.85 and negative_share_on_reverse >= 0.85

    warnings = []
    if low_variability:
        warnings.append("Ответы имеют очень низкую вариативность; профиль следует интерпретировать осторожно.")
    if extreme_positive:
        warnings.append("Обнаружен почти исключительно социально предпочтительный профиль ответов.")
    return ResponseQuality(low_variability, extreme_positive, tuple(warnings))

