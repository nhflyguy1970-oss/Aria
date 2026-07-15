"""Analogical Reasoning artifacts — explainable structure maps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalogyAlignment:
    source_concept_id: str
    target_concept_id: str
    source_label: str
    target_label: str
    relation: str
    strength: float
    why: list[str] = field(default_factory=list)

    def to_public(self) -> dict[str, Any]:
        return {
            "source_concept_id": self.source_concept_id,
            "target_concept_id": self.target_concept_id,
            "source_label": self.source_label,
            "target_label": self.target_label,
            "relation": self.relation,
            "strength": round(self.strength, 4),
            "why": list(self.why),
        }


@dataclass
class AnalogyMapping:
    id: str
    cue: str
    source_id: str
    target_id: str
    source_label: str
    target_label: str
    confidence: float
    alignments: list[AnalogyAlignment]
    created: float
    transfer_summary: str = ""
    why: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": "What existing memories are analogous even when they appear different?",
            "cue": self.cue,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "source_label": self.source_label,
            "target_label": self.target_label,
            "confidence": round(self.confidence, 4),
            "alignments": [a.to_public() for a in self.alignments],
            "transfer_summary": self.transfer_summary,
            "why": list(self.why),
            "plans": False,
            "decides": False,
            "executive": False,
        }
