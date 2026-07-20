"""Multi-capability request planning helpers (prompt → required organs)."""

from __future__ import annotations

import re
from typing import Any

_COMPOUND = re.compile(
    r"\b(?:"
    r"and tell me|and whether|and what|and if|and how|"
    r"also tell me|as well as|plus tell me"
    r")\b",
    re.I,
)

_REFERENCE = re.compile(
    r"\b(?:"
    r"documentation|docs?|readme|user guide|manual|adr|"
    r"architecture|capability bus|explain|show me|how does|"
    r"what is (?:the|a)|describe (?:the|how)"
    r")\b",
    re.I,
)

_RUNTIME = re.compile(
    r"\b(?:"
    r"running|healthy|health|status|currently|operating|available|"
    r"connected|applications?|services?|docker|mission control|"
    r"jobs?|gpu|ram|model|providers?"
    r")\b",
    re.I,
)

_MEMORY = re.compile(
    r"\b(?:"
    r"remember|recall|what do you know about me|my preference|"
    r"about me|from memory|search (?:my )?memory"
    r")\b",
    re.I,
)

_ADVISOR = re.compile(
    r"\b(?:"
    r"needs? attention|operational advisor|what should i do|"
    r"recommend(?:ation)?s?|what to do next"
    r")\b",
    re.I,
)

_ARCH_COMPONENT = re.compile(
    r"\b(?:capability bus|cognitive orchestrator|event bus|reflex layer)\b",
    re.I,
)

_SPLIT = re.compile(
    r"\b(?:and tell me|and whether|and what|and if|also tell me|as well as)\b",
    re.I,
)


def is_compound_request(prompt: str) -> bool:
    text = (prompt or "").strip()
    if len(text) < 12:
        return False
    return bool(_COMPOUND.search(text))


def detect_required_capabilities(prompt: str) -> list[str]:
    """Ordered organs required for this prompt."""
    text = (prompt or "").strip()
    if not text:
        return []
    try:
        from jarvis.routing_explain import is_routing_explain_query

        if is_routing_explain_query(text):
            return []
    except Exception:
        pass
    selected: list[str] = []
    if _REFERENCE.search(text):
        selected.append("reference")
    if _MEMORY.search(text) and "memory provider" not in text.lower():
        selected.append("memory")
    if _ADVISOR.search(text):
        if "runtime" not in selected:
            selected.append("runtime")
    elif _RUNTIME.search(text):
        selected.append("runtime")
    out: list[str] = []
    for item in selected:
        if item not in out:
            out.append(item)
    return out


def split_compound_prompt(prompt: str) -> tuple[str, str]:
    text = (prompt or "").strip()
    parts = _SPLIT.split(text, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(" ,."), parts[1].strip(" ,.?")
    return text, text


def runtime_action_for(prompt: str, *, runtime_clause: str = "") -> dict[str, Any]:
    """Choose runtime presentation action / notes for the live half of a compound ask."""
    blob = f"{prompt} {runtime_clause}".strip()
    lower = blob.lower()
    match = _ARCH_COMPONENT.search(blob)
    if match and re.search(r"\b(?:operating|running|normal|healthy|status)\b", lower):
        return {
            "runtime_action": "architectural_component",
            "architectural": True,
            "component": match.group(0),
        }
    if re.search(r"\bapplications?\b", lower):
        return {"runtime_action": "runtime_applications"}
    if re.search(r"\bmission control\b", lower) and re.search(
        r"\b(?:healthy|health|status)\b", lower
    ):
        return {"runtime_action": "runtime_health"}
    if re.search(r"\b(?:docker|services?)\b", lower):
        return {"runtime_action": "runtime_services"}
    if _ADVISOR.search(blob):
        return {"runtime_action": "runtime_attention"}
    try:
        from jarvis.runtime_introspection import classify_runtime_action

        return {"runtime_action": classify_runtime_action(blob)}
    except Exception:
        return {"runtime_action": "runtime_status"}


def build_request_plan(prompt: str) -> dict[str, Any]:
    """Build a multi-capability plan when the prompt requires composition."""
    from aria_core.cognitive_orchestrator import COGNITIVE_ORGANS

    text = (prompt or "").strip()
    caps = detect_required_capabilities(text)
    combine = is_compound_request(text) and len(caps) >= 2
    if not combine:
        return {
            "capability": "request",
            "selected": caps[:1] if caps else [],
            "skipped": [o for o in COGNITIVE_ORGANS if o not in caps[:1]],
            "execution_order": caps[:1] if caps else [],
            "combine": False,
            "policy": "passthrough-single",
            "prompt": text,
        }

    ref_clause, live_clause = split_compound_prompt(text)
    runtime_meta = runtime_action_for(text, runtime_clause=live_clause)
    selected = list(caps)
    skipped = [o for o in COGNITIVE_ORGANS if o not in selected]
    execution_order = list(selected) + ["composer"]
    return {
        "capability": "compose",
        "selected": selected,
        "skipped": skipped,
        "execution_order": execution_order,
        "combine": True,
        "policy": "multi-capability-compose",
        "prompt": text,
        "reference_query": ref_clause,
        "runtime_clause": live_clause,
        **runtime_meta,
        "request_event": "CapabilitySelected",
        "learning": False,
        "clarification": False,
    }
