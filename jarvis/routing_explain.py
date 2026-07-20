"""Routing explainability — answers about routing decisions."""

from __future__ import annotations

import re
from typing import Any

from jarvis.routing_trace import (
    last_routing_trace,
    routing_debug_enabled,
)

_EXPLAIN_RE = re.compile(
    r"\b("
    r"why did you choose that (?:answer|response|model|capability|route)|"
    r"why did you (?:pick|select|use|choose) (?:that|this) (?:answer|response|model|capability|route)|"
    r"why did (?:this|that)(?:\s+(?:question|request|query))? (?:go|route|get sent) to mission control|"
    r"why did this route to mission control|"
    r"why (?:was|is) (?:this|that)(?:\s+(?:question|request|query))? (?:sent|routed|going) to mission control|"
    r"why was acm used|"
    r"why (?:didn't|did not|wasn't|was not) deepseek selected|"
    r"why (?:didn't|did not) (?:you )?use deepseek|"
    r"explain (?:the |your )?(?:routing|answer|choice|decision)|"
    r"show (?:the )?routing trace|"
    r"why did you route|"
    r"why (?:was|is) that (?:the )?(?:answer|response)"
    r")\b",
    re.I,
)

_CAPABILITY_LABELS = {
    "runtime": "live workstation status via Aria Mission Control",
    "mission_control": "live workstation status via Aria Mission Control",
    "memory": "personal memory",
    "acm": "personal memory",
    "episodic": "personal memory",
    "coding": "coding assistance",
    "planning": "planning",
    "planner": "planning",
    "reference": "documentation lookup",
    "knowledge": "general knowledge",
    "web_search": "web search",
    "chat": "general conversation",
    "conversation": "general conversation",
}


def is_routing_explain_query(message: str) -> bool:
    """True for routing explain queries — always intercept, never execute MC/memory."""
    return bool(_EXPLAIN_RE.search((message or "").strip()))


def _friendly_capability(data: dict[str, Any]) -> str:
    raw = (
        str(data.get("capability") or "")
        or str(data.get("action") or "")
        or str(data.get("intent") or "")
        or str(data.get("provider") or "")
        or str(data.get("handler") or "")
    ).strip().lower()
    for key, label in _CAPABILITY_LABELS.items():
        if key in raw:
            return label
    if raw.startswith("runtime") or "runtime" in raw or "status_summary" in raw:
        return _CAPABILITY_LABELS["runtime"]
    if raw.startswith("planner") or "planning" in raw:
        return _CAPABILITY_LABELS["planning"]
    if raw.startswith("coding") or "engineering" in raw:
        return _CAPABILITY_LABELS["coding"]
    if raw.startswith("memory") or "acm" in raw:
        return _CAPABILITY_LABELS["memory"]
    return "general conversation"


def _is_mission_control_route(data: dict[str, Any]) -> bool:
    provider = (data.get("provider") or "").lower()
    capability = str(data.get("capability") or data.get("action") or data.get("intent") or "").lower()
    handler = str(data.get("handler") or "").lower()
    if provider in ("mission_control", "runtime"):
        return True
    if capability.startswith("runtime") or capability == "status_summary":
        return True
    if "runtime" in handler or "mission" in handler:
        return True
    return False


def explain_routing(message: str = "", *, trace: dict[str, Any] | None = None) -> str:
    """Return a user-facing routing explanation — no internal implementation dump."""
    data = trace or last_routing_trace()
    text = (message or "").lower()
    if not data:
        hint = ""
        if not routing_debug_enabled():
            hint = " Ask again right after a request so I can explain that choice."
        return "I don't have a prior request to explain yet." + hint

    capability = _friendly_capability(data)
    prior = (data.get("user_input") or "").strip()
    prior_bit = f' (your previous request was “{prior[:120]}”)' if prior else ""

    if "mission control" in text:
        if _is_mission_control_route(data):
            return (
                "Aria Mission Control is the live workstation status service — "
                "not an unrelated product or game. "
                f"That question needed live system information{prior_bit}, "
                "so I used Mission Control instead of personal memory or a chat model. "
                "Cognition was not used because this was about current machine state, "
                "not something you previously taught me."
            )
        return (
            "That request did not go to Aria Mission Control. "
            f"I treated it as {capability}{prior_bit}."
        )

    if "acm" in text:
        if (data.get("provider") or "").lower() == "acm" or str(
            data.get("capability", "")
        ).startswith("episodic") or "memory" in str(data.get("capability") or "").lower():
            return (
                "I used personal memory because you asked about something you previously "
                f"told me{prior_bit}."
            )
        return f"I did not use personal memory for that request. I treated it as {capability}."

    if "deepseek" in text:
        selected = (data.get("selected_model") or "").lower()
        if "deepseek" in selected:
            return "A DeepSeek model was selected for that request."
        return "DeepSeek was not selected for that request."

    if "model" in text and "answer" not in text and "response" not in text:
        selected = data.get("selected_model") or "the default assistant model"
        return f"The response used `{selected}` based on the request type."

    return (
        f"I chose that answer because it matched the {capability} path"
        f"{prior_bit}. "
        f"Capability used: {capability}."
    )


def try_routing_explain(message: str) -> dict[str, Any] | None:
    """If explain query, return a chat-style ok payload — never execute Mission Control."""
    if not is_routing_explain_query(message):
        return None
    return {
        "action": "chat",
        "params": {"routing_explain": True, "explain_text": explain_routing(message)},
        "thinking": "routing_explain",
        "route_reason": "routing_debug_explain",
        "route_handler": "RoutingExplain",
    }
