"""Runtime routing — highest-priority intent selection for Mission Control queries."""

from __future__ import annotations

import re
from typing import Any

# Keywords that must never route to web search / RAG — answered via RuntimeClient.
_RUNTIME_KEYWORD_TERMS: tuple[str, ...] = (
    "status",
    "health",
    "runtime",
    "platform",
    "mission control",
    "cpu",
    "ram",
    "swap",
    "gpu",
    "vram",
    "hardware",
    "services",
    "service",
    "providers",
    "provider",
    "models",
    "model",
    "jobs",
    "job",
    "activity",
    "databases",
    "database",
    "memory",
    "knowledge",
    "ollama",
    "litellm",
    "redis",
    "postgres",
    "mongodb",
    "qdrant",
    "grafana",
    "prometheus",
    "n8n",
)

_RUNTIME_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in _RUNTIME_KEYWORD_TERMS) + r")\b",
    re.I,
)

# General encyclopedic / how-to questions about a technology — not live system state.
_ENCYCLOPEDIC_EXCLUDE = re.compile(
    r"\b(?:"
    r"history of|invented by|founded in|when was|who (?:created|invented|founded)|"
    r"difference between|compare .{0,40} (?:vs|versus)|"
    r"how to (?:install|setup|set up|configure|deploy|compile|build)|"
    r"tutorial|documentation for|learn about|teach me about|"
    r"what is a |what are (?:the )?(?:benefits|advantages|disadvantages)"
    r")\b",
    re.I,
)

# User memory commands — must route to MemoryStore, not RuntimeClient.
_USER_MEMORY_EXCLUDE = re.compile(
    r"\b("
    r"search my memory|search memory|find in memory|memory search|"
    r"what do you remember|recall|my memories|"
    r"remember (?:that|these)|don't forget|note that|keep in mind|"
    r"forget|delete memory|remove memory|"
    r"something i like|what do i like|about me|who am i|tell me about myself|"
    r"why\b.+\b(?:favorite|favourite)|"
    r"why\b.+\b(?:isn'?t|is\s+not|no\s+longer)\b.+\bactive|"
    r"why\b.+\bactive|"
    r"what\s+replaced|"
    r"retired|superseded|replaced|"
    r"evidence|"
    r"history behind this memory|"
    r"why this memory changed|"
    r"(?:yesterday|today|this\s+morning|last\s+week|last\s+tuesday)\s+i\s+"
    r"(?:bought|cleaned|went|installed|visited)|"
    r"i\s+(?:bought|cleaned|went|installed|visited)\s+.+\s+"
    r"(?:yesterday|today|this\s+morning|last\s+week)|"
    r"what\s+happened|what\s+did\s+i\s+\w+"
    r")\b",
    re.I,
)

_KEYWORD_ACTION_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\b(full status|runtime report|system report|diagnostics?)\b", re.I),
        "runtime_report",
    ),
    (
        re.compile(r"\b(databases?|postgres|mongodb|mongo|redis|qdrant)\b", re.I),
        "runtime_databases",
    ),
    (re.compile(r"\b(services?|grafana|prometheus|n8n)\b", re.I), "runtime_services"),
    (re.compile(r"\b(models?|ollama|litellm)\b", re.I), "runtime_models"),
    (re.compile(r"\b(how much )?ram\b|\bsystem memory\b", re.I), "runtime_ram"),
    (re.compile(r"\b(disk|storage)\b", re.I), "runtime_storage"),
    (re.compile(r"\bnetwork\b", re.I), "runtime_network"),
    (re.compile(r"\b(gpu|vram|cpu|hardware|graphics)\b", re.I), "runtime_gpu"),
    (re.compile(r"\b(jobs?|activity)\b", re.I), "runtime_jobs"),
    (re.compile(r"\b(providers?|memory provider|knowledge provider)\b", re.I), "runtime_providers"),
    (
        re.compile(r"\b(platform|mission control|runtime|attached|connected)\b", re.I),
        "runtime_platform",
    ),
    (re.compile(r"\bapplications?\b", re.I), "runtime_applications"),
    (re.compile(r"\b(needs attention|attention)\b", re.I), "runtime_attention"),
    (re.compile(r"\b(status|health)\b", re.I), "runtime_health"),
)


def is_runtime_routing_question(message: str) -> bool:
    """True when the prompt must be answered from Mission Control, never web search."""
    from jarvis.runtime_introspection import is_runtime_introspection_question, is_status_command

    if is_runtime_introspection_question(message):
        return True
    if is_status_command(message):
        return True
    text = (message or "").strip()
    if len(text) < 2:
        return False
    if _ENCYCLOPEDIC_EXCLUDE.search(text):
        return False
    if _USER_MEMORY_EXCLUDE.search(text):
        return False
    try:
        from jarvis.nlu.episodic_patterns import is_episodic_memory_utterance

        if is_episodic_memory_utterance(text):
            return False
    except Exception:
        pass
    return bool(_RUNTIME_KEYWORD_RE.search(text))


def classify_runtime_from_keywords(message: str) -> str:
    text = (message or "").strip()
    for pattern, action in _KEYWORD_ACTION_RULES:
        if pattern.search(text):
            return action
    return "runtime_status"


def route_runtime_priority(message: str) -> dict[str, Any] | None:
    """Return runtime router intent when prompt must use RuntimeClient."""
    if not is_runtime_routing_question(message):
        return None

    from jarvis.runtime_introspection import is_status_command, route_runtime_introspection

    if runtime_hit := route_runtime_introspection(message):
        return {
            **runtime_hit,
            "route_reason": "runtime_introspection_pattern",
            "route_confidence": 1.0,
            "route_handler": "RuntimeClient",
        }

    if status_action := is_status_command(message):
        return {
            "action": status_action,
            "params": {},
            "thinking": "runtime status command",
            "route_reason": "runtime_status_command",
            "route_confidence": 1.0,
            "route_handler": "RuntimeClient",
        }

    action = classify_runtime_from_keywords(message)
    return {
        "action": action,
        "params": {},
        "thinking": "runtime keyword routing",
        "route_reason": "runtime_keyword",
        "route_confidence": 0.95,
        "route_handler": "RuntimeClient",
    }


def runtime_trace_steps(message: str, action: str) -> list[str]:
    return [
        f"Prompt: {message[:160]}",
        f"Intent: {action}",
        "Route: Runtime",
        "Handler: RuntimeClient",
        "Backend: Mission Control",
        "Response: live runtime data",
    ]
