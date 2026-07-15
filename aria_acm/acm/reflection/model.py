"""Reflection evaluation products — metacognitive, not reasoning dumps."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ReflectionOutcome(StrEnum):
    SUFFICIENT = "sufficient"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNCERTAINTY = "uncertainty"
    CONTRADICTION = "contradiction"
    CONSISTENCY = "consistency"
    PATTERN = "pattern"
    QUESTION = "question"
    HYPOTHESIS = "hypothesis"
    INSIGHT = "insight"
    UNKNOWN = "unknown"


@dataclass
class ReflectionEvaluation:
    """Observable evaluation of a Remembering reconstruction."""

    cue: str
    remembered_answer: str
    remembered_confidence: float
    confidence_assessment: float
    outcomes: list[ReflectionOutcome] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    consistencies: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    insufficient_evidence: bool = False
    ambiguous: bool = False
    evaluation_summary: str = ""
    reflective_experience_id: str = ""
    reflects_on_id: str = ""
    activated_concept_ids: list[str] = field(default_factory=list)
    association_ids: list[str] = field(default_factory=list)
    experience_ids: list[str] = field(default_factory=list)
    reconstruction: dict[str, Any] = field(default_factory=dict)
    activation_reused: bool = True

    def to_public(self) -> dict[str, Any]:
        return {
            "question": "What do I think about what I remember?",
            "answer": self.evaluation_summary,
            "remembered_answer": self.remembered_answer,
            "remembered_confidence": round(self.remembered_confidence, 4),
            "confidence_assessment": round(self.confidence_assessment, 4),
            "outcomes": [o.value for o in self.outcomes],
            "contradictions": list(self.contradictions),
            "consistencies": list(self.consistencies),
            "patterns": list(self.patterns),
            "questions": list(self.questions),
            "hypotheses": list(self.hypotheses),
            "insufficient_evidence": self.insufficient_evidence,
            "ambiguous": self.ambiguous,
            "reflective_experience_id": self.reflective_experience_id,
            "reflects_on_id": self.reflects_on_id,
            "activated_concept_ids": list(self.activated_concept_ids),
            "association_ids": list(self.association_ids),
            "experience_ids": list(self.experience_ids),
            "activation_reused": self.activation_reused,
            "reconstruction": self.reconstruction,
        }
