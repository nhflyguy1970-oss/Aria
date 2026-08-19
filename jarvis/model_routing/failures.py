"""Failure classification — deciding what actually went wrong, and whether
trying a different model could possibly help.

The important distinctions are not about severity. A cancellation and a policy
denial are both "not a success", but neither is a reason to go and run somebody
else's model: the user asked for it to stop, or ARIA refused on purpose.
"""

from __future__ import annotations

import re
from typing import Any

# Failure kinds.
UNAVAILABLE = "unavailable"
TIMEOUT = "timeout"
CONNECTION = "connection_failure"
MODEL_NOT_FOUND = "model_not_found"
CAPABILITY_MISMATCH = "capability_mismatch"
PROVIDER_ERROR = "provider_error"
MALFORMED_RESPONSE = "malformed_response"
CONTEXT_OVERFLOW = "context_overflow"
TOOL_INCOMPATIBLE = "tool_incompatibility"
STRUCTURED_OUTPUT_FAILED = "structured_output_failure"
CANCELLED = "cancelled"
POLICY_DENIED = "policy_denial"
INTERNAL = "internal_routing_error"

KINDS = (
    UNAVAILABLE,
    TIMEOUT,
    CONNECTION,
    MODEL_NOT_FOUND,
    CAPABILITY_MISMATCH,
    PROVIDER_ERROR,
    MALFORMED_RESPONSE,
    CONTEXT_OVERFLOW,
    TOOL_INCOMPATIBLE,
    STRUCTURED_OUTPUT_FAILED,
    CANCELLED,
    POLICY_DENIED,
    INTERNAL,
)

# Trying another model can only help when the problem is with *this* model or
# its provider. Cancellation and denial are decisions, not faults, and a
# malformed response or a failed schema may well repeat — but a different model
# is a reasonable next thing to try, so those do fall back.
FALLBACK_ELIGIBLE = frozenset(
    {
        UNAVAILABLE,
        TIMEOUT,
        CONNECTION,
        MODEL_NOT_FOUND,
        CAPABILITY_MISMATCH,
        PROVIDER_ERROR,
        MALFORMED_RESPONSE,
        CONTEXT_OVERFLOW,
        TOOL_INCOMPATIBLE,
        STRUCTURED_OUTPUT_FAILED,
    }
)

# Never retried: doing so would override an explicit decision.
NEVER_FALLBACK = frozenset({CANCELLED, POLICY_DENIED, INTERNAL})

_PATTERNS = (
    (re.compile(r"cancel", re.I), CANCELLED),
    (re.compile(r"not found|no such model|pull the model|does not exist", re.I), MODEL_NOT_FOUND),
    (re.compile(r"timed? ?out|deadline", re.I), TIMEOUT),
    (re.compile(r"connection|refused|unreachable|broken pipe|reset by peer", re.I), CONNECTION),
    (
        re.compile(r"context length|too many tokens|exceeds context|prompt is too long", re.I),
        CONTEXT_OVERFLOW,
    ),
    (re.compile(r"does not support tools|tool.{0,20}not supported", re.I), TOOL_INCOMPATIBLE),
    (
        re.compile(r"invalid json|malformed|could not parse|unexpected token", re.I),
        MALFORMED_RESPONSE,
    ),
    (re.compile(r"permission|denied|not permitted|unauthorized", re.I), POLICY_DENIED),
    (re.compile(r"unavailable|unload|out of memory|insufficient memory", re.I), UNAVAILABLE),
    (re.compile(r"gateway executed", re.I), PROVIDER_ERROR),
)


def classify(error: BaseException | str, *, default: str = PROVIDER_ERROR) -> str:
    """Name the failure. Exception type wins over message text where it is decisive."""
    if isinstance(error, BaseException):
        if isinstance(error, TimeoutError):
            return TIMEOUT
        if isinstance(error, ConnectionError):
            return CONNECTION
        text = f"{type(error).__name__}: {error}"
    else:
        text = str(error or "")
    for pattern, kind in _PATTERNS:
        if pattern.search(text):
            return kind
    return default


def may_fallback(kind: str) -> bool:
    """Whether this failure justifies trying a different model."""
    return kind in FALLBACK_ELIGIBLE


def describe(kind: str) -> str:
    return {
        CANCELLED: "the request was cancelled, so no other model was tried",
        POLICY_DENIED: "ARIA policy refused the request; a different model would not change that",
        INTERNAL: "routing itself failed; retrying a model would hide the bug",
    }.get(kind, f"model failed with {kind}")


def as_dict(kind: str, error: Any) -> dict[str, Any]:
    return {
        "kind": kind,
        "error": str(error)[:2000],
        "fallback_eligible": may_fallback(kind),
        "explanation": describe(kind),
    }
