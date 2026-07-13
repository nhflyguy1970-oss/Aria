"""Aria Core Cognitive Orchestrator (Phase 6).

Coordinates which cognitive capabilities participate in a request.
Does not perform cognition — existing organs continue to do the work.
Phase 6 policy is passthrough: one primary capability per Cap Bus verb.
"""

from __future__ import annotations

import contextvars
import time
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

from aria_core.ownership import module_ownership

T = TypeVar("T")

PUBLISHER = "aria_core.cognition"
COGNITION_VERSION = "2.0-phase6"

# Organs the orchestrator may coordinate (not move).
COGNITIVE_ORGANS: tuple[str, ...] = (
    "memory",
    "knowledge",
    "reference",
    "planning",
    "reasoning",
    "learning",
    "runtime",
    "capabilities",
)

# Cap Bus verb → (primary organ, request event name)
VERB_POLICY: dict[str, tuple[str, str]] = {
    "remember": ("memory", "MemoryRequested"),
    "recall": ("memory", "MemoryRequested"),
    "search": ("knowledge", "KnowledgeRequested"),
    "reference": ("reference", "ReferenceRequested"),
    "plan": ("planning", "PlanningRequested"),
    "reason": ("reasoning", "ReasoningRequested"),
    "infer": ("reasoning", "ReasoningRequested"),
    "learn": ("learning", "LearningRequested"),
    "execute_tool": ("capabilities", "CapabilitySelected"),
    "schedule": ("runtime", "CapabilitySelected"),
    "observe": ("runtime", "CapabilitySelected"),
    "notify": ("runtime", "CapabilitySelected"),
    "diagnose": ("runtime", "CapabilitySelected"),
    "repair": ("runtime", "CapabilitySelected"),
    "backup": ("runtime", "CapabilitySelected"),
    "recover": ("runtime", "CapabilitySelected"),
}

_HISTORY: list[dict[str, Any]] = []
_HISTORY_LIMIT = 300
_DEPTH: contextvars.ContextVar[int] = contextvars.ContextVar("aria_cognition_depth", default=0)


def _owner() -> dict[str, Any]:
    return module_ownership("cognition")


def _emit(name: str, **payload: Any) -> None:
    try:
        from aria_core.event_bus import safe_publish

        safe_publish(name, source=PUBLISHER, **payload)
    except Exception:
        pass


def participation_for(capability: str) -> dict[str, Any]:
    """Deterministic Phase 6 participation: primary organ only (identical to today)."""
    primary, request_event = VERB_POLICY.get(capability, ("capabilities", "CapabilitySelected"))
    selected = [primary]
    skipped = [o for o in COGNITIVE_ORGANS if o not in selected]
    return {
        "capability": capability,
        "selected": selected,
        "skipped": skipped,
        "execution_order": list(selected),
        "request_event": request_event,
        "learning": primary == "learning",
        "clarification": False,
        "combine": False,
        "policy": "passthrough-phase6",
    }


def run(capability: str, fn: Callable[[], T], *, meta: dict[str, Any] | None = None) -> T:
    """Coordinate a Cap Bus verb then execute fn() unchanged."""
    depth = _DEPTH.get()
    if depth > 0:
        # Nested Cap Bus call (e.g. infer→reason) — do not re-wrap cognition envelope.
        return fn()

    token = _DEPTH.set(depth + 1)
    plan = participation_for(capability)
    cognition_id = str(uuid.uuid4())
    t0 = time.perf_counter()
    events: list[str] = ["CognitionStarted"]
    _emit(
        "CognitionStarted",
        cognition_id=cognition_id,
        capability=capability,
        selected=plan["selected"],
        **(meta or {}),
    )
    try:
        for organ in plan["selected"]:
            _emit(
                "CapabilitySelected",
                cognition_id=cognition_id,
                capability=capability,
                organ=organ,
            )
            events.append("CapabilitySelected")
            req = plan["request_event"]
            if req and req != "CapabilitySelected":
                _emit(
                    req,
                    cognition_id=cognition_id,
                    capability=capability,
                    organ=organ,
                )
                events.append(req)
        for organ in plan["skipped"]:
            _emit(
                "CapabilitySkipped",
                cognition_id=cognition_id,
                capability=capability,
                organ=organ,
                reason="passthrough-primary-only",
            )
            events.append("CapabilitySkipped")

        result = fn()
        duration_ms = round((time.perf_counter() - t0) * 1000, 3)
        _emit(
            "CognitionCompleted",
            cognition_id=cognition_id,
            capability=capability,
            ok=True,
            duration_ms=duration_ms,
        )
        events.append("CognitionCompleted")
        _record(
            cognition_id=cognition_id,
            capability=capability,
            plan=plan,
            ok=True,
            duration_ms=duration_ms,
            events_published=events,
            meta=meta or {},
        )
        return result
    except Exception as exc:
        duration_ms = round((time.perf_counter() - t0) * 1000, 3)
        _emit(
            "CognitionCompleted",
            cognition_id=cognition_id,
            capability=capability,
            ok=False,
            error=type(exc).__name__,
            duration_ms=duration_ms,
        )
        events.append("CognitionCompleted")
        _record(
            cognition_id=cognition_id,
            capability=capability,
            plan=plan,
            ok=False,
            duration_ms=duration_ms,
            events_published=events,
            meta={**(meta or {}), "error": type(exc).__name__},
        )
        raise
    finally:
        _DEPTH.reset(token)


def _record(
    *,
    cognition_id: str,
    capability: str,
    plan: dict[str, Any],
    ok: bool,
    duration_ms: float,
    events_published: list[str],
    meta: dict[str, Any],
) -> None:
    rec = {
        "id": cognition_id,
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "capability": capability,
        "selected": list(plan.get("selected") or []),
        "skipped": list(plan.get("skipped") or []),
        "execution_order": list(plan.get("execution_order") or []),
        "ok": ok,
        "duration_ms": duration_ms,
        "events_published": list(events_published),
        "decision_metadata": {
            "policy": plan.get("policy"),
            "learning": plan.get("learning"),
            "clarification": plan.get("clarification"),
            "combine": plan.get("combine"),
            "request_event": plan.get("request_event"),
            **{k: v for k, v in meta.items() if k in ("query_len", "action", "kind")},
        },
        "health": "ok" if ok else "error",
    }
    _HISTORY.append(rec)
    if len(_HISTORY) > _HISTORY_LIMIT:
        del _HISTORY[: len(_HISTORY) - _HISTORY_LIMIT]


def recent_pipelines(*, limit: int = 50) -> list[dict[str, Any]]:
    return list(_HISTORY[-limit:])


def cognition_statistics() -> dict[str, Any]:
    items = list(_HISTORY)
    by_cap: dict[str, int] = {}
    ok_n = sum(1 for r in items if r.get("ok"))
    lat = [float(r.get("duration_ms") or 0) for r in items]
    lat.sort()
    for r in items:
        c = str(r.get("capability") or "?")
        by_cap[c] = by_cap.get(c, 0) + 1
    return {
        "total": len(items),
        "ok": ok_n,
        "errors": len(items) - ok_n,
        "by_capability": by_cap,
        "latency_p50_ms": round(lat[len(lat) // 2], 3) if lat else 0.0,
        "latency_max_ms": round(max(lat), 3) if lat else 0.0,
        "owner": "aria_core.cognition",
        "version": COGNITION_VERSION,
    }


def clear_history() -> None:
    _HISTORY.clear()


def reset_for_tests() -> None:
    clear_history()


def mission_control_panel(*, limit: int = 50) -> dict[str, Any]:
    stats = cognition_statistics()
    pipes = recent_pipelines(limit=limit)
    return {
        "ok": True,
        "title": "Aria Core Cognition",
        "owner": "aria_core.cognition",
        "version": COGNITION_VERSION,
        "health": {"ok": True, "policy": "passthrough-phase6"},
        "statistics": stats,
        "pipelines": pipes,
        "latency": {
            "p50_ms": stats.get("latency_p50_ms"),
            "max_ms": stats.get("latency_max_ms"),
        },
        "organs": list(COGNITIVE_ORGANS),
        "verb_policy": {k: {"organ": v[0], "request_event": v[1]} for k, v in VERB_POLICY.items()},
        "note": (
            "Cognitive Orchestrator coordinates Cap Bus verbs; "
            "organs unchanged. Execution metadata only — no chain-of-thought."
        ),
    }
