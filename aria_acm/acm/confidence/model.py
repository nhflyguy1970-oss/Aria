"""Uncertainty & Confidence artifacts — M16."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class UncertaintyKind(StrEnum):
    KNOWN_UNKNOWN = "known_unknown"
    EVIDENCE = "evidence"
    PREDICTION = "prediction"
    SIMULATION = "simulation"
    LEARNING = "learning"
    REFLECTION = "reflection"
    STALE = "stale"
    OBSOLETE = "obsolete"


class EvidenceStatus(StrEnum):
    ACTIVE = "active"
    STALE = "stale"
    OBSOLETE = "obsolete"


@dataclass
class EvidenceInfluence:
    """Per-evidence influence on a living target — never deletes provenance or Experiences."""

    target_kind: str
    target_id: str
    experience_id: str
    weight: float = 1.0
    last_reinforced: float = 0.0
    created: float = 0.0
    status: EvidenceStatus = EvidenceStatus.ACTIVE

    @property
    def key(self) -> str:
        return f"{self.target_kind}:{self.target_id}:{self.experience_id}"

    def to_public(self) -> dict[str, Any]:
        return {
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "experience_id": self.experience_id,
            "weight": round(self.weight, 4),
            "last_reinforced": self.last_reinforced,
            "created": self.created,
            "status": self.status.value,
        }


@dataclass
class ConfidenceSnapshot:
    target_kind: str
    target_id: str
    value: float
    uncertainty_kinds: list[str] = field(default_factory=list)
    factors: dict[str, float] = field(default_factory=dict)
    explain: str = ""

    def to_public(self) -> dict[str, Any]:
        return {
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "value": round(self.value, 4),
            "uncertainty_kinds": list(self.uncertainty_kinds),
            "factors": {k: round(v, 4) for k, v in self.factors.items()},
            "explain": self.explain,
        }


@dataclass
class ConfidenceEvent:
    timestamp: float
    target_kind: str
    target_id: str
    before: float
    after: float
    source: str
    factors: list[str] = field(default_factory=list)
    summary: str = ""

    def to_public(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "before": round(self.before, 4),
            "after": round(self.after, 4),
            "source": self.source,
            "factors": list(self.factors),
            "summary": self.summary,
        }
