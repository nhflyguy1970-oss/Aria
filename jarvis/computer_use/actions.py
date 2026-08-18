"""Computer-use action catalog — classification, validation, redaction.

Actions are classified by impact so autonomy can be granted incrementally:
READ is safe to hand to a research agent, INTERACT changes page state, and
HIGH_IMPACT causes real-world side effects and is denied by default.

Redaction happens here rather than at the log call site, so a secret cannot
leak by someone forgetting to scrub one particular result path.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

# --- impact classes
READ = "read"
INTERACT = "interact"
HIGH_IMPACT = "high_impact"

ACTIONS: dict[str, dict[str, Any]] = {
    # READ — navigation and observation
    "navigate": {"impact": READ, "required": ("url",)},
    "back": {"impact": READ, "required": ()},
    "forward": {"impact": READ, "required": ()},
    "reload": {"impact": READ, "required": ()},
    "inspect": {"impact": READ, "required": ()},
    "extract": {"impact": READ, "required": ()},
    "screenshot": {"impact": READ, "required": ()},
    "wait": {"impact": READ, "required": ()},
    "close": {"impact": READ, "required": ()},
    # INTERACT — changes page state
    "click": {"impact": INTERACT, "required": ("target",)},
    "type": {"impact": INTERACT, "required": ("target", "text")},
    "select": {"impact": INTERACT, "required": ("target", "value")},
    "scroll": {"impact": INTERACT, "required": ()},
    # HIGH_IMPACT — real-world side effects, denied unless explicitly granted
    "submit": {"impact": HIGH_IMPACT, "required": ("target",)},
    "download": {"impact": HIGH_IMPACT, "required": ("url",)},
}

READ_ACTIONS = tuple(sorted(a for a, s in ACTIONS.items() if s["impact"] == READ))
INTERACT_ACTIONS = tuple(sorted(a for a, s in ACTIONS.items() if s["impact"] == INTERACT))
HIGH_IMPACT_ACTIONS = tuple(sorted(a for a, s in ACTIONS.items() if s["impact"] == HIGH_IMPACT))

# --- bounds. Conservative on purpose; a runaway browser task is expensive.
LIMITS = {
    "navigation_timeout_ms": 20000,
    "action_timeout_ms": 10000,
    "max_extract_chars": 20000,
    "max_actions_per_session": 200,
    "max_screenshots_per_session": 20,
    "session_ttl_s": 1800,
    "max_redirects": 10,
}


class ActionError(ValueError):
    """The requested computer-use action is invalid."""


class NavigationBlocked(ActionError):
    """The URL is not permitted by ARIA's navigation safety rules."""


def impact_of(action: str) -> str:
    spec = ACTIONS.get(action)
    if not spec:
        raise ActionError(f"Unknown computer-use action: {action!r}")
    return spec["impact"]


def validate(action: str, params: dict[str, Any]) -> dict[str, Any]:
    spec = ACTIONS.get(action)
    if not spec:
        raise ActionError(f"Unknown computer-use action: {action!r}")
    missing = [k for k in spec["required"] if not str(params.get(k) or "").strip()]
    if missing:
        raise ActionError(f"Action {action!r} requires: {missing}")
    return params


# --------------------------------------------------------------- URL safety

_PRIVATE_HOSTS = re.compile(
    r"^(localhost|127\.|10\.|192\.168\.|169\.254\.|::1$|\[::1\]|0\.0\.0\.0|"
    r"172\.(1[6-9]|2\d|3[01])\.)",
    re.I,
)
_ALLOWED_SCHEMES = ("http", "https")


def normalize_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        raise NavigationBlocked("URL required")
    if "://" not in raw:
        raw = "https://" + raw
    return raw


def check_url(url: str, *, allow_local: bool = False) -> str:
    """Validate a navigation target. Blocks internal hosts unless explicitly allowed.

    Without this an autonomous agent could be steered into ARIA's own loopback
    services, turning browsing into an SSRF path.
    """
    candidate = normalize_url(url)
    parts = urlsplit(candidate)
    if parts.scheme.lower() not in _ALLOWED_SCHEMES:
        raise NavigationBlocked(f"Scheme not permitted: {parts.scheme!r}")
    host = (parts.hostname or "").strip()
    if not host:
        raise NavigationBlocked(f"Malformed URL: {url!r}")
    if _PRIVATE_HOSTS.match(host) and not allow_local:
        raise NavigationBlocked(f"Navigation to internal host blocked: {host}")

    # Defer to ARIA's own risky-URL policy when it is available. An explicit
    # allow_local (local fixtures, deliberate internal targets) has already been
    # authorised by the caller, so the host policy must not veto it — otherwise
    # the flag has no effect at all.
    if allow_local:
        return candidate
    try:
        from jarvis.browser_agent import check_url_safe

        verdict = check_url_safe(candidate)
        if isinstance(verdict, dict) and verdict.get("ok") is False:
            raise NavigationBlocked(verdict.get("message") or "URL blocked by ARIA policy")
    except NavigationBlocked:
        raise
    except Exception:  # noqa: BLE001 - policy unavailable must not open the gate wider
        pass
    return candidate


# --------------------------------------------------------------- redaction

_SECRET_KEYS = re.compile(
    r"(pass(word|wd)?|secret|token|api[_-]?key|authorization|auth|cookie|session[_-]?id|"
    r"credential|bearer|otp|pin)",
    re.I,
)
_SECRETISH_VALUE = re.compile(
    r"(?i)\b(bearer\s+[a-z0-9._-]{8,}|sk-[a-z0-9]{12,}|eyJ[a-zA-Z0-9._-]{20,})"
)
REDACTED = "[redacted]"


def redact(value: Any, *, key: str = "") -> Any:
    """Strip credential-shaped data from anything that leaves the browser layer."""
    if key and _SECRET_KEYS.search(key):
        return REDACTED
    if isinstance(value, dict):
        return {k: redact(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return _SECRETISH_VALUE.sub(REDACTED, value)
    return value


def redact_params(action: str, params: dict[str, Any]) -> dict[str, Any]:
    """Typing into a password field must never echo the value back."""
    safe = redact(dict(params or {}))
    target = str(params.get("target") or "")
    if action == "type" and _SECRET_KEYS.search(target):
        safe["text"] = REDACTED
    return safe
