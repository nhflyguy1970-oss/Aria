"""Living Concept records — meaning that evolves (unlike immutable Experiences)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from acm.types import Attribute, ConceptRole


class ConceptStage(StrEnum):
    NUCLEUS = "nucleus"
    GROWING = "growing"
    STABLE = "stable"
    MATURE = "mature"
    DORMANT = "dormant"
    RETIRED = "retired"


class HierarchyKind(StrEnum):
    IS_A = "is_a"
    SPECIALIZES = "specializes"  # inverse annotation convenience
    ALIAS_OF = "alias_of"
    MERGE_INTO = "merge_into"


@dataclass
class Prototype:
    """Central tendency of features — family resemblance, not a single exemplar."""

    features: dict[str, str] = field(default_factory=dict)
    feature_weights: dict[str, float] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "features": dict(self.features),
            "feature_weights": dict(self.feature_weights),
        }


@dataclass
class Concept:
    id: str
    labels: list[str]
    role: ConceptRole = ConceptRole.ENTITY
    attributes: list[Attribute] = field(default_factory=list)
    envelope_ids: list[str] = field(default_factory=list)
    strength: float = 0.35
    importance: float = 0.5
    confidence: float = 0.45
    access_count: int = 0
    first_seen: float = 0.0
    last_activated: float = 0.0
    provisional: bool = True
    active: bool = True
    identity: bool = False
    stage: ConceptStage = ConceptStage.NUCLEUS
    evidence_ids: list[str] = field(default_factory=list)
    exemplar_ids: list[str] = field(default_factory=list)  # Experience ids
    instance_ids: list[str] = field(default_factory=list)  # child instance concept ids
    parent_ids: list[str] = field(default_factory=list)
    child_ids: list[str] = field(default_factory=list)
    prototype: Prototype = field(default_factory=Prototype)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "labels": list(self.labels),
            "role": self.role.value,
            "stage": self.stage.value,
            "strength": self.strength,
            "importance": self.importance,
            "confidence": self.confidence,
            "provisional": self.provisional,
            "identity": self.identity,
            "evidence_count": len(self.evidence_ids),
            "exemplar_ids": list(self.exemplar_ids[-12:]),
            "parent_ids": list(self.parent_ids),
            "child_ids": list(self.child_ids),
            "prototype": self.prototype.to_public(),
            "attributes": [
                {
                    "key": a.key,
                    "value": a.value,
                    "confidence": a.confidence,
                    "active": a.active,
                    "version": a.version,
                }
                for a in self.attributes
                if a.active
            ],
        }


@dataclass(frozen=True)
class HierarchyEdge:
    id: str
    child_id: str
    parent_id: str
    kind: HierarchyKind = HierarchyKind.IS_A
    weight: float = 0.5


@dataclass
class ConceptProposal:
    id: str
    kind: str  # merge | split
    concept_ids: tuple[str, ...]
    reason: str
    status: str = "pending"  # pending | accepted | rejected
