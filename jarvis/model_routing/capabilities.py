"""Capability vocabulary for model routing.

Support is deliberately three-valued. A model that does not advertise a
capability is UNKNOWN, not UNSUPPORTED, and UNKNOWN is never treated as
SUPPORTED when a caller requires the capability — ARIA must not claim a model
can do something it cannot verify.
"""

from __future__ import annotations

# Support states.
SUPPORTED = "supported"
UNKNOWN = "unknown"
UNSUPPORTED = "unsupported"
SUPPORT_STATES = (SUPPORTED, UNKNOWN, UNSUPPORTED)

# Capability vocabulary. Extensible: a new capability is a new constant plus,
# where possible, an evidence rule in profiles.py.
GENERAL_CHAT = "general_chat"
CODING = "coding"
REASONING = "reasoning"
RESEARCH = "research"
SUMMARIZATION = "summarization"
EXTRACTION = "extraction"
STRUCTURED_OUTPUT = "structured_output"
TOOL_USE = "tool_use"
VISION = "vision"
LONG_CONTEXT = "long_context"
FAST_RESPONSE = "fast_response"
HIGH_QUALITY = "high_quality"
LOCAL_ONLY = "local_only"
EMBEDDING = "embedding"

CAPABILITIES = (
    GENERAL_CHAT,
    CODING,
    REASONING,
    RESEARCH,
    SUMMARIZATION,
    EXTRACTION,
    STRUCTURED_OUTPUT,
    TOOL_USE,
    VISION,
    LONG_CONTEXT,
    FAST_RESPONSE,
    HIGH_QUALITY,
    LOCAL_ONLY,
    EMBEDDING,
)

# Capabilities where guessing is unsafe: requiring one of these and getting a
# model that merely *might* support it produces silent, confusing failure. For
# these, UNKNOWN is treated as a hard rejection.
SAFETY_CRITICAL = frozenset({TOOL_USE, VISION, STRUCTURED_OUTPUT, EMBEDDING})

# Ollama advertises these tokens directly on /api/show.
PROVIDER_CAPABILITY_TOKENS = {
    "tools": TOOL_USE,
    "vision": VISION,
    "embedding": EMBEDDING,
    "completion": GENERAL_CHAT,
    "thinking": REASONING,
}

LONG_CONTEXT_THRESHOLD = 32768


def satisfies(state: str, capability: str) -> bool:
    """Whether a support state is good enough to satisfy a hard requirement."""
    if state == SUPPORTED:
        return True
    if state == UNSUPPORTED:
        return False
    # UNKNOWN: acceptable only where a wrong guess degrades quality rather than
    # producing a result that is silently invalid.
    return capability not in SAFETY_CRITICAL


def normalise(capability: str) -> str:
    name = (capability or "").strip().lower()
    if name not in CAPABILITIES:
        raise ValueError(f"Unknown capability: {capability!r}")
    return name
