"""Structured cognitive facts produced by Semantic Extraction.

Language models understand language. ACM understands cognition.
Facts are authoritative; original wording is supporting evidence only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class PerspectiveSubject(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    THIRD_PARTY = "third_party"
    SHARED = "shared"
    UNKNOWN = "unknown"


class FactKind(StrEnum):
    IDENTITY = "identity"
    PREFERENCE = "preference"
    GOAL = "goal"
    PROJECT = "project"
    RELATIONSHIP = "relationship"
    LOCATION = "location"
    POSSESSION = "possession"
    SKILL = "skill"
    EXPERIENCE = "experience"
    CORRECTION = "correction"
    NEGATION = "negation"
    TEACHABLE = "teachable"


class UpdateOp(StrEnum):
    SET = "set"
    REVISE = "revise"
    NEGATE = "negate"
    STRENGTHEN = "strengthen"


@dataclass(frozen=True)
class CognitiveFact:
    """One structured cognitive fact — never raw conversational wording."""

    kind: FactKind
    subject: PerspectiveSubject
    property: str
    value: str
    relation_type: str | None = None
    confidence: float = 0.85
    update_op: UpdateOp = UpdateOp.SET
    labels: tuple[str, ...] = ()

    def canonical_summary(self) -> str:
        """Host-agnostic fact phrase for Experience.summary / reconstruction."""
        subj = {
            PerspectiveSubject.USER: "User",
            PerspectiveSubject.ASSISTANT: "Assistant",
            PerspectiveSubject.THIRD_PARTY: self.relation_type or "Entity",
            PerspectiveSubject.SHARED: "Shared",
            PerspectiveSubject.UNKNOWN: "Entity",
        }[self.subject]
        if self.kind == FactKind.RELATIONSHIP and self.relation_type:
            return f"{subj}'s {self.relation_type} name is {self.value}"
        if self.kind == FactKind.NEGATION:
            return f"{subj} {self.property} is not {self.value}"
        if self.property == "preferred_name":
            return f"{subj} preferred name is {self.value}"
        if self.property == "name":
            return f"{subj} name is {self.value}"
        if self.property == "role":
            return f"{subj} role is {self.value}"
        if self.property == "location":
            return f"{subj} location is {self.value}"
        if self.kind == FactKind.PREFERENCE:
            if self.property.startswith("prefer_"):
                domain = self.property.replace("prefer_", "").replace("_", " ")
                return f"preferred {domain} is {self.value}"
            label = self.property.replace("favorite_", "favorite ").replace("_", " ")
            return f"{label} is {self.value}"
        if self.kind == FactKind.GOAL:
            return f"Goal: {self.value}"
        if self.kind == FactKind.PROJECT:
            return f"Project: {self.value}"
        if self.kind == FactKind.SKILL:
            return f"{subj} can {self.value}"
        if self.kind == FactKind.EXPERIENCE:
            action = (self.property or "experienced").replace("_", " ")
            obj = (self.value or "").strip()
            phrase = f"{subj} {action} {obj}".strip()
            when = (self.relation_type or "").replace("_", " ").strip()
            if when:
                return f"{phrase} ({when})"
            return phrase
        return f"{subj} {self.property} is {self.value}"

    def to_public(self) -> dict:
        return {
            "kind": self.kind.value,
            "subject": self.subject.value,
            "property": self.property,
            "value": self.value,
            "relation_type": self.relation_type,
            "confidence": self.confidence,
            "update_op": self.update_op.value,
            "summary": self.canonical_summary(),
        }


@dataclass(frozen=True)
class PerspectiveResolution:
    """Resolved conversational perspective for an utterance."""

    first_person: PerspectiveSubject
    second_person: PerspectiveSubject
    speaker_hint: str | None = None
    reason: str = ""


@dataclass
class ExtractionResult:
    """Output of Semantic Extraction — facts + evidence separation."""

    facts: list[CognitiveFact] = field(default_factory=list)
    evidence: str = ""
    perspective: PerspectiveResolution | None = None
    instructional_stripped: bool = False
    raw_fallback: bool = False

    @property
    def primary_summary(self) -> str:
        if self.facts:
            return "; ".join(f.canonical_summary() for f in self.facts)
        # Never prefer instructional noise — strip if present
        return (self.evidence or "").strip()

    def identity_facts(self) -> list[CognitiveFact]:
        return [
            f
            for f in self.facts
            if f.kind
            in (
                FactKind.IDENTITY,
                FactKind.SKILL,
                FactKind.LOCATION,
                FactKind.CORRECTION,
                FactKind.NEGATION,
            )
            or f.property in ("name", "preferred_name", "role", "capability", "location")
        ]

    def to_public(self) -> dict:
        return {
            "facts": [f.to_public() for f in self.facts],
            "evidence": self.evidence,
            "primary_summary": self.primary_summary,
            "instructional_stripped": self.instructional_stripped,
            "raw_fallback": self.raw_fallback,
            "perspective": None
            if self.perspective is None
            else {
                "first_person": self.perspective.first_person.value,
                "second_person": self.perspective.second_person.value,
                "speaker_hint": self.perspective.speaker_hint,
                "reason": self.perspective.reason,
            },
        }
