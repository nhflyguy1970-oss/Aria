"""Trusted Memory Ingestion — source eligibility before semantic extraction."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IngestionActor(StrEnum):
    """Who supplied the content presented for autobiographical encoding."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"
    REFLECTION = "reflection"
    DIAGNOSTIC = "diagnostic"
    MEMORY = "memory"
    PLANNER = "planner"
    SCHEDULER = "scheduler"
    CONVERSATION = "conversation"
    INFRASTRUCTURE = "infrastructure"
    UNKNOWN = "unknown"


class HostOperation(StrEnum):
    """How the content reached ACM."""

    CONVERSATION = "conversation"
    ENCODING = "encoding"
    RETRIEVAL = "retrieval"
    REFLECTION = "reflection"
    TOOL_EXECUTION = "tool_execution"
    MEMORY_SEARCH = "memory_search"
    DIAGNOSTIC = "diagnostic"
    SYSTEM_EVENT = "system_event"
    UNKNOWN = "unknown"


class MessageRole(StrEnum):
    """Role of the submitted message, independent of its wording."""

    USER_STATEMENT = "user_statement"
    USER_TEACHING = "user_teaching"
    USER_CORRECTION = "user_correction"
    ASSISTANT_REPLY = "assistant_reply"
    TOOL_RESULT = "tool_result"
    REFLECTION_OUTPUT = "reflection_output"
    DIAGNOSTIC_OUTPUT = "diagnostic_output"
    SYSTEM_MESSAGE = "system_message"
    PROMPT_TEXT = "prompt_text"
    METADATA = "metadata"
    CONVERSATION_TEXT = "conversation_text"
    INFRASTRUCTURE_LOG = "infrastructure_log"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IngestionProvenance:
    """Explicit, non-cognitive source declaration for one encode request."""

    actor: IngestionActor
    host_operation: HostOperation
    message_role: MessageRole

    def __post_init__(self) -> None:
        object.__setattr__(self, "actor", IngestionActor(self.actor))
        object.__setattr__(self, "host_operation", HostOperation(self.host_operation))
        object.__setattr__(self, "message_role", MessageRole(self.message_role))

    def to_public(self) -> dict[str, str]:
        return {
            "actor": self.actor.value,
            "host_operation": self.host_operation.value,
            "message_role": self.message_role.value,
        }


@dataclass(frozen=True)
class IngestionDecision:
    """Eligibility result evaluated before any semantic-memory mutation."""

    eligible: bool
    reason: str
    provenance: IngestionProvenance | None = None

    def to_public(self) -> dict[str, object]:
        return {
            "eligible": self.eligible,
            "reason": self.reason,
            "provenance": None if self.provenance is None else self.provenance.to_public(),
            "schema": "trusted_memory_ingestion.v1",
        }


_TRUSTED_USER_ROLES = frozenset(
    {
        MessageRole.USER_STATEMENT,
        MessageRole.USER_TEACHING,
        MessageRole.USER_CORRECTION,
    }
)
_TRUSTED_USER_OPERATIONS = frozenset(
    {
        HostOperation.CONVERSATION,
        HostOperation.ENCODING,
    }
)


def evaluate_ingestion(provenance: IngestionProvenance | None) -> IngestionDecision:
    """Apply D046's closed autobiographical-ingestion policy."""
    if provenance is None:
        return IngestionDecision(False, "missing_provenance")
    if provenance.actor == IngestionActor.UNKNOWN:
        return IngestionDecision(False, "unknown_actor", provenance)
    if provenance.host_operation == HostOperation.UNKNOWN:
        return IngestionDecision(False, "unknown_host_operation", provenance)
    if provenance.message_role == MessageRole.UNKNOWN:
        return IngestionDecision(False, "unknown_message_role", provenance)
    if provenance.actor != IngestionActor.USER:
        return IngestionDecision(False, "actor_not_autobiographical", provenance)
    if provenance.host_operation not in _TRUSTED_USER_OPERATIONS:
        return IngestionDecision(False, "host_operation_not_eligible", provenance)
    if provenance.message_role not in _TRUSTED_USER_ROLES:
        return IngestionDecision(False, "message_role_not_eligible", provenance)
    return IngestionDecision(
        True,
        f"trusted_{provenance.message_role.value}",
        provenance,
    )


TRUSTED_USER_STATEMENT = IngestionProvenance(
    actor=IngestionActor.USER,
    host_operation=HostOperation.CONVERSATION,
    message_role=MessageRole.USER_STATEMENT,
)
TRUSTED_USER_TEACHING = IngestionProvenance(
    actor=IngestionActor.USER,
    host_operation=HostOperation.ENCODING,
    message_role=MessageRole.USER_TEACHING,
)
TRUSTED_USER_CORRECTION = IngestionProvenance(
    actor=IngestionActor.USER,
    host_operation=HostOperation.ENCODING,
    message_role=MessageRole.USER_CORRECTION,
)


__all__ = [
    "HostOperation",
    "IngestionActor",
    "IngestionDecision",
    "IngestionProvenance",
    "MessageRole",
    "TRUSTED_USER_CORRECTION",
    "TRUSTED_USER_STATEMENT",
    "TRUSTED_USER_TEACHING",
    "evaluate_ingestion",
]
