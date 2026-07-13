"""Aria Core Learning Manager — authoritative Learning organ (Phase 5).

Behavior remains propose → immediate commit → apply (passthrough).
Ownership moved to Aria Core; jarvis.learning_governor is a compat shim.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")

_HISTORY: list[dict[str, Any]] = []
_HISTORY_LIMIT = 500
_AUDIT: list[dict[str, Any]] = []
_AUDIT_LIMIT = 200

PUBLISHER = "aria_core.learning"


def enabled() -> bool:
    raw = os.getenv("ARIA_LEARNING_GOVERNOR", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


@dataclass(frozen=True)
class Proposal:
    """A candidate learning write. Phase 5 still commits immediately."""

    kind: str
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    proposed_at: float = field(default_factory=time.time)
    origin: str = ""
    capability: str = "learn"
    application: str = ""
    reason: str = ""
    confidence: float | None = None
    memory_targets: tuple[str, ...] = ()
    knowledge_targets: tuple[str, ...] = ()
    expected_impact: str = ""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))


def propose(
    *,
    kind: str,
    payload: dict[str, Any] | None = None,
    source: str = "",
    origin: str = "",
    capability: str = "learn",
    application: str = "",
    reason: str = "",
    confidence: float | None = None,
    memory_targets: list[str] | tuple[str, ...] | None = None,
    knowledge_targets: list[str] | tuple[str, ...] | None = None,
    expected_impact: str = "",
) -> Proposal:
    proposal = Proposal(
        kind=kind,
        payload=dict(payload or {}),
        source=source,
        origin=origin or source or "unknown",
        capability=capability or "learn",
        application=application,
        reason=reason,
        confidence=confidence,
        memory_targets=tuple(memory_targets or ()),
        knowledge_targets=tuple(knowledge_targets or ()),
        expected_impact=expected_impact,
    )
    events = ["LearningProposed"]
    _emit("LearningProposed", proposal, extra={"payload_keys": sorted(proposal.payload.keys())})
    _history_upsert(
        proposal,
        decision="pending",
        duration_ms=0.0,
        events_published=events,
    )
    return proposal


def commit(proposal: Proposal, apply: Callable[[], T]) -> T:
    """Commit by invoking apply() immediately (passthrough)."""
    if not enabled():
        return apply()
    t0 = time.perf_counter()
    try:
        result = apply()
    except Exception as exc:
        duration_ms = round((time.perf_counter() - t0) * 1000, 3)
        events = ["LearningRejected"]
        _emit("LearningRejected", proposal, extra={"error": type(exc).__name__})
        _history_upsert(
            proposal,
            decision="rejected",
            duration_ms=duration_ms,
            events_published=events,
            error=type(exc).__name__,
        )
        raise
    duration_ms = round((time.perf_counter() - t0) * 1000, 3)
    _record_audit(proposal, ok=True)
    events = ["LearningAccepted", "LearningCommitted"]
    _emit("LearningAccepted", proposal, extra={"ok": True})
    _emit("LearningCommitted", proposal, extra={"ok": True, "duration_ms": duration_ms})
    _history_upsert(
        proposal,
        decision="accepted",
        duration_ms=duration_ms,
        events_published=events,
    )
    return result


def propose_learning(**kwargs: Any) -> Proposal:
    return propose(**kwargs)


def commit_learning(proposal: Proposal, apply: Callable[[], T]) -> T:
    return commit(proposal, apply)


def approve_learning(proposal: Proposal, apply: Callable[[], T]) -> T:
    """Phase 5: identical to commit (immediate approve)."""
    return commit(proposal, apply)


def reject_learning(proposal: Proposal, *, reason: str = "") -> dict[str, Any]:
    """Record rejection without applying a writer (explicit reject API)."""
    events = ["LearningRejected"]
    _emit(
        "LearningRejected",
        proposal,
        extra={"error": "rejected", "reason": reason or proposal.reason},
    )
    rec = _history_upsert(
        proposal,
        decision="rejected",
        duration_ms=0.0,
        events_published=events,
        error=reason or "rejected",
    )
    return {"ok": True, "decision": "rejected", "record": rec}


def replay_learning(proposal_id: str) -> dict[str, Any]:
    """Replay = re-surface a history record (no organ rewrite in Phase 5)."""
    for rec in reversed(_HISTORY):
        if rec.get("proposal_id") == proposal_id or rec.get("id") == proposal_id:
            _emit_name(
                "LearningReplayed",
                proposal_id=proposal_id,
                kind=rec.get("kind"),
                decision=rec.get("decision"),
            )
            out = dict(rec)
            out["events_published"] = list(rec.get("events_published") or []) + ["LearningReplayed"]
            return {"ok": True, "record": out, "replayed": True}
    return {"ok": False, "error": "not found", "proposal_id": proposal_id}


def rollback_learning(proposal_id: str, *, reason: str = "") -> dict[str, Any]:
    """Mark rolled back in history only — does not mutate Memory/Knowledge organs."""
    for rec in reversed(_HISTORY):
        if rec.get("proposal_id") == proposal_id or rec.get("id") == proposal_id:
            _emit_name(
                "LearningRolledBack",
                proposal_id=proposal_id,
                kind=rec.get("kind"),
                reason=reason,
            )
            rec["decision"] = "rolled_back"
            rec["rollback_reason"] = reason
            events = list(rec.get("events_published") or [])
            events.append("LearningRolledBack")
            rec["events_published"] = events
            return {"ok": True, "record": dict(rec)}
    return {"ok": False, "error": "not found", "proposal_id": proposal_id}


def learning_history(*, limit: int = 100, decision: str = "") -> list[dict[str, Any]]:
    items = list(_HISTORY)
    if decision:
        items = [r for r in items if r.get("decision") == decision]
    return items[-limit:]


def learning_statistics() -> dict[str, Any]:
    items = list(_HISTORY)
    by_decision: dict[str, int] = {}
    by_source: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    latencies = [float(r.get("duration_ms") or 0) for r in items if r.get("decision") == "accepted"]
    for r in items:
        d = str(r.get("decision") or "unknown")
        by_decision[d] = by_decision.get(d, 0) + 1
        src = str(r.get("origin") or r.get("source") or "unknown")
        by_source[src] = by_source.get(src, 0) + 1
        kind = str(r.get("kind") or "unknown")
        by_kind[kind] = by_kind.get(kind, 0) + 1
    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else 0.0
    return {
        "total": len(items),
        "by_decision": by_decision,
        "by_source": by_source,
        "by_kind": by_kind,
        "accepted": by_decision.get("accepted", 0),
        "rejected": by_decision.get("rejected", 0),
        "pending": by_decision.get("pending", 0),
        "rolled_back": by_decision.get("rolled_back", 0),
        "latency_p50_ms": round(p50, 3),
        "latency_max_ms": round(max(latencies), 3) if latencies else 0.0,
        "owner": "aria_core.learning",
        "enabled": enabled(),
    }


def recent_audit(*, limit: int = 50) -> list[dict[str, Any]]:
    return list(_AUDIT[-limit:])


def clear_audit() -> None:
    _AUDIT.clear()


def clear_history() -> None:
    _HISTORY.clear()


def reset_for_tests() -> None:
    clear_audit()
    clear_history()


def _emit(name: str, proposal: Proposal, *, extra: dict[str, Any] | None = None) -> None:
    payload = {
        "kind": proposal.kind,
        "proposal_source": proposal.source,
        "proposal_id": proposal.proposal_id,
        "origin": proposal.origin,
        "capability": proposal.capability,
        "application": proposal.application,
        "confidence": proposal.confidence,
    }
    if extra:
        payload.update(extra)
    _emit_name(name, **payload)


def _emit_name(name: str, **payload: Any) -> None:
    try:
        from aria_core.event_bus import safe_publish

        safe_publish(name, source=PUBLISHER, **payload)
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


def _history_upsert(
    proposal: Proposal,
    *,
    decision: str,
    duration_ms: float,
    events_published: list[str],
    error: str = "",
) -> dict[str, Any]:
    rec = {
        "id": proposal.proposal_id,
        "proposal_id": proposal.proposal_id,
        "origin": proposal.origin,
        "capability": proposal.capability,
        "application": proposal.application,
        "timestamp": proposal.proposed_at,
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(proposal.proposed_at)),
        "reason": proposal.reason,
        "confidence": proposal.confidence,
        "memory_targets": list(proposal.memory_targets),
        "knowledge_targets": list(proposal.knowledge_targets),
        "expected_impact": proposal.expected_impact,
        "decision": decision,
        "duration_ms": duration_ms,
        "events_published": list(events_published),
        "kind": proposal.kind,
        "source": proposal.source,
        "payload_keys": sorted(proposal.payload.keys()),
        "error": error,
        "decided_at": time.time(),
    }
    # Replace pending with final decision when same proposal_id exists
    for i, existing in enumerate(_HISTORY):
        if existing.get("proposal_id") == proposal.proposal_id:
            _HISTORY[i] = rec
            break
    else:
        _HISTORY.append(rec)
    if len(_HISTORY) > _HISTORY_LIMIT:
        del _HISTORY[: len(_HISTORY) - _HISTORY_LIMIT]
    return dict(rec)


def mission_control_panel(*, limit: int = 100) -> dict[str, Any]:
    """Operational Learning view payload (no chain-of-thought)."""
    hist = learning_history(limit=limit)
    stats = learning_statistics()
    nlu = {}
    try:
        from jarvis.nlu.learning import learning_summary

        nlu = learning_summary()
    except Exception:
        nlu = {}
    return {
        "ok": True,
        "title": "Aria Core Learning",
        "owner": "aria_core.learning",
        "implementation": "aria_core.learning_manager",
        "health": {"ok": True, "enabled": enabled()},
        "statistics": stats,
        "proposals": hist,
        "accepted": [r for r in hist if r.get("decision") == "accepted"],
        "rejected": [r for r in hist if r.get("decision") == "rejected"],
        "pending": [r for r in hist if r.get("decision") == "pending"],
        "sources": stats.get("by_source") or {},
        "applications": sorted(
            {str(r.get("application") or "") for r in hist if r.get("application")}
        ),
        "capabilities": sorted({str(r.get("capability") or "learn") for r in hist}),
        "latency": {
            "p50_ms": stats.get("latency_p50_ms"),
            "max_ms": stats.get("latency_max_ms"),
        },
        "replay": learning_history(limit=min(20, limit)),
        "nlu_summary": nlu,
        "note": "Core-owned Learning Manager; organs underneath unchanged. Visibility only.",
    }
