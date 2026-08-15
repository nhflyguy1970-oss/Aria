"""ACM boundary — secrets must never enter ACM memories / search / exports."""

from __future__ import annotations

import re
from typing import Any

# Heuristic patterns for secret-shaped content (disposable / detection only).
_SECRET_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|secret|password|token|bearer)\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bsk-[a-z0-9]{16,}\b"),
    re.compile(r"(?i)\bghp_[a-z0-9]{20,}\b"),
    re.compile(r"(?i)\bhf_[a-z0-9]{20,}\b"),
    re.compile(r"(?i)BEGIN (RSA |OPENSSH )?PRIVATE KEY"),
    re.compile(r"(?i)\baria-owner-recovery\b"),
]

FORBIDDEN_ACM_FIELDS = frozenset(
    {
        "master_password",
        "recovery_key",
        "vault_root_key",
        "api_key",
        "password",
        "token",
        "oauth_token",
        "ha_token",
        "lan_api_key",
        "client_secret",
    }
)


def looks_like_secret(text: str) -> bool:
    s = (text or "").strip()
    if not s:
        return False
    if len(s) >= 32 and re.fullmatch(r"[0-9a-fA-F-]{32,}", s.replace(" ", "")):
        # Long hex / recovery-key shaped
        if s.count("-") >= 3 or len(s) >= 64:
            return True
    return any(p.search(s) for p in _SECRET_PATTERNS)


def assert_safe_for_acm(payload: Any, *, context: str = "acm") -> None:
    """Raise ValueError if payload appears to contain secret material."""
    if payload is None:
        return
    if isinstance(payload, dict):
        for k, v in payload.items():
            kl = str(k).lower()
            if kl in FORBIDDEN_ACM_FIELDS or any(f in kl for f in ("password", "secret", "token", "api_key")):
                raise ValueError(f"ACM boundary violation ({context}): forbidden field {k!r}")
            assert_safe_for_acm(v, context=context)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            assert_safe_for_acm(item, context=context)
        return
    if isinstance(payload, str) and looks_like_secret(payload):
        raise ValueError(f"ACM boundary violation ({context}): secret-shaped content refused")


def safe_metadata_only(**meta: Any) -> dict[str, Any]:
    """Filter to non-secret metadata suitable for ACM."""
    out = {}
    for k, v in meta.items():
        kl = str(k).lower()
        if kl in FORBIDDEN_ACM_FIELDS:
            continue
        if isinstance(v, str) and looks_like_secret(v):
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
    return out
