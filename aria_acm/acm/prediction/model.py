"""Prediction artifacts — probable memory outcomes (never plans)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class HypothesisStatus(StrEnum):
    ACTIVE = "active"
    DISPROVED = "disproved"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class ComparisonKind(StrEnum):
    HIT = "hit"
    PARTIAL = "partial"
    MISS = "miss"


@dataclass
class PredictedOutcome:
    concept_id: str
    label: str
    probability: float
    support: list[str] = field(default_factory=list)  # association / evidence ids
    why: list[str] = field(default_factory=list)  # cue/factor classes — not CoT

    def to_public(self) -> dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "label": self.label,
            "probability": round(self.probability, 4),
            "support": list(self.support),
            "why": list(self.why),
        }


@dataclass
class Prediction:
    id: str
    cue: str
    outcomes: list[PredictedOutcome]
    confidence: float
    created: float
    evaluated: bool = False
    accuracy: float | None = None
    hypothetical: bool = False  # predictions are expectations about reality, not sims
    source_concept_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": "Based upon memory, what is likely?",
            "cue": self.cue,
            "outcomes": [o.to_public() for o in self.outcomes],
            "confidence": round(self.confidence, 4),
            "evaluated": self.evaluated,
            "accuracy": self.accuracy,
            "source_concept_ids": list(self.source_concept_ids),
            "last_audit_id": self.metadata.get("last_audit_id"),
            "hypothesis_ids": list(self.metadata.get("hypothesis_ids") or []),
            "plans": False,
            "decides": False,
        }


@dataclass
class Hypothesis:
    """Competing memory claim — status lifecycle only; never invents Experiences."""

    id: str
    claim: str
    confidence: float
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    supporting_ids: list[str] = field(default_factory=list)
    conflicting_ids: list[str] = field(default_factory=list)
    prediction_id: str = ""
    simulation_id: str = ""
    reflective_experience_id: str = ""
    concept_id: str = ""
    superseded_by: str = ""
    withdrawn_reason: str = ""
    created: float = 0.0
    closed_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "claim": self.claim,
            "confidence": round(self.confidence, 4),
            "status": self.status.value,
            "supporting_ids": list(self.supporting_ids),
            "conflicting_ids": list(self.conflicting_ids),
            "prediction_id": self.prediction_id,
            "concept_id": self.concept_id,
            "superseded_by": self.superseded_by,
            "withdrawn_reason": self.withdrawn_reason,
            "created": self.created,
            "closed_at": self.closed_at,
            "plans": False,
            "decides": False,
        }


@dataclass
class PredictionAudit:
    """Append-only prediction → outcome → calibration trail. Never rewrite history."""

    id: str
    prediction_id: str
    observed_concept_id: str = ""
    observed_experience_id: str = ""
    comparison: ComparisonKind = ComparisonKind.MISS
    hit_rank: int | None = None
    expected_top_label: str = ""
    realized_label: str = ""
    accuracy: float = 0.0
    confidence_before: float = 0.0
    confidence_after: float = 0.0
    calibration_delta: float = 0.0
    confidence_event_ids: list[str] = field(default_factory=list)
    adaptation_ids: list[str] = field(default_factory=list)
    hypothesis_updates: list[str] = field(default_factory=list)
    explanation: str = ""
    created: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "prediction_id": self.prediction_id,
            "observed_concept_id": self.observed_concept_id,
            "observed_experience_id": self.observed_experience_id,
            "comparison": self.comparison.value,
            "hit_rank": self.hit_rank,
            "expected_top_label": self.expected_top_label,
            "realized_label": self.realized_label,
            "accuracy": round(self.accuracy, 4),
            "confidence_before": round(self.confidence_before, 4),
            "confidence_after": round(self.confidence_after, 4),
            "calibration_delta": round(self.calibration_delta, 4),
            "confidence_event_ids": list(self.confidence_event_ids),
            "adaptation_ids": list(self.adaptation_ids),
            "hypothesis_updates": list(self.hypothesis_updates),
            "explanation": self.explanation,
            "created": self.created,
            "plans": False,
            "decides": False,
        }
