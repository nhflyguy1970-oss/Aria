"""Core cognitive identifiers and enums — host-agnostic."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


def new_id(prefix: str = "c") -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class MemoryVerb(StrEnum):
    ENCODE = "encode"
    REMEMBER = "remember"
    RECONSOLIDATE = "reconsolidate"
    LEARN = "learn"
    SLEEP = "sleep"
    ATTEND = "attend"
    FORGET = "forget"
    PREDICT = "predict"
    SIMULATE = "simulate"
    RECOMBINE = "recombine"
    ANALOGIZE = "analogize"
    RECONCILE = "reconcile"
    ASSESS = "assess"


class AttentionClass(StrEnum):
    NOVELTY = "novelty"
    STAKES = "stakes"
    FREQUENCY = "frequency"
    GOAL = "goal"
    PREDICTION_ERROR = "prediction_error"
    USER_PIN = "user_pin"
    SENSORY = "sensory"
    DEFAULT = "default"


class ExplanationClass(StrEnum):
    PREFERENCE = "preference"
    EXPERIENCE = "experience"
    PROCEDURE = "procedure"
    GOAL = "goal"
    REPEATED = "repeated"
    STALE = "stale"
    CONTESTED = "contested"
    CONTEXT = "context"
    ADOPTED_KNOWLEDGE = "adopted_knowledge"
    UNKNOWN = "unknown"


class ConceptRole(StrEnum):
    ENTITY = "entity"
    PREFERENCE = "preference"
    SKILL = "skill"
    PLACE = "place"
    TOPIC = "topic"
    IDENTITY = "identity"
    OTHER = "other"


class EdgeType(StrEnum):
    RELATED_TO = "related_to"
    IS_A = "is_a"
    PART_OF = "part_of"
    DEPICTS = "depicts"
    OCCURS_IN = "occurs_in"
    OWNED_BY = "owned_by"
    SUPERSEDES = "supersedes"
    CONTESTS = "contests"
    CO_ACTIVATED = "co_activated"
    EVIDENCED_BY = "evidenced_by"


@dataclass
class EnvelopeRef:
    """Pointer to multimodal content (bytes live in a store; cognition holds the link)."""

    content_hash: str
    kind: str  # text | image | audio | video | pdf | code | sensor | ...
    mime: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Attribute:
    key: str
    value: str
    confidence: float = 0.7
    importance: float = 0.5
    context_tags: tuple[str, ...] = ()
    evidence_ids: list[str] = field(default_factory=list)
    active: bool = True
    version: int = 1
