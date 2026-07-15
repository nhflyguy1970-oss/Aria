"""Reconstruction records — cognitive products of Remembering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CompetingRecollection:
    concept_id: str
    label: str
    energy: float
    confidence: float
    answer_preview: str


@dataclass
class Reconstruction:
    """A remembered reconstruction — never a rewritten Experience."""

    cue: str
    answer: str
    explanation_class: str
    confidence: float
    primary_concept_id: str = ""
    primary_label: str = ""
    activated_concept_ids: list[str] = field(default_factory=list)
    association_ids: list[str] = field(default_factory=list)
    experience_ids: list[str] = field(default_factory=list)
    experience_summaries: list[str] = field(default_factory=list)
    competing: list[CompetingRecollection] = field(default_factory=list)
    ambiguous: bool = False
    goal_influenced: bool = False
    identity_influenced: bool = False
    context_influenced: bool = False
    working_influenced: bool = False
    activation: dict[str, Any] = field(default_factory=dict)
    cue_classes: list[str] = field(default_factory=list)

    def to_public(self) -> dict[str, Any]:
        return {
            "question": "What do I remember?",
            "answer": self.answer,
            "confidence": self.confidence,
            "ambiguous": self.ambiguous,
            "explanation_class": self.explanation_class,
            "primary_concept_id": self.primary_concept_id,
            "primary_label": self.primary_label,
            "activated_concept_ids": list(self.activated_concept_ids),
            "association_ids": list(self.association_ids),
            "experience_ids": list(self.experience_ids),
            "experience_summaries": list(self.experience_summaries),
            "competing": [
                {
                    "concept_id": c.concept_id,
                    "label": c.label,
                    "energy": round(c.energy, 4),
                    "confidence": round(c.confidence, 4),
                    "answer_preview": c.answer_preview,
                }
                for c in self.competing
            ],
            "goal_influenced": self.goal_influenced,
            "identity_influenced": self.identity_influenced,
            "context_influenced": self.context_influenced,
            "working_influenced": self.working_influenced,
            "cue_classes": list(self.cue_classes),
            "activation": self.activation,
        }
