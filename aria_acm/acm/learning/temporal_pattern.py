"""Temporal patterns — long-term routines/schedules (M5 Cap5).

Evidence-based. Never invent Experiences. Weaken when unobserved (Cap2-aligned).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PatternKind(StrEnum):
    ROUTINE = "routine"
    SCHEDULE = "schedule"
    SEASONAL = "seasonal"
    RECURRING = "recurring"
    PERIODIC = "periodic"
    TREND = "trend"
    HABIT = "habit"


class PatternStatus(StrEnum):
    ACTIVE = "active"
    WEAKENING = "weakening"
    DORMANT = "dormant"
    RETIRED = "retired"


@dataclass
class TemporalPattern:
    """Living temporal regularity derived from Experiences — never invents memory."""

    id: str
    label: str
    kind: PatternKind = PatternKind.HABIT
    status: PatternStatus = PatternStatus.ACTIVE
    antecedent: str = ""
    consequent: str = ""
    period_hint: str = ""  # morning | saturday | weekly | seasonal | daily | …
    confidence: float = 0.4
    strength: float = 0.4
    observation_count: int = 0
    supporting_experience_ids: list[str] = field(default_factory=list)
    supporting_concept_ids: list[str] = field(default_factory=list)
    first_observed: float = 0.0
    last_observed: float = 0.0
    last_weakened: float = 0.0
    retired_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "kind": self.kind.value,
            "status": self.status.value,
            "antecedent": self.antecedent,
            "consequent": self.consequent,
            "period_hint": self.period_hint,
            "confidence": round(self.confidence, 4),
            "strength": round(self.strength, 4),
            "observation_count": self.observation_count,
            "supporting_experience_ids": list(self.supporting_experience_ids),
            "supporting_concept_ids": list(self.supporting_concept_ids),
            "first_observed": self.first_observed,
            "last_observed": self.last_observed,
            "last_weakened": self.last_weakened,
            "retired_at": self.retired_at,
            "invents_experiences": False,
        }
