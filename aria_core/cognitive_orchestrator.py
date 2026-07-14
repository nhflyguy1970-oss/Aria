"""Aria Core Cognitive Orchestrator (Phase 6 + Daily Use compose).

Coordinates which cognitive capabilities participate in a request.
Does not perform cognition — existing organs continue to do the work.

Cap Bus verbs remain primary-organ passthrough for backward compatibility.
Compound chat requests use plan_request + orchestrate_compose to run
multiple complementary organs and merge via the Response Composer.
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
COGNITION_VERSION = "2.0-compose"

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
    """Cap Bus verb participation: primary organ (unchanged contract)."""
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
        "policy": "passthrough-primary",
    }


def plan_request(prompt: str) -> dict[str, Any]:
    """Plan organs for a user prompt. Multi-cap when compound + >=2 families."""
    from aria_core.request_plan import build_request_plan

    return build_request_plan(prompt)


def run(capability: str, fn: Callable[[], T], *, meta: dict[str, Any] | None = None) -> T:
    """Coordinate a Cap Bus verb then execute fn() unchanged."""
    depth = _DEPTH.get()
    if depth > 0:
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


def _execute_organ(organ: str, plan: dict[str, Any]) -> dict[str, Any]:
    """Run one organ using existing implementations. Failures are soft."""
    prompt = str(plan.get("prompt") or "")
    t0 = time.perf_counter()
    try:
        if organ == "reference":
            from jarvis.reference_engine import search_reference

            query = str(plan.get("reference_query") or prompt).strip()
            result = search_reference(query)
            ok = bool(result.get("ok", True)) and bool(str(result.get("message") or "").strip())
            data = dict(result.get("data") or {})
            if result.get("diagnostics"):
                data["diagnostics"] = result["diagnostics"]
            if result.get("selected") is not None:
                data["selected"] = result.get("selected")
            if result.get("rejected") is not None:
                data["rejected"] = result.get("rejected")
            return {
                "capability": "reference",
                "ok": ok,
                "message": result.get("message") or "",
                "data": data,
                "error": None if ok else (result.get("error") or "empty reference result"),
                "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
            }
        if organ == "runtime":
            if plan.get("architectural"):
                component = plan.get("component") or "This architectural component"
                msg = (
                    f"{str(component).title()} is an Aria Core architectural component, "
                    "not a Docker/systemd service. It operates in-process whenever Aria "
                    "is handling requests; there is no separate runtime container to check. "
                    "Mission Control Cognition / Events show live coordination."
                )
                return {
                    "capability": "runtime",
                    "ok": True,
                    "message": msg,
                    "data": {"architectural": True, "component": component},
                    "error": None,
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
                }
            from jarvis.runtime_introspection import runtime_action_result

            action = str(plan.get("runtime_action") or "runtime_status")
            result = runtime_action_result(action)
            ok = bool(result.get("ok", True))
            return {
                "capability": "runtime",
                "ok": ok,
                "message": result.get("message") or "",
                "data": result.get("data"),
                "error": None if ok else (result.get("error") or "runtime unavailable"),
                "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
            }
        if organ == "memory":
            try:
                from aria_core.memory import search_memory

                hits = list(search_memory(prompt, limit=5) or [])
                if hits:
                    lines = ["From memory:"]
                    for hit in hits[:5]:
                        if isinstance(hit, dict):
                            lines.append(f"• {hit.get('text') or hit.get('content') or hit}")
                        else:
                            lines.append(f"• {hit}")
                    msg = "\n".join(lines)
                else:
                    msg = "No relevant memories were found for this request."
                return {
                    "capability": "memory",
                    "ok": True,
                    "message": msg,
                    "data": {"hits": hits},
                    "error": None,
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
                }
            except Exception as exc:
                return {
                    "capability": "memory",
                    "ok": False,
                    "message": "",
                    "data": {},
                    "error": str(exc),
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
                }
        return {
            "capability": organ,
            "ok": False,
            "message": "",
            "data": {},
            "error": f"no executor for organ {organ}",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
        }
    except Exception as exc:
        return {
            "capability": organ,
            "ok": False,
            "message": "",
            "data": {},
            "error": str(exc),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
        }


def orchestrate_compose(prompt: str, *, plan: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a multi-capability plan and compose one natural response."""
    from aria_core.observability import annotate_part, capability_plan_view
    from aria_core.response_composer import compose_natural

    plan = plan or plan_request(prompt)
    if not plan.get("combine"):
        selected = list(plan.get("selected") or [])
        if len(selected) < 2:
            return {
                "ok": False,
                "message": "Not a multi-capability request.",
                "error": "not_combine",
                "plan": plan,
            }

    cognition_id = str(uuid.uuid4())
    t0 = time.perf_counter()
    events: list[str] = ["CognitionStarted"]
    selected = [o for o in (plan.get("selected") or []) if o != "composer"]
    skipped = list(plan.get("skipped") or [])
    _emit(
        "CognitionStarted",
        cognition_id=cognition_id,
        capability="compose",
        selected=selected,
        combine=True,
    )

    parts: list[dict[str, Any]] = []
    executed: list[str] = []
    failed: list[str] = []

    for organ in selected:
        _emit(
            "CapabilitySelected",
            cognition_id=cognition_id,
            capability="compose",
            organ=organ,
        )
        events.append("CapabilitySelected")
        part = annotate_part(_execute_organ(organ, plan))
        parts.append(part)
        if part.get("ok"):
            executed.append(organ)
        else:
            failed.append(organ)
            _emit(
                "CapabilityFailed",
                cognition_id=cognition_id,
                capability="compose",
                organ=organ,
                error=part.get("error"),
            )
            events.append("CapabilityFailed")

    for organ in skipped:
        _emit(
            "CapabilitySkipped",
            cognition_id=cognition_id,
            capability="compose",
            organ=organ,
            reason="not-required-for-request",
        )
        events.append("CapabilitySkipped")

    _emit(
        "CapabilitySelected",
        cognition_id=cognition_id,
        capability="compose",
        organ="composer",
    )
    events.append("CompositionStarted")
    message = compose_natural(parts)
    events.append("CompositionCompleted")

    duration_ms = round((time.perf_counter() - t0) * 1000, 3)
    ok = bool(executed)
    _emit(
        "CognitionCompleted",
        cognition_id=cognition_id,
        capability="compose",
        ok=ok,
        duration_ms=duration_ms,
        executed=executed,
        failed=failed,
    )
    events.append("CognitionCompleted")

    plan_out = {
        **plan,
        "executed": executed,
        "failed": failed,
        "duration_ms": duration_ms,
        "parts": [
            {
                "capability": p.get("capability"),
                "ok": p.get("ok"),
                "latency_ms": p.get("latency_ms"),
                "error": p.get("error"),
            }
            for p in parts
        ],
        "execution_plan_display": " → ".join([*(selected or []), "composer"]),
        "skip_reasons": {o: "not-required-for-request" for o in skipped},
        "provenance": [
            {
                "capability": p.get("capability"),
                "provenance": p.get("provenance"),
                "confidence": p.get("confidence"),
            }
            for p in parts
        ],
        "section_confidence": {p.get("capability"): p.get("confidence") for p in parts},
    }
    plan_out["plan_view"] = capability_plan_view(plan_out, action="cognitive_compose")
    plan_out["plan_view"]["final_response_latency_ms"] = duration_ms
    _record(
        cognition_id=cognition_id,
        capability="compose",
        plan=plan_out,
        ok=ok,
        duration_ms=duration_ms,
        events_published=events,
        meta={"action": "cognitive_compose", "combine": True},
    )
    return {
        "ok": ok,
        "message": message,
        "data": {
            "plan": plan_out,
            "parts": parts,
            "cognition_id": cognition_id,
            "duration_ms": duration_ms,
        },
        "source": "cognitive_orchestrator",
        "type": "info",
    }


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
    plan_view = plan.get("plan_view") or {}
    stages = plan_view.get("stages") or {
        "planner": list(plan.get("selected") or []),
        "execution": list(plan.get("executed") or plan.get("selected") or []),
        "composer": "completed" if plan.get("combine") or capability == "compose" else "n/a",
        "final_response": "emitted",
    }
    rec = {
        "id": cognition_id,
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "capability": capability,
        "selected": list(plan.get("selected") or []),
        "skipped": list(plan.get("skipped") or []),
        "skip_reasons": dict(plan.get("skip_reasons") or {}),
        "execution_order": list(plan.get("execution_order") or []),
        "executed": list(plan.get("executed") or plan.get("selected") or []),
        "failed": list(plan.get("failed") or []),
        "execution_plan_display": plan.get("execution_plan_display")
        or " → ".join(plan.get("execution_order") or plan.get("selected") or []),
        "stages": stages,
        "plan_view": plan_view,
        "waterfall": plan_view.get("waterfall"),
        "provenance": plan.get("provenance") or [],
        "section_confidence": plan.get("section_confidence") or {},
        "ok": ok,
        "duration_ms": duration_ms,
        "events_published": list(events_published),
        "decision_metadata": {
            "policy": plan.get("policy"),
            "learning": plan.get("learning"),
            "clarification": plan.get("clarification"),
            "combine": plan.get("combine"),
            "request_event": plan.get("request_event"),
            "architectural": plan.get("architectural"),
            **{k: v for k, v in meta.items() if k in ("query_len", "action", "kind", "combine")},
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
    latest = pipes[-1] if pipes else None
    return {
        "ok": True,
        "title": "Aria Core Cognition",
        "owner": "aria_core.cognition",
        "version": COGNITION_VERSION,
        "health": {"ok": True, "policy": "compose-when-multi"},
        "statistics": stats,
        "pipelines": pipes,
        "latest_execution_plan": (latest or {}).get("execution_plan_display"),
        "latest_stages": (latest or {}).get("stages"),
        "latest_waterfall": (latest or {}).get("waterfall"),
        "latest_provenance": (latest or {}).get("provenance") or [],
        "latest_section_confidence": (latest or {}).get("section_confidence") or {},
        "composition_stages": ["planner", "execution", "composer", "final_response"],
        "latency": {
            "p50_ms": stats.get("latency_p50_ms"),
            "max_ms": stats.get("latency_max_ms"),
        },
        "organs": list(COGNITIVE_ORGANS),
        "verb_policy": {k: {"organ": v[0], "request_event": v[1]} for k, v in VERB_POLICY.items()},
        "note": (
            "Cognitive Orchestrator coordinates Cap Bus verbs and multi-capability "
            "chat plans (Planner → Execution → Composer → Final Response). "
            "Execution metadata only — no chain-of-thought."
        ),
    }
