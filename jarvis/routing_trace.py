"""Unified end-to-end routing trace — lightweight, disabled by default.

Records: input → intent → capability → role → policy → model → gateway → handler → presentation.
Never shown to normal users; used for debug/audit only.
"""

from __future__ import annotations

import contextvars
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any

_TRACE: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "routing_trace", default=None
)
_LAST_TRACE: dict[str, Any] | None = None
# Always-on lightweight decision for user-facing explainability (no debug flag required).
_LAST_DECISION: dict[str, Any] | None = None


def routing_debug_enabled() -> bool:
    return os.getenv("JARVIS_ROUTING_DEBUG", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ) or os.getenv("JARVIS_DEBUG", "0").strip().lower() in ("1", "true", "yes", "on")


def routing_trace_enabled() -> bool:
    if routing_debug_enabled():
        return True
    return os.getenv("JARVIS_ROUTING_TRACE", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


@dataclass
class RoutingTrace:
    schema: str = "routing_trace/1"
    user_input: str = ""
    intent: str = ""
    capability: str = ""
    role: str = ""
    configured_model: str | None = None
    selected_model: str | None = None
    execution_policy: dict[str, Any] = field(default_factory=dict)
    gateway_decision: dict[str, Any] = field(default_factory=dict)
    handler: str = ""
    provider: str = ""
    presentation: str | None = None
    response_kind: str = ""
    stages: list[dict[str, Any]] = field(default_factory=list)
    started_at: float = 0.0
    latency_ms: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _active() -> dict[str, Any] | None:
    if not routing_trace_enabled():
        return None
    return _TRACE.get()


def begin_trace(user_input: str) -> None:
    if not routing_trace_enabled():
        return
    _TRACE.set(
        {
            "trace": RoutingTrace(user_input=(user_input or "")[:500], started_at=time.perf_counter()),
            "t0": time.perf_counter(),
        }
    )


def _append_stage(name: str, detail: dict[str, Any]) -> None:
    ctx = _active()
    if not ctx:
        return
    trace: RoutingTrace = ctx["trace"]
    trace.stages.append({"stage": name, **detail, "ts": time.perf_counter()})


def record_intent(*, intent: str, action: str = "", reason: str = "", handler: str = "") -> None:
    ctx = _active()
    if not ctx:
        return
    trace: RoutingTrace = ctx["trace"]
    trace.intent = intent or action or trace.intent
    if handler:
        trace.handler = handler
    _append_stage(
        "intent",
        {"intent": trace.intent, "action": action, "reason": reason, "handler": handler},
    )


def record_capability(*, capability: str, role: str | None = None) -> None:
    ctx = _active()
    if not ctx:
        return
    trace: RoutingTrace = ctx["trace"]
    trace.capability = capability
    if role is not None:
        trace.role = role or "memory"
    _append_stage("capability", {"capability": capability, "role": role})


def record_model_selection(
    *,
    role: str,
    configured_model: str | None,
    selected_model: str | None,
    policy: dict[str, Any] | None = None,
    provider: str = "",
) -> None:
    ctx = _active()
    if not ctx:
        return
    trace: RoutingTrace = ctx["trace"]
    trace.role = role or trace.role
    trace.configured_model = configured_model
    trace.selected_model = selected_model
    if policy:
        trace.execution_policy = dict(policy)
    if provider:
        trace.provider = provider
    _append_stage(
        "model_policy",
        {
            "role": role,
            "configured_model": configured_model,
            "selected_model": selected_model,
            "policy": policy or {},
            "provider": provider,
        },
    )


def record_gateway(*, decision: dict[str, Any]) -> None:
    ctx = _active()
    if not ctx:
        return
    trace: RoutingTrace = ctx["trace"]
    trace.gateway_decision = dict(decision)
    if decision.get("provider"):
        trace.provider = str(decision["provider"])
    _append_stage("gateway", decision)


def record_handler(*, handler: str, provider: str = "") -> None:
    ctx = _active()
    if not ctx:
        return
    trace: RoutingTrace = ctx["trace"]
    trace.handler = handler
    if provider:
        trace.provider = provider
    _append_stage("handler", {"handler": handler, "provider": provider})


def record_presentation(*, layer: str, response_kind: str = "") -> None:
    ctx = _active()
    if not ctx:
        return
    trace: RoutingTrace = ctx["trace"]
    trace.presentation = layer
    if response_kind:
        trace.response_kind = response_kind
    _append_stage("presentation", {"layer": layer, "response_kind": response_kind})


def finalize_trace(*, response_kind: str = "") -> dict[str, Any] | None:
    global _LAST_TRACE
    ctx = _active()
    if not ctx:
        return None
    trace: RoutingTrace = ctx["trace"]
    trace.latency_ms = round((time.perf_counter() - ctx["t0"]) * 1000, 1)
    if response_kind:
        trace.response_kind = response_kind
    payload = trace.to_dict()
    _LAST_TRACE = payload
    _TRACE.set(None)
    return payload


def get_current_trace() -> dict[str, Any] | None:
    ctx = _active()
    if not ctx:
        return None
    trace: RoutingTrace = ctx["trace"]
    return trace.to_dict()


def last_routing_trace() -> dict[str, Any] | None:
    return _LAST_TRACE or _LAST_DECISION


def record_route_decision_summary(
    *,
    user_input: str = "",
    intent: str = "",
    action: str = "",
    capability: str = "",
    handler: str = "",
    provider: str = "",
    reason: str = "",
) -> None:
    """Persist a lightweight last-route summary for explainability (always on)."""
    global _LAST_DECISION
    _LAST_DECISION = {
        "user_input": (user_input or "")[:500],
        "intent": intent or action or "",
        "capability": capability or intent or action or "",
        "handler": handler or "",
        "provider": provider or "",
        "action": action or "",
        "route_reason": reason or "",
        "execution_policy": {"policy_reason": reason} if reason else {},
    }


def attach_trace_to_intent(intent: dict[str, Any]) -> dict[str, Any]:
    """Merge finalized or in-progress trace into router intent (debug only)."""
    if not routing_trace_enabled():
        return intent
    trace = get_current_trace() or last_routing_trace()
    if not trace:
        return intent
    out = dict(intent)
    out["routing_trace"] = trace
    return out


def format_trace_text(trace: dict[str, Any] | None = None) -> str:
    """Human-readable routing trace for debug explainability."""
    data = trace or last_routing_trace()
    if not data:
        return "No routing trace is available. Enable `JARVIS_ROUTING_TRACE=1` or routing debug mode."

    lines = [
        "**Routing trace**",
        "",
        f"**User input:** {(data.get('user_input') or '')[:200]}",
        f"**Intent:** {data.get('intent') or '—'}",
        f"**Capability:** {data.get('capability') or '—'}",
        f"**Role:** {data.get('role') or '—'}",
        f"**Configured model:** {data.get('configured_model') or 'none'}",
        f"**Selected model:** {data.get('selected_model') or 'none'}",
        f"**Provider:** {data.get('provider') or '—'}",
        f"**Handler:** {data.get('handler') or '—'}",
        f"**Presentation:** {data.get('presentation') or '—'}",
        f"**Response:** {data.get('response_kind') or '—'}",
    ]
    policy = data.get("execution_policy") or {}
    if policy:
        lines.extend(
            [
                "",
                "**Execution policy**",
                f"- Reason: {policy.get('policy_reason') or policy.get('reason') or '—'}",
                f"- Path: {policy.get('execution_path') or '—'}",
                f"- Fallback active: {policy.get('fallback_active', False)}",
            ]
        )
    gateway = data.get("gateway_decision") or {}
    if gateway:
        lines.extend(
            [
                "",
                "**Gateway**",
                f"- Backend: {gateway.get('backend') or gateway.get('execution_path') or '—'}",
                f"- Model: {gateway.get('model') or '—'}",
                f"- Reason: {gateway.get('reason') or '—'}",
            ]
        )
    if data.get("latency_ms") is not None:
        lines.append(f"\n**Trace latency:** {data.get('latency_ms')} ms")
    return "\n".join(lines)
