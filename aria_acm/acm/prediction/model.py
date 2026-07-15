"""Prediction artifacts — probable memory outcomes (never plans)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
            "plans": False,
            "decides": False,
        }
