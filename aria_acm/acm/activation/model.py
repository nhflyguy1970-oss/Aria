"""Shared cognitive activation field — canonical for all active organs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ActivationTarget(StrEnum):
    CONCEPT = "concept"
    ASSOCIATION = "association"
    EXPERIENCE = "experience"
    GOAL = "goal"
    IDENTITY = "identity"
    WORKING = "working"


class CueClass(StrEnum):
    QUESTION = "question"
    CONCEPT = "concept"
    GOAL = "goal"
    PLACE = "place"
    PERSON = "person"
    TIME = "time"
    IDENTITY = "identity"
    WORKING = "working"
    OBSERVATION = "observation"
    LEXICAL = "lexical"
    CONTEXT = "context"


@dataclass
class ActivationSeed:
    target_kind: ActivationTarget
    target_id: str
    energy: float
    cue_classes: tuple[str, ...] = ()
    label: str = ""


@dataclass
class PropagationStep:
    """Observable hop — not chain-of-thought."""

    from_id: str
    to_id: str
    association_id: str
    relation: str
    energy_in: float
    energy_out: float
    direction: str  # forward | backward


@dataclass
class ActivatedNode:
    target_kind: ActivationTarget
    target_id: str
    energy: float
    confidence: float = 0.0
    label: str = ""
    path_depth: int = 0
    sources: tuple[str, ...] = ()


@dataclass
class ActivationField:
    """Result of one activation episode."""

    cue: str
    cue_classes: list[str] = field(default_factory=list)
    seeds: list[ActivationSeed] = field(default_factory=list)
    concepts: dict[str, ActivatedNode] = field(default_factory=dict)
    associations: dict[str, float] = field(default_factory=dict)
    experiences: dict[str, ActivatedNode] = field(default_factory=dict)
    steps: list[PropagationStep] = field(default_factory=list)
    decayed: int = 0
    inhibited: int = 0
    goal_influenced: bool = False
    identity_influenced: bool = False
    context_influenced: bool = False
    working_influenced: bool = False
    max_energy: float = 0.0

    def ranked_concepts(self, *, limit: int = 8) -> list[ActivatedNode]:
        nodes = sorted(self.concepts.values(), key=lambda n: n.energy, reverse=True)
        return nodes[:limit]

    def to_public(self) -> dict[str, Any]:
        ranked = self.ranked_concepts()
        return {
            "cue": self.cue,
            "cue_classes": list(self.cue_classes),
            "seed_count": len(self.seeds),
            "concept_activations": [
                {
                    "id": n.target_id,
                    "label": n.label,
                    "energy": round(n.energy, 4),
                    "confidence": round(n.confidence, 4),
                    "depth": n.path_depth,
                }
                for n in ranked
            ],
            "association_activations": len(self.associations),
            "experience_participants": len(self.experiences),
            "propagation_steps": len(self.steps),
            "decayed": self.decayed,
            "inhibited": self.inhibited,
            "goal_influenced": self.goal_influenced,
            "identity_influenced": self.identity_influenced,
            "context_influenced": self.context_influenced,
            "working_influenced": self.working_influenced,
            "max_energy": round(self.max_energy, 4),
            "path_sample": [
                {
                    "from": s.from_id,
                    "to": s.to_id,
                    "relation": s.relation,
                    "energy_out": round(s.energy_out, 4),
                }
                for s in self.steps[:12]
            ],
        }
