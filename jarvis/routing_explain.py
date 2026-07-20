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
    "runtime": "live system status (Mission Control)",
    "mission_control": "live system status (Mission Control)",
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
        or str(data.get("intent") or "")
        or str(data.get("provider") or "")
        or str(data.get("handler") or "")
    ).strip().lower()
    for key, label in _CAPABILITY_LABELS.items():
        if key in raw:
            return label
    if raw.startswith("runtime") or "runtime" in raw:
        return _CAPABILITY_LABELS["runtime"]
    if raw.startswith("planner") or "planning" in raw:
        return _CAPABILITY_LABELS["planning"]
    if raw.startswith("coding") or "engineering" in raw:
        return _CAPABILITY_LABELS["coding"]
    if raw.startswith("memory") or "acm" in raw:
        return _CAPABILITY_LABELS["memory"]
    return "general conversation"


def _reason_for(data: dict[str, Any], message: str = "") -> str:
    text = (message or "").lower()
    provider = (data.get("provider") or "").lower()
    capability = (data.get("capability") or data.get("intent") or "").lower()
    policy = data.get("execution_policy") or {}
    policy_reason = str(policy.get("policy_reason") or policy.get("reason") or "").strip()

    if "mission control" in text:
        if provider in ("mission_control", "runtime") or capability.startswith("runtime"):
            return (
                "your previous question asked about the live workstation — "
                "hardware, services, or Mission Control status — so I used live system data"
            )
        return "your previous question did not go to Mission Control"

    if "acm" in text or "memory" in capability or provider == "acm":
        if provider == "acm" or capability.startswith("episodic") or "memory" in capability:
            return (
                "you asked about something you previously told me, "
                "so I answered from personal memory"
            )
        return "personal memory was not used for that request"

    if "deepseek" in text:
        selected = (data.get("selected_model") or "").lower()
        if "deepseek" in selected:
            return "a DeepSeek model was selected for that request"
        return (
            "DeepSeek was not selected for that request"
            + (f" ({policy_reason})" if policy_reason else "")
        )

    if "model" in text:
        selected = data.get("selected_model") or "the default assistant model"
        return f"the response used `{selected}` based on the request type"

    if "answer" in text or "response" in text or "choose" in text or "choice" in text:
        return (
            f"that matched the {_friendly_capability(data)} path "
            "for the previous request"
        )

    if policy_reason:
        return policy_reason.replace("_", " ")
    return f"that matched the {_friendly_capability(data)} path"


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
    reason = _reason_for(data, message)

    if "mission control" in text:
        if (data.get("provider") or "").lower() in ("mission_control", "runtime") or str(
            data.get("capability") or ""
        ).startswith("runtime"):
            return (
                f"That question went to Mission Control because {reason}. "
                f"I selected {capability}."
            )
        return (
            "That request did not go to Mission Control. "
            f"I treated it as {capability} because {reason}."
        )

    if "acm" in text:
        if (data.get("provider") or "").lower() == "acm" or str(
            data.get("capability", "")
        ).startswith("episodic"):
            return f"I used personal memory because {reason}."
        return f"I did not use personal memory for that request. I treated it as {capability}."

    return (
        f"I chose that answer because {reason}. "
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
