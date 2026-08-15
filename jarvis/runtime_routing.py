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
    "disk",
    "storage",
    "filesystem",
    "drive",
    "volume",
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

# General encyclopedic / how-to / world-knowledge — not live Mission Control state.
_ENCYCLOPEDIC_EXCLUDE = re.compile(
    r"\b(?:"
    r"history of|invented by|founded in|when was|who (?:created|invented|founded)|"
    r"difference between|compare .{0,80} (?:vs|versus|and)|"
    r"how to (?:install|setup|set up|configure|deploy|compile|build)|"
    r"how (?:do|does|can|should|would)\s+i\b|"
    r"what should i (?:do|check|try|run)\b|"
    r"should i (?:run|delete|remove|format|wire|replace)\b|"
    r"research\b|recommend(?:ed)?\b|best (?:local|current|available)\b|"
    r"using current information|current information|"
    r"latest|newest|official documentation|find the official|"
    r"what does (?:the )?official|documentation say|"
    r"tutorial|documentation for|learn about|teach me about|"
    r"what is a |what are (?:the )?(?:benefits|advantages|disadvantages)|"
    r"good way to|ways? to (?:free|fix|check|clear|reduce)|"
    r"gpu driver|graphics driver|supported (?:nvidia |amd )?driver|"
    r"driver for linux|download (?:the )?nvidia|from nvidia|"
    r"modelfile|authoritative sources?|conflicting (?:web )?sources|"
    r"torque|brake|rotor|caliper|fsck|raid\b"
    r")\b",
    re.I,
)

# Live-state / ownership cues — required with bare runtime keywords (model/job/disk…).
_LIVE_STATE_CUE = re.compile(
    r"\b(?:"
    r"my|our|loaded|running|installed|available|free|attached|connected|"
    r"active|how much|show(?:\s+me)?(?:\s+the)?|"
    # Ownership/live only — not "what is the current NVIDIA driver" (world research).
    r"what(?:'s|\s+is)\s+(?:my|our)(?:\s+\w+){0,3}\s+(?:gpu|vram|cpu|ram|model|disk|status)|"
    r"what(?:'s|\s+is)\s+(?:my|our)\b|"
    r"is\s+\w+\s+(?:running|up|connected|healthy)|"
    r"are\s+\w+\s+(?:running|loaded|active)|"
    r"status|health(?!\s+records?)"
    r")\b|"
    r"(?:grafana|prometheus|n8n|ollama|litellm|postgres|redis|mongodb|qdrant)\s+up\b|"
    r"\b\w+\s+up\?",
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
    r"(?:yesterday|today|this\s+morning|last\s+week|last\s+tuesday|last\s+friday)\s+i\s+"
    r"(?:bought|cleaned|went|installed|visited|caught|fished)|"
    r"i\s+(?:bought|cleaned|went|installed|visited|caught|fished)\s+.+\s+"
    r"(?:yesterday|today|this\s+morning|last\s+week|last\s+friday)|"
    r"what\s+happened|what\s+did\s+i\s+\w+|where\s+did\s+i\s+go|"
    r"what\s+kind\s+of\s+.+\s+prefer"
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
    (re.compile(r"\b(disk|storage|filesystem|drive|volume)\b", re.I), "runtime_storage"),
    (re.compile(r"\bnetwork\b", re.I), "runtime_network"),
    # CPU before GPU — "CPU load?" must not surface VRAM-only answers.
    (re.compile(r"\bcpu\b", re.I), "runtime_cpu"),
    (re.compile(r"\b(gpu|vram|hardware|graphics)\b", re.I), "runtime_gpu"),
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


_WRITING_REQUEST = re.compile(
    r"\b(?:write|draft|compose|pen)\s+(?:me\s+)?(?:a\s+|an\s+|the\s+)?"
    r"(?:short\s+|quick\s+|casual\s+|one[- ]paragraph\s+|brief\s+)?"
    r"(?:project\s+)?(?:note|email|memo|letter|paragraph|summary|update|blurb|text|sms|message)\b|"
    r"\b(?:write|draft|compose)\s+(?:me\s+)?(?:a\s+)?(?:status\s+update|project\s+note)\b|"
    r"\b(?:draft|write)\s+(?:a\s+)?(?:short\s+)?(?:casual\s+)?(?:text|sms|email)\b|"
    r"\bproject\s+note\s+for\b",
    re.I,
)


def is_writing_request(message: str) -> bool:
    """True when the user asked to write/draft prose — not Mission Control status."""
    return bool(_WRITING_REQUEST.search(message or ""))


def is_runtime_routing_question(message: str) -> bool:
    """True when the prompt must be answered from Mission Control, never web search."""
    from jarvis.runtime_introspection import is_runtime_introspection_question, is_status_command

    text = (message or "").strip()
    if re.search(r"\bgit\s+(status|diff|commit|branch|log|push|pull)\b", text, re.I):
        return False
    if re.search(r"\b(what changed in git|create (?:a )?pull request|summarize (?:the )?diff)\b", text, re.I):
        return False
    # "Write a … status update" is prose, not MC health (RW-010).
    if is_writing_request(text):
        return False
    if is_runtime_introspection_question(message):
        return True
    if is_status_command(message):
        return True
    if len(text) < 2:
        return False
    if _ENCYCLOPEDIC_EXCLUDE.search(text):
        return False
    try:
        from jarvis.routing_explain import is_routing_explain_query

        if is_routing_explain_query(text):
            return False
    except Exception:
        pass
    if _USER_MEMORY_EXCLUDE.search(text):
        return False
    try:
        from jarvis.nlu.episodic_patterns import (
            is_episodic_memory_utterance,
            is_live_hardware_question,
            is_past_event_memory_question,
        )

        if is_episodic_memory_utterance(text) or is_past_event_memory_question(text):
            return False
        if is_live_hardware_question(text):
            return True
    except Exception:
        pass
    if not _RUNTIME_KEYWORD_RE.search(text):
        return False
    # Bare nouns like "models"/"job"/"service"/"disk" are not Mission Control
    # unless the user is asking about live workstation state.
    if _LIVE_STATE_CUE.search(text):
        return True
    # Short MC-style probes: "Status", "GPU?", "models?", "active jobs"
    if len(text) <= 48 and re.search(
        r"\b(status|health|models?|gpu|vram|cpu|ram|jobs?|services?|hardware|providers?)\b",
        text,
        re.I,
    ):
        return True
    return False


def classify_runtime_from_keywords(message: str) -> str:
    text = (message or "").strip()
    for pattern, action in _KEYWORD_ACTION_RULES:
        if pattern.search(text):
            return action
    return "runtime_status"


def route_runtime_priority(message: str) -> dict[str, Any] | None:
    """Return runtime router intent when prompt must use RuntimeClient."""
    text = (message or "").strip()
    # Git CLI intents must not be stolen by bare "status" / Mission Control.
    if re.search(r"\bgit\s+(status|diff|commit|branch|log|push|pull)\b", text, re.I):
        return None
    if re.search(r"\b(what changed in git|create (?:a )?pull request|summarize (?:the )?diff)\b", text, re.I):
        return None
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
