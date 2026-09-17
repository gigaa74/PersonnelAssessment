from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Mapping


class Competency(StrEnum):
    STRATEGIC_THINKING = "strategic_thinking"
    DELEGATION = "delegation"
    ACCOUNTABILITY = "accountability"
    COMMUNICATION = "communication"
    PERSISTENCE = "persistence"
    RESULT_ORIENTATION = "result_orientation"
    MOTIVATION = "motivation"
    COMPOSURE = "composure"
    MANAGEMENT = "management"


class Level(StrEnum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass(frozen=True, slots=True)
class ScoringItem:
    question_id: str
    competency: Competency
    reverse_keyed: bool = False
    weight: int = 1


@dataclass(frozen=True, slots=True)
class CompetencyScore:
    competency: Competency
    percentage: int
    level: Level


def level_for(value: int) -> Level:
    if not 0 <= value <= 100:
        raise ValueError("percentage must be between 0 and 100")
    return (
        Level.VERY_LOW if value <= 20 else Level.LOW if value <= 40
        else Level.MEDIUM if value <= 60 else Level.HIGH if value <= 80
        else Level.VERY_HIGH
    )


def score_assessment(items: Iterable[ScoringItem], responses: Mapping[str, int]):
    item_list = list(items)
    ids = [item.question_id for item in item_list]
    if not item_list or len(ids) != len(set(ids)):
        raise ValueError("assessment items must be non-empty and unique")
    missing = sorted(set(ids) - responses.keys())
    unexpected = sorted(responses.keys() - set(ids))
    if missing:
        raise ValueError(f"missing responses: {', '.join(missing)}")
    if unexpected:
        raise ValueError(f"unexpected responses: {', '.join(unexpected)}")
    totals, weights = {}, {}
    for item in item_list:
        value = responses[item.question_id]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"response for {item.question_id} must be an integer from 1 to 5")
        keyed = 6 - value if item.reverse_keyed else value
        totals[item.competency] = totals.get(item.competency, 0) + keyed * item.weight
        weights[item.competency] = weights.get(item.competency, 0) + item.weight
    result = {}
    for competency, total in totals.items():
        weight = weights[competency]
        percentage = round((total - weight) / (4 * weight) * 100)
        result[competency] = CompetencyScore(competency, percentage, level_for(percentage))
    return result

