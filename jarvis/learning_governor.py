"""Learning Governor — Continuous Proposal, Discontinuous Commit.

Phase 1: passthrough only. Every proposal is committed immediately via the
same writer that existed before the Governor. Behavior must be bit-identical.

Disable with ARIA_LEARNING_GOVERNOR=0 (or false/no/off).
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")

_AUDIT: list[dict[str, Any]] = []
_AUDIT_LIMIT = 200


def enabled() -> bool:
    raw = os.getenv("ARIA_LEARNING_GOVERNOR", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


@dataclass(frozen=True)
class Proposal:
    """A candidate learning write. Phase 1 commits immediately."""

    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    proposed_at: float = field(default_factory=time.time)


def propose(
    *,
    kind: str,
    payload: dict[str, Any] | None = None,
    source: str = "",
) -> Proposal:
    proposal = Proposal(kind=kind, payload=dict(payload or {}), source=source)
    _emit_learning(
        "LearningProposed",
        kind=proposal.kind,
        proposal_source=proposal.source,
        payload_keys=sorted(proposal.payload.keys()),
    )
    return proposal


def commit(proposal: Proposal, apply: Callable[[], T]) -> T:
    """Commit a proposal by invoking apply() immediately (passthrough).

    Phase 1 does not filter, delay, or mutate payloads. apply() must perform
    the exact legacy write.
    """
    if not enabled():
        return apply()
    try:
        result = apply()
    except Exception as exc:
        _emit_learning(
            "LearningRejected",
            kind=proposal.kind,
            proposal_source=proposal.source,
            error=type(exc).__name__,
        )
        raise
    _record_audit(proposal, ok=True)
    _emit_learning(
        "LearningAccepted",
        kind=proposal.kind,
        proposal_source=proposal.source,
        ok=True,
    )
    return result


def _emit_learning(name: str, **payload: Any) -> None:
    """Best-effort Aria Core Event Bus publish — never affects learning behavior."""
    try:
        from aria_core.event_bus import safe_publish

        safe_publish(name, source="jarvis.learning_governor", **payload)
    except Exception:
        pass


def _record_audit(proposal: Proposal, *, ok: bool) -> None:
    if os.getenv("ARIA_LEARNING_GOVERNOR_AUDIT", "0").strip().lower() in (
        "0",
        "false",
        "no",
        "off",
        "",
    ):
        return
    _AUDIT.append(
        {
            "ts": time.time(),
            "kind": proposal.kind,
            "source": proposal.source,
            "ok": ok,
            "payload_keys": sorted(proposal.payload.keys()),
        }
    )
    if len(_AUDIT) > _AUDIT_LIMIT:
        del _AUDIT[: len(_AUDIT) - _AUDIT_LIMIT]


def recent_audit(*, limit: int = 50) -> list[dict[str, Any]]:
    return list(_AUDIT[-limit:])


def clear_audit() -> None:
    _AUDIT.clear()
