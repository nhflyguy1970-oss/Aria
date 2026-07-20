"""Routing explainability — debug-mode answers about routing decisions."""

from __future__ import annotations

import re
from typing import Any

from jarvis.routing_trace import (
    format_trace_text,
    last_routing_trace,
    routing_debug_enabled,
)

_EXPLAIN_RE = re.compile(
    r"\b("
    r"why did you choose that model|"
    r"why did you (?:pick|select|use) (?:that|this) model|"
    r"why did this route to mission control|"
    r"why (?:was|is) (?:this|that) (?:sent|routed) to mission control|"
    r"why was acm used|"
    r"why (?:didn't|did not|wasn't|was not) deepseek selected|"
    r"why (?:didn't|did not) (?:you )?use deepseek|"
    r"explain (?:the )?routing|"
    r"show (?:the )?routing trace|"
    r"why did you route"
    r")\b",
    re.I,
)


def is_routing_explain_query(message: str) -> bool:
    if not routing_debug_enabled():
        return False
    return bool(_EXPLAIN_RE.search((message or "").strip()))


def explain_routing(message: str = "", *, trace: dict[str, Any] | None = None) -> str:
    """Return routing trace narrative for a debug explain query."""
    data = trace or last_routing_trace()
    text = (message or "").lower()
    if not data:
        return (
            "No routing trace is stored yet. Enable routing debug (`JARVIS_ROUTING_DEBUG=1`) "
            "or trace capture (`JARVIS_ROUTING_TRACE=1`), send a request, then ask again."
        )

    if "mission control" in text:
        if (data.get("provider") or "").lower() in ("mission_control", "runtime"):
            return format_trace_text(data) + "\n\n**Answer:** This was classified as a live system/runtime query, not user memory or general chat."
        return format_trace_text(data) + "\n\n**Answer:** This request did **not** route to Mission Control."

    if "acm" in text:
        if (data.get("provider") or "").lower() == "acm" or data.get("capability", "").startswith("episodic"):
            return format_trace_text(data) + "\n\n**Answer:** ACM owns cognitive memory — teaching, recall, evidence, and explanation do not use a chat model."
        return format_trace_text(data) + "\n\n**Answer:** ACM was **not** used for this request."

    if "deepseek" in text:
        selected = (data.get("selected_model") or "").lower()
        configured = (data.get("configured_model") or "").lower()
        policy = data.get("execution_policy") or {}
        if "deepseek" in selected:
            return format_trace_text(data) + "\n\n**Answer:** A DeepSeek model **was** selected."
        reason = policy.get("policy_reason") or policy.get("reason") or "policy/default"
        fb = policy.get("fallback_model") or policy.get("fallback_active")
        extra = f" Fallback active: {fb}." if fb else ""
        return (
            format_trace_text(data)
            + f"\n\n**Answer:** DeepSeek was not selected. Configured: `{configured or '—'}`, "
            f"selected: `{selected or '—'}`. Policy: {reason}.{extra}"
        )

    if "model" in text:
        return format_trace_text(data)

    return format_trace_text(data)


def try_routing_explain(message: str) -> dict[str, Any] | None:
    """If debug explain query, return a chat-style ok payload."""
    if not is_routing_explain_query(message):
        return None
    return {
        "action": "chat",
        "params": {"routing_explain": True, "explain_text": explain_routing(message)},
        "thinking": "routing_explain",
        "route_reason": "routing_debug_explain",
        "route_handler": "RoutingExplain",
    }
