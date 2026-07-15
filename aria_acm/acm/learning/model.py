"""Adaptation Records — auditable Learning artifacts (never Experience rewrites)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AdaptationTarget(StrEnum):
    CONCEPT = "concept"
    ASSOCIATION = "association"
    IDENTITY_CONCEPT = "identity_concept"
    PREFERENCE_ATTRIBUTE = "preference_attribute"
    GOAL = "goal"


class GovernanceClass(StrEnum):
    AUTOMATIC = "automatic"
    PROPOSED = "proposed"
    ASSENTED = "assented"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"
    ABSTAINED = "abstained"


class AdaptationKind(StrEnum):
    REINFORCE = "reinforce"
    WEAKEN = "weaken"
    GENERALIZE = "generalize"
    CONFIDENCE = "confidence"
    STABILIZE = "stabilize"
    ROLLBACK = "rollback"
    ABSTAIN = "abstain"


@dataclass
class Adaptation:
    id: str
    kind: AdaptationKind
    target_kind: AdaptationTarget
    target_id: str
    governance: GovernanceClass
    before: dict[str, float] = field(default_factory=dict)
    after: dict[str, float] = field(default_factory=dict)
    reflective_experience_ids: list[str] = field(default_factory=list)
    evidence_experience_ids: list[str] = field(default_factory=list)
    sleep_batch_id: str = ""
    summary: str = ""
    attribute_key: str = ""
    created: float = 0.0
    applied: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "target_kind": self.target_kind.value,
            "target_id": self.target_id,
            "governance": self.governance.value,
            "before": dict(self.before),
            "after": dict(self.after),
            "reflective_experience_ids": list(self.reflective_experience_ids),
            "evidence_experience_ids": list(self.evidence_experience_ids),
            "sleep_batch_id": self.sleep_batch_id,
            "summary": self.summary,
            "attribute_key": self.attribute_key,
            "applied": self.applied,
            "created": self.created,
        }
