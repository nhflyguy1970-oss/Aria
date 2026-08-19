"""Shared execution context — correlation metadata, and nothing more.

This is deliberately not a memory system. It carries the identifiers that let
one piece of autonomous work be recognised across missions, workflows, agents,
skills, tools and models. Nothing here is ever written to ACM or to long-term
memory: what becomes memory is a separate, user-approved decision, and this
layer must not quietly make it.
"""

from __future__ import annotations

import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from typing import Any

_CURRENT: ContextVar[dict[str, Any] | None] = ContextVar("aria_execution_context", default=None)

MAX_TOOLS_TRACKED = 40
MAX_SOURCES_TRACKED = 40


@dataclass(frozen=True)
class ExecutionContext:
    """Who asked for what, and which subsystems are carrying it out."""

    request_id: str
    task_id: str = ""
    workflow_id: str = ""
    mission_id: str = ""
    requester: str = ""
    agent_id: str = ""
    skill_id: str = ""
    model: str = ""
    provider: str = ""
    autonomy: str = ""
    deadline_ts: float = 0.0
    tools: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    started_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def expired(self, now: float | None = None) -> bool:
        return bool(self.deadline_ts) and (now or time.time()) > self.deadline_ts

    def remaining_s(self) -> float | None:
        if not self.deadline_ts:
            return None
        return round(max(0.0, self.deadline_ts - time.time()), 2)

    def with_(self, **updates: Any) -> ExecutionContext:
        """A derived context. Bounded lists stay bounded."""
        for key in ("tools", "sources", "evidence"):
            if key in updates and isinstance(updates[key], (list, tuple)):
                limit = MAX_TOOLS_TRACKED if key == "tools" else MAX_SOURCES_TRACKED
                updates[key] = tuple(updates[key])[:limit]
        return replace(self, **updates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "mission_id": self.mission_id,
            "requester": self.requester,
            "agent_id": self.agent_id,
            "skill_id": self.skill_id,
            "model": self.model,
            "provider": self.provider,
            "autonomy": self.autonomy,
            "tools": list(self.tools),
            "sources": list(self.sources),
            "evidence": list(self.evidence),
            "started_at": self.started_at,
            "elapsed_s": round(time.time() - self.started_at, 2),
            "deadline_ts": self.deadline_ts,
            "remaining_s": self.remaining_s(),
            "metadata": dict(self.metadata),
        }


def new_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:10]}"


def create(
    *,
    requester: str = "",
    autonomy: str = "",
    timeout_s: float = 0.0,
    **fields: Any,
) -> ExecutionContext:
    return ExecutionContext(
        request_id=new_request_id(),
        requester=requester,
        autonomy=autonomy,
        deadline_ts=(time.time() + timeout_s) if timeout_s else 0.0,
        **fields,
    )


def current() -> ExecutionContext | None:
    raw = _CURRENT.get()
    return raw["context"] if raw else None


class bind:
    """Make a context current for a block of work.

    A context manager rather than a global: nested work gets its own derived
    context and the previous one is restored, so concurrent requests cannot see
    each other's identifiers.
    """

    def __init__(self, context: ExecutionContext) -> None:
        self._context = context
        self._token = None

    def __enter__(self) -> ExecutionContext:
        self._token = _CURRENT.set({"context": self._context})
        return self._context

    def __exit__(self, *exc: Any) -> bool:
        if self._token is not None:
            _CURRENT.reset(self._token)
        return False


def correlate(payload: dict[str, Any]) -> dict[str, Any]:
    """Stamp the current context's identifiers onto an outgoing payload.

    Only identifiers, and only where the caller has not set them: this is how a
    subsystem learns which request it belongs to, not a way to override what a
    caller explicitly asked for.
    """
    context = current()
    if context is None:
        return dict(payload)
    stamped = dict(payload)
    for key in ("workflow_id", "mission_id", "request_id"):
        value = getattr(context, key, "")
        if value and not stamped.get(key):
            stamped[key] = value
    return stamped
