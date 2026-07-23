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
    """Taxonomic link owned by the Concept organ (D016). Evidence-stamped; never invents Experiences."""

    id: str
    child_id: str
    parent_id: str
    kind: HierarchyKind = HierarchyKind.IS_A
    weight: float = 0.5
    evidence_ids: tuple[str, ...] = ()
    created: float = 0.0
    last_reinforced: float = 0.0

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "child_id": self.child_id,
            "parent_id": self.parent_id,
            "kind": self.kind.value,
            "weight": self.weight,
            "evidence_ids": list(self.evidence_ids),
            "evidence_count": len(self.evidence_ids),
            "created": self.created,
            "last_reinforced": self.last_reinforced,
        }


@dataclass
class ConceptProposal:
    id: str
    kind: str  # merge | split | hierarchy_link | specialize | generalize | inherit
    concept_ids: tuple[str, ...]
    reason: str
    status: str = "pending"  # pending | accepted | rejected
    evidence_ids: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class AbstractionLevel(StrEnum):
    """Progressive multi-level abstraction (M5 Cap4)."""

    L1_OBSERVATION = "l1_observation"
    L2_CONCEPT = "l2_concept"
    L3_GENERALIZED = "l3_generalized"
    L4_PRINCIPLE = "l4_principle"
    L5_STRUCTURE = "l5_structure"


class AbstractionStatus(StrEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    REFINED = "refined"
    SPLIT = "split"
    MERGED = "merged"
    RETIRED = "retired"


class PrincipleModality(StrEnum):
    """Probabilistic modality — never absolute truth."""

    USUALLY = "usually"
    TENDS = "tends"
    COMMONLY = "commonly"
    RARELY = "rarely"


@dataclass
class AbstractionRecord:
    """Evidence-based multi-level abstraction. Never invents Experiences."""

    id: str
    label: str
    level: AbstractionLevel
    status: AbstractionStatus = AbstractionStatus.CANDIDATE
    confidence: float = 0.35
    supporting_concept_ids: list[str] = field(default_factory=list)
    supporting_experience_ids: list[str] = field(default_factory=list)
    conflicting_experience_ids: list[str] = field(default_factory=list)
    hierarchy_edge_ids: list[str] = field(default_factory=list)
    parent_abstraction_id: str = ""
    child_abstraction_ids: list[str] = field(default_factory=list)
    merged_into: str = ""
    split_from: str = ""
    prediction_audit_ids: list[str] = field(default_factory=list)
    created: float = 0.0
    last_reinforced: float = 0.0
    retired_at: float = 0.0
    retirement_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "level": self.level.value,
            "status": self.status.value,
            "confidence": round(self.confidence, 4),
            "supporting_concept_ids": list(self.supporting_concept_ids),
            "supporting_experience_ids": list(self.supporting_experience_ids),
            "conflicting_experience_ids": list(self.conflicting_experience_ids),
            "hierarchy_edge_ids": list(self.hierarchy_edge_ids),
            "parent_abstraction_id": self.parent_abstraction_id,
            "child_abstraction_ids": list(self.child_abstraction_ids),
            "merged_into": self.merged_into,
            "split_from": self.split_from,
            "prediction_audit_ids": list(self.prediction_audit_ids),
            "created": self.created,
            "last_reinforced": self.last_reinforced,
            "retired_at": self.retired_at,
            "retirement_reason": self.retirement_reason,
            "evidence_count": len(self.supporting_experience_ids),
            "invents_experiences": False,
        }


@dataclass
class GeneralPrinciple:
    """Probabilistic general principle — never an absolute truth."""

    id: str
    statement: str
    modality: PrincipleModality
    confidence: float = 0.4
    abstraction_id: str = ""
    supporting_concept_ids: list[str] = field(default_factory=list)
    supporting_experience_ids: list[str] = field(default_factory=list)
    conflicting_experience_ids: list[str] = field(default_factory=list)
    active: bool = True
    created: float = 0.0
    last_reinforced: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "modality": self.modality.value,
            "confidence": round(self.confidence, 4),
            "abstraction_id": self.abstraction_id,
            "supporting_concept_ids": list(self.supporting_concept_ids),
            "supporting_experience_ids": list(self.supporting_experience_ids),
            "conflicting_experience_ids": list(self.conflicting_experience_ids),
            "active": self.active,
            "created": self.created,
            "last_reinforced": self.last_reinforced,
            "absolute": False,
            "invents_experiences": False,
        }
