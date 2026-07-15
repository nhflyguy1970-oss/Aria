"""Living Association records — cognitive relationships (not graph-tech edges)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RelationKind(StrEnum):
    """Evolvable vocabulary — not a closed mega-ontology."""

    RELATED_TO = "related_to"
    PART_OF = "part_of"
    CAUSED_BY = "caused_by"
    SUPPORTS = "supports"
    CONFLICTS_WITH = "conflicts_with"
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    DEPENDS_ON = "depends_on"
    RESEMBLES = "resembles"
    BELONGS_WITH = "belongs_with"
    EXPLAINS = "explains"
    PREDICTS = "predicts"
    REINFORCES = "reinforces"
    REQUIRES = "requires"
    CO_ACTIVATED = "co_activated"
    OWNED_BY = "owned_by"
    EVIDENCED_BY = "evidenced_by"
    IS_A_TRAFFIC = "is_a_traffic"  # mirrors Concept hierarchy as directed traffic
    SUPERSEDES = "supersedes"
    DEPICTS = "depicts"
    OCCURS_IN = "occurs_in"


class AssociationStage(StrEnum):
    NASCENT = "nascent"
    ACTIVE = "active"
    STRONG = "strong"
    DORMANT = "dormant"
    RETIRED = "retired"


class CognitiveDistance(StrEnum):
    IMMEDIATE = "immediate"
    NEAR = "near"
    FAR = "far"
    WEAK = "weak"
    DORMANT = "dormant"
    UNEXPECTED = "unexpected"


@dataclass
class Association:
    """Directed cognitive relationship with independent forward/back strengths."""

    id: str
    source_id: str
    target_id: str
    relation: RelationKind = RelationKind.RELATED_TO
    strength_forward: float = 0.4
    strength_backward: float = 0.25
    confidence: float = 0.5
    stage: AssociationStage = AssociationStage.NASCENT
    evidence_ids: list[str] = field(default_factory=list)
    context_tags: tuple[str, ...] = ()
    goal_influenced: bool = False
    identity_influenced: bool = False
    temporal_weight: float = 0.0
    access_count: int = 0
    first_seen: float = 0.0
    last_activated: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def active(self) -> bool:
        return self.stage not in (AssociationStage.DORMANT, AssociationStage.RETIRED)

    @active.setter
    def active(self, value: bool) -> None:
        """Compat for sleep/prune — False → dormant; True restores active if not retired."""
        if value:
            if self.stage == AssociationStage.RETIRED:
                return
            if self.stage == AssociationStage.DORMANT:
                self.stage = AssociationStage.ACTIVE
        else:
            if self.stage != AssociationStage.RETIRED:
                self.stage = AssociationStage.DORMANT

    @property
    def weight(self) -> float:
        """Compatibility scalar — prefers forward strength."""
        return self.strength_forward

    @weight.setter
    def weight(self, value: float) -> None:
        self.strength_forward = float(value)

    @property
    def edge_type(self) -> RelationKind:
        """Compatibility alias for legacy EdgeType usage."""
        return self.relation

    def distance_band(self) -> CognitiveDistance:
        if self.stage == AssociationStage.DORMANT:
            return CognitiveDistance.DORMANT
        if self.metadata.get("unexpected"):
            return CognitiveDistance.UNEXPECTED
        s = max(self.strength_forward, self.strength_backward)
        if s >= 0.75:
            return CognitiveDistance.IMMEDIATE
        if s >= 0.55:
            return CognitiveDistance.NEAR
        if s >= 0.35:
            return CognitiveDistance.FAR
        return CognitiveDistance.WEAK

    def strength_toward(self, from_id: str, to_id: str) -> float:
        if self.source_id == from_id and self.target_id == to_id:
            return self.strength_forward
        if self.source_id == to_id and self.target_id == from_id:
            return self.strength_backward
        return 0.0

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation.value,
            "strength_forward": self.strength_forward,
            "strength_backward": self.strength_backward,
            "confidence": self.confidence,
            "stage": self.stage.value,
            "distance": self.distance_band().value,
            "evidence_count": len(self.evidence_ids),
            "context_tags": list(self.context_tags),
            "goal_influenced": self.goal_influenced,
            "identity_influenced": self.identity_influenced,
            "temporal_weight": self.temporal_weight,
            "access_count": self.access_count,
        }
