"""Operational observability helpers — metadata only, no behavior changes.

Provides capability health rollups, cross-capability usage analytics,
and provenance/confidence helpers for Conversation Trace + Mission Control.
Never includes chain-of-thought or memory/learning contents by default.
"""

from __future__ import annotations

import time
from collections import Counter
from typing import Any

# Organs / platform surfaces tracked for health (not only Docker services).
CAPABILITY_SURFACES: tuple[str, ...] = (
    "memory",
    "knowledge",
    "learning",
    "planning",
    "reasoning",
    "reference",
    "runtime",
    "capability_bus",
    "event_bus",
    "conversation_trace",
    "operational_advisor",
    "cognition",
)

# Provenance source labels for response sections.
PROVENANCE_SOURCES: tuple[str, ...] = (
    "runtime",
    "reference",
    "knowledge",
    "memory",
    "learning",
    "reasoning",
    "search",
    "inference",
    "composer",
)


def section_provenance(capability: str, *, ok: bool = True) -> dict[str, Any]:
    """Internal provenance tag for a response section (not shown by default)."""
    source = capability if capability in PROVENANCE_SOURCES else "composer"
    return {
        "source": source,
        "ok": bool(ok),
        "recorded_at": time.time(),
    }


def section_confidence(capability: str, *, ok: bool = True, architectural: bool = False) -> float:
    """Operational confidence estimate for a section (metadata only)."""
    if not ok:
        return 0.0
    if architectural:
        return 1.0
    defaults = {
        "runtime": 1.0,
        "reference": 1.0,
        "memory": 0.94,
        "knowledge": 0.96,
        "learning": 0.9,
        "reasoning": 0.92,
        "inference": 0.98,
        "search": 0.9,
        "composer": 1.0,
        "planning": 0.95,
    }
    return float(defaults.get(capability, 0.9))


def annotate_part(part: dict[str, Any]) -> dict[str, Any]:
    """Add provenance + confidence to an organ result part (non-destructive)."""
    cap = str(part.get("capability") or "composer")
    ok = bool(part.get("ok"))
    architectural = bool((part.get("data") or {}).get("architectural"))
    out = dict(part)
    out["provenance"] = section_provenance(cap, ok=ok)
    out["confidence"] = section_confidence(cap, ok=ok, architectural=architectural)
    return out


def capability_plan_view(plan: dict[str, Any] | None, *, action: str = "") -> dict[str, Any]:
    """Normalize a plan into Conversation Trace / MC display shape."""
    plan = plan or {}
    selected = [str(x) for x in (plan.get("selected") or []) if str(x) != "composer"]
    executed = [str(x) for x in (plan.get("executed") or selected)]
    failed = [str(x) for x in (plan.get("failed") or [])]
    skipped = [str(x) for x in (plan.get("skipped") or [])]
    skip_reasons = plan.get("skip_reasons") or {}
    if not skip_reasons:
        for organ in skipped:
            skip_reasons[organ] = (
                "passthrough-primary-only"
                if plan.get("policy", "").startswith("passthrough")
                else "not-required-for-request"
            )
    display = plan.get("execution_plan_display") or " → ".join(
        [*(selected or ([action] if action else [])), "composer"]
        if selected or action == "cognitive_compose"
        else ([action] if action else ["—"])
    )
    stages = {
        "planner": selected or ([action] if action and action != "cognitive_compose" else []),
        "execution": [
            {
                "capability": c,
                "status": "ok"
                if c in executed and c not in failed
                else ("fail" if c in failed else "pending"),
            }
            for c in (selected or executed or [])
        ],
        "composer": "completed" if plan.get("combine") or action == "cognitive_compose" else "n/a",
        "final_response": "emitted",
    }
    return {
        "display": display,
        "planned": selected,
        "executed": executed,
        "failed": failed,
        "skipped": skipped,
        "skip_reasons": skip_reasons,
        "composition_stage": bool(plan.get("combine") or action == "cognitive_compose"),
        "stages": stages,
        "policy": plan.get("policy"),
        "waterfall": _waterfall_text(selected, executed, failed, skipped, skip_reasons),
    }


def _waterfall_text(
    planned: list[str],
    executed: list[str],
    failed: list[str],
    skipped: list[str],
    skip_reasons: dict[str, Any],
) -> str:
    lines = ["Capability Plan"]
    plan_line = list(dict.fromkeys([*(planned or []), *skipped]))
    if plan_line:
        lines.extend(c.title() for c in plan_line)
    else:
        lines.append("(single / none)")
    lines.append("↓")
    lines.append("Execution")
    seen: set[str] = set()
    for c in plan_line or executed:
        if c in seen:
            continue
        seen.add(c)
        if c in failed:
            lines.append(f"✗ {c.title()} (failed)")
        elif c in skipped:
            reason = skip_reasons.get(c) or "skipped"
            lines.append(f"✗ {c.title()} ({reason})")
        else:
            lines.append(f"✓ {c.title()}")
    lines.append("↓")
    lines.append("Response Composer")
    lines.append("↓")
    lines.append("Final Response")
    return "\n".join(lines)


def _safe_call(label: str, fn) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        data = fn()
        ms = round((time.perf_counter() - t0) * 1000, 3)
        if isinstance(data, dict):
            ok = data.get("ok", True)
            if "health" in data and isinstance(data["health"], dict):
                ok = data["health"].get("ok", ok)
            return {
                "id": label,
                "ok": bool(ok),
                "latency_ms": ms,
                "detail": data.get("detail") or data.get("status") or "",
                "raw_keys": sorted(data.keys())[:12],
            }
        return {"id": label, "ok": True, "latency_ms": ms, "detail": ""}
    except Exception as exc:
        return {
            "id": label,
            "ok": False,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
            "detail": str(exc),
            "error": type(exc).__name__,
        }


def capability_health_snapshot() -> dict[str, Any]:
    """Health of Aria capabilities / buses / advisors — not Docker services."""
    rows: list[dict[str, Any]] = []

    def _probe_memory() -> dict[str, Any]:
        from aria_core.memory import memory_health

        return memory_health()

    def _probe_learning() -> dict[str, Any]:
        from aria_core.learning import mission_control_panel

        panel = mission_control_panel(limit=5)
        return {"ok": True, "detail": f"proposals={len(panel.get('proposals') or [])}"}

    def _probe_knowledge() -> dict[str, Any]:
        try:
            from aria_core.knowledge import mission_control_panel

            return mission_control_panel(limit=1)
        except Exception:
            return {"ok": True, "detail": "knowledge organ available"}

    def _probe_reference() -> dict[str, Any]:
        try:
            from aria_core import reference as ref_mod

            if hasattr(ref_mod, "mission_control_panel"):
                return ref_mod.mission_control_panel()
        except Exception:
            pass
        return {"ok": True, "detail": "reference organ available"}

    def _probe_cognition() -> dict[str, Any]:
        from aria_core.cognition import mission_control_panel

        return mission_control_panel(limit=5)

    def _probe_caps() -> dict[str, Any]:
        from aria_core.capability_bus import mission_control_panel

        return mission_control_panel()

    def _probe_events() -> dict[str, Any]:
        from aria_core.event_bus import get_bus

        bus = get_bus()
        count = getattr(bus, "subscriber_count", None)
        detail = f"subscribers={count()}" if callable(count) else "event bus ok"
        return {"ok": True, "detail": detail}

    def _probe_runtime() -> dict[str, Any]:
        try:
            from jarvis.runtime_client import get_runtime_client

            snap = get_runtime_client().snapshot(required=False)
            return {"ok": bool(snap.get("ok")), "detail": snap.get("connection_mode") or ""}
        except Exception as exc:
            return {"ok": False, "detail": str(exc)}

    def _probe_advisor() -> dict[str, Any]:
        try:
            from aiplatform.mission_control.operational_advisor import build_advice

            adv = build_advice() or {}
            return {"ok": True, "detail": str(adv.get("headline") or "")[:120]}
        except Exception:
            return {"ok": True, "detail": "advisor unavailable in-process"}

    def _probe_trace() -> dict[str, Any]:
        try:
            from aiplatform.mission_control.conversation_trace import analytics

            a = analytics(limit=20)
            return {
                "ok": True,
                "detail": f"traces={a.get('total')} avg_ms={a.get('avg_latency_ms')}",
            }
        except Exception:
            return {"ok": True, "detail": "trace analytics unavailable"}

    probes = {
        "memory": _probe_memory,
        "learning": _probe_learning,
        "knowledge": _probe_knowledge,
        "reference": _probe_reference,
        "planning": lambda: {"ok": True, "detail": "planning organ present"},
        "reasoning": lambda: {"ok": True, "detail": "reasoning organ present"},
        "runtime": _probe_runtime,
        "capability_bus": _probe_caps,
        "event_bus": _probe_events,
        "cognition": _probe_cognition,
        "conversation_trace": _probe_trace,
        "operational_advisor": _probe_advisor,
    }

    try:
        from aria_core.cognition import cognition_statistics, recent_pipelines

        stats = cognition_statistics()
        pipes = recent_pipelines(limit=50)
    except Exception:
        stats, pipes = {}, []

    last_ok: dict[str, float | None] = {}
    errors: Counter[str] = Counter()
    latency_sum: Counter[str] = Counter()
    latency_n: Counter[str] = Counter()
    consumers: Counter[str] = Counter()
    for p in pipes:
        for organ in p.get("executed") or p.get("selected") or []:
            consumers[str(organ)] += 1
            if p.get("ok"):
                last_ok[str(organ)] = p.get("ts")
            latency_sum[str(organ)] += float(p.get("duration_ms") or 0)
            latency_n[str(organ)] += 1
        for organ in p.get("failed") or []:
            errors[str(organ)] += 1

    for name in CAPABILITY_SURFACES:
        row = _safe_call(name, probes.get(name, lambda: {"ok": True}))
        n = latency_n.get(name) or 0
        err_n = errors.get(name) or 0
        total_n = max(consumers.get(name) or 0, n, 1)
        row.update(
            {
                "consumers": int(consumers.get(name) or 0),
                "avg_latency_ms": round(latency_sum[name] / n, 3) if n else row.get("latency_ms"),
                "error_rate": round(err_n / total_n, 4) if total_n else 0.0,
                "last_success_ts": last_ok.get(name),
            }
        )
        rows.append(row)

    healthy = sum(1 for r in rows if r.get("ok"))
    return {
        "ok": True,
        "title": "Capability Health",
        "owner": "aria_core.observability",
        "note": "Capability health is operational metadata — not service/container status.",
        "summary": {"total": len(rows), "healthy": healthy, "unhealthy": len(rows) - healthy},
        "capabilities": rows,
        "cognition_stats": stats,
    }


def cross_capability_analytics(*, limit: int = 200) -> dict[str, Any]:
    """Measure which capability combinations Aria actually uses."""
    combos: Counter[str] = Counter()
    try:
        from aria_core.cognition import recent_pipelines

        for p in recent_pipelines(limit=limit):
            executed = [
                str(x) for x in (p.get("executed") or p.get("selected") or []) if x != "composer"
            ]
            if not executed:
                cap = str(p.get("capability") or "unknown")
                combos[cap] += 1
            else:
                key = " + ".join(sorted(set(executed)))
                combos[key] += 1
    except Exception:
        pass

    try:
        from aiplatform.mission_control.conversation_trace import list_traces

        for tr in list_traces(limit=limit):
            ct = tr.get("conversation_trace") or tr
            cog = ct.get("cognition") or {}
            used = list(cog.get("subsystems_consulted") or [])
            if used:
                combos[" + ".join(sorted(set(used)))] += 1
    except Exception:
        pass

    ranked = [{"combo": k, "count": v} for k, v in combos.most_common(40)]
    return {
        "ok": True,
        "title": "Cross-Capability Analytics",
        "owner": "aria_core.observability",
        "note": "Usage frequency of capability combinations — guides optimization, not speculative features.",
        "total_observations": sum(combos.values()),
        "combinations": ranked,
        "examples": [
            "Reference",
            "Reference + Runtime",
            "Reference + Memory",
            "Runtime + Memory",
            "Reference + Runtime + Memory",
            "Knowledge + Runtime",
            "Coding + Reference",
            "Learning + Memory",
        ],
    }


def mission_control_panel() -> dict[str, Any]:
    panel = {
        "ok": True,
        "title": "Product Observability",
        "owner": "aria_core.observability",
        "capability_health": capability_health_snapshot(),
        "cross_capability": cross_capability_analytics(),
        "note": "Observability only — architecture frozen; Daily Use Mode governs implementation.",
    }
    try:
        from jarvis.reference_engine import mission_control_panel as ref_panel

        panel["reference"] = ref_panel(limit=20)
    except Exception as exc:
        panel["reference"] = {"ok": False, "error": str(exc)[:160]}
    return panel
