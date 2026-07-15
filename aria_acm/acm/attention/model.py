"""Attention & Memory Priority models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PriorityFactor(StrEnum):
    IDENTITY = "identity"
    GOAL = "goal"
    NOVELTY = "novelty"
    IMPORTANCE = "importance"
    REPETITION = "repetition"
    CONTEXT = "context"
    CONFLICT = "conflict"
    REFLECTION = "reflection"
    LEARNING = "learning"
    OFFLINE = "offline"
    CONFIDENCE = "confidence"
    SALIENCE = "salience"
    CUE = "cue"
    USER_PIN = "user_pin"


@dataclass
class AttentionAllocation:
    """Observable attention decision for a cognitive verb."""

    attention_class: str
    weight: float
    base_weight: float
    priority_boost: float
    factors: dict[str, float] = field(default_factory=dict)
    concept_ids: list[str] = field(default_factory=list)
    summary: str = ""

    def to_public(self) -> dict[str, Any]:
        return {
            "attention_class": self.attention_class,
            "weight": self.weight,
            "base_weight": self.base_weight,
            "priority_boost": self.priority_boost,
            "factors": dict(self.factors),
            "concept_ids": list(self.concept_ids),
            "summary": self.summary,
        }


@dataclass
class PriorityEvent:
    timestamp: float
    concept_id: str
    before: float
    after: float
    delta: float
    source: str
    factors: tuple[str, ...] = ()
    summary: str = ""
