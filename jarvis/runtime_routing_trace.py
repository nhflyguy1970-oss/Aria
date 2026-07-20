"""Structured routing trace logging for debugging intent selection."""

from __future__ import annotations

import logging
from typing import Any

from jarvis.routing_inspector import classify_route, handler_for_action

logger = logging.getLogger("jarvis.router.trace")


def log_route_decision(
    *,
    message: str,
    intent: dict[str, Any],
    stage: str,
    reason: str | None = None,
    confidence: float | None = None,
    handler: str | None = None,
) -> dict[str, Any]:
    """Attach trace metadata to intent and emit a structured log line."""
    action = intent.get("action", "?")
    resolved_handler = handler or intent.get("route_handler") or handler_for_action(action)
    resolved_reason = reason or intent.get("route_reason") or intent.get("thinking") or stage
    trace = {
        "prompt": (message or "")[:200],
        "intent": action,
        "route": intent.get("route") or classify_route(action),
        "reason": resolved_reason,
        "confidence": confidence if confidence is not None else intent.get("route_confidence"),
        "handler": resolved_handler,
        "stage": stage,
    }
    intent.setdefault("route_trace", trace)
    # Skip recording explain queries as the "prior" decision.
    try:
        from jarvis.routing_explain import is_routing_explain_query
        from jarvis.routing_trace import record_route_decision_summary

        if not is_routing_explain_query(message or ""):
            action_s = str(action or "")
            provider = ""
            if action_s.startswith("runtime_") or action_s == "status_summary":
                provider = "mission_control"
            elif action_s.startswith("memory_") or action_s in ("remember", "recall"):
                provider = "acm"
            elif action_s.startswith("coding_"):
                provider = "coding"
            elif action_s.startswith("planner_"):
                provider = "planning"
            record_route_decision_summary(
                user_input=message or "",
                intent=str(intent.get("route_reason") or action_s),
                action=action_s,
                capability=action_s,
                handler=str(resolved_handler or ""),
                provider=provider,
                reason=str(resolved_reason or ""),
            )
    except Exception:
        pass
    logger.info(
        "route trace | intent=%s route=%s handler=%s reason=%s confidence=%s stage=%s prompt=%r",
        trace["intent"],
        trace["route"],
        trace["handler"],
        trace["reason"],
        trace["confidence"],
        trace["stage"],
        trace["prompt"],
    )
    return intent


# Legacy helpers kept for compatibility with older imports.
def _route_family(action: str) -> str:
    return classify_route(action)


def _handler_for_action(action: str) -> str:
    return handler_for_action(action)
