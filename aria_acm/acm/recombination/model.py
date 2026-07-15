"""Memory Recombination artifacts — novel blends; never historical Experiences."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecombinedFragment:
    concept_id: str
    label: str
    role: str  # seed | blend | bridge
    source_experience_ids: list[str] = field(default_factory=list)

    def to_public(self) -> dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "label": self.label,
            "role": self.role,
            "source_experience_ids": list(self.source_experience_ids),
        }


@dataclass
class RecombinedMemory:
    id: str
    cue: str
    fragments: list[RecombinedFragment]
    novelty: float
    confidence: float
    created: float
    summary: str = ""
    domains: list[str] = field(default_factory=list)
    simulation_id: str = ""
    prediction_id: str = ""
    recombined: bool = True
    historical: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": "What new memories can emerge by recombining existing memories?",
            "cue": self.cue,
            "fragments": [f.to_public() for f in self.fragments],
            "novelty": round(self.novelty, 4),
            "confidence": round(self.confidence, 4),
            "summary": self.summary,
            "domains": list(self.domains),
            "simulation_id": self.simulation_id,
            "prediction_id": self.prediction_id,
            "recombined": True,
            "historical": False,
            "plans": False,
            "decides": False,
        }
