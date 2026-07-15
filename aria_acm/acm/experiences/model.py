"""Immutable Experience records and temporal links."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from acm.experiences.kinds import CognitiveKind, ExternalKind
from acm.experiences.salience import SalienceVector


class ExperienceLifecycle(StrEnum):
    ACTIVE = "active"
    DORMANT = "dormant"
    RETIRED = "retired"


class TemporalRelation(StrEnum):
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    OVERLAPS = "overlaps"
    CONCURRENT = "concurrent"
    CAUSES = "causes"
    CAUSED_BY = "caused_by"
    REVISES = "revises"
    REFLECTS_ON = "reflects_on"
    NEAR = "near"
    PART_OF_EPISODE = "part_of_episode"


@dataclass(frozen=True)
class Experience:
    """Immutable cognitive event — content history is never rewritten."""

    id: str
    summary: str
    sequence: int
    t_start: float
    t_encoded: float
    external_kind: ExternalKind
    cognitive_kind: CognitiveKind
    salience_birth: SalienceVector
    t_end: float | None = None
    context_tags: tuple[str, ...] = ()
    goal_ids: tuple[str, ...] = ()
    envelope_ids: tuple[str, ...] = ()
    concept_ids: tuple[str, ...] = ()
    parent_id: str | None = None
    revises_id: str | None = None
    reflects_on_id: str | None = None
    identity_influenced: bool = False
    attention_class: str = "default"
    metadata: tuple[tuple[str, str], ...] = ()

    @property
    def timestamp(self) -> float:
        return self.t_start

    @property
    def importance(self) -> float:
        return self.salience_birth.importance

    def meta_dict(self) -> dict[str, str]:
        return dict(self.metadata)

    def to_public(
        self,
        *,
        lifecycle: str = "active",
        salience_current: dict | None = None,
    ) -> dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "sequence": self.sequence,
            "t_start": self.t_start,
            "t_end": self.t_end,
            "t_encoded": self.t_encoded,
            "duration": None if self.t_end is None else max(0.0, self.t_end - self.t_start),
            "external_kind": self.external_kind.value,
            "cognitive_kind": self.cognitive_kind.value,
            "salience_birth": self.salience_birth.to_dict(),
            "salience_current": salience_current,
            "context_tags": list(self.context_tags),
            "goal_ids": list(self.goal_ids),
            "envelope_ids": list(self.envelope_ids),
            "concept_ids": list(self.concept_ids),
            "parent_id": self.parent_id,
            "revises_id": self.revises_id,
            "reflects_on_id": self.reflects_on_id,
            "identity_influenced": self.identity_influenced,
            "lifecycle": lifecycle,
            "attention_class": self.attention_class,
            "metadata": self.meta_dict(),
        }


@dataclass(frozen=True)
class TemporalLink:
    id: str
    source_id: str
    target_id: str
    relation: TemporalRelation
    weight: float = 1.0
    metadata: tuple[tuple[str, str], ...] = ()

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation.value,
            "weight": self.weight,
            "metadata": dict(self.metadata),
        }
