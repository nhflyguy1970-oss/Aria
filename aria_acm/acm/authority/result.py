"""Structured Cognitive Memory Result — never language-model authority."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class MemoryStatus(StrEnum):
    """Authority status of a cognitive memory reconstruction."""

    KNOWN = "known"
    UNKNOWN = "unknown"
    LOW_CONFIDENCE = "low_confidence"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING = "conflicting"
    NOT_MEMORY = "not_memory"


@dataclass
class CognitiveMemoryResult:
    """ACM's sole cognitive product for memory requests.

    This object is **not** natural language generation authority.
    Hosts may only communicate its fields (via ``speak_cognitive_result``).
    """

    status: MemoryStatus
    is_memory_request: bool
    intent: str
    memory: str | None
    confidence: float
    uncertainty: str | None = None
    explanation_class: str = "unknown"
    provenance: list[dict[str, Any]] = field(default_factory=list)
    supporting_experiences: list[dict[str, Any]] = field(default_factory=list)
    supporting_concepts: list[dict[str, Any]] = field(default_factory=list)
    supporting_associations: list[dict[str, Any]] = field(default_factory=list)
    reflective_evidence: list[dict[str, Any]] = field(default_factory=list)
    learning_evidence: list[dict[str, Any]] = field(default_factory=list)
    reasoning_path: list[str] = field(default_factory=list)
    ambiguous: bool = False
    language_may_speak: bool = False
    allow_encode_from_speech: bool = False
    classification: dict[str, Any] = field(default_factory=dict)
    organ_payload: dict[str, Any] = field(default_factory=dict)
    schema: str = "cognitive_memory_result.v1"

    def to_public(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @property
    def may_fabricate(self) -> bool:
        """Always false — LM must never invent memory content."""
        return False
