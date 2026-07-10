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
    trace = {
        "prompt": (message or "")[:200],
        "intent": action,
        "route": intent.get("route") or classify_route(action),
        "reason": reason or intent.get("route_reason") or intent.get("thinking") or stage,
        "confidence": confidence if confidence is not None else intent.get("route_confidence"),
        "handler": handler or intent.get("route_handler") or handler_for_action(action),
        "stage": stage,
    }
    intent.setdefault("route_trace", trace)
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
