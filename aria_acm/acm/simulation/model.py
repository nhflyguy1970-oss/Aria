"""Mental Simulation artifacts — hypothetical only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HypotheticalStep:
    index: int
    concept_id: str
    label: str
    summary: str
    source_experience_ids: list[str] = field(default_factory=list)
    hypothetical: bool = True

    def to_public(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "concept_id": self.concept_id,
            "label": self.label,
            "summary": self.summary,
            "source_experience_ids": list(self.source_experience_ids),
            "hypothetical": True,
        }


@dataclass
class Simulation:
    id: str
    cue: str
    branch: int
    steps: list[HypotheticalStep]
    confidence: float
    created: float
    source_concept_ids: list[str] = field(default_factory=list)
    prediction_id: str = ""
    hypothetical: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": "What possible futures can memory imagine?",
            "cue": self.cue,
            "branch": self.branch,
            "steps": [s.to_public() for s in self.steps],
            "confidence": round(self.confidence, 4),
            "source_concept_ids": list(self.source_concept_ids),
            "prediction_id": self.prediction_id,
            "hypothetical": True,
            "historical": False,
            "plans": False,
            "decides": False,
        }
