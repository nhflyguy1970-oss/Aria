"""Identity rendering isolation — one requested identity per response (D044)."""

from __future__ import annotations

import re
from enum import StrEnum


class IdentityRenderTarget(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    RELATIONSHIP = "relationship"  # explicit multi-identity questions only


# Relationship / personalization glue — never on simple who-am-i / who-are-you.
_RELATIONSHIP_GLUE = re.compile(
    r"(?:"
    r"you\s+know\s+me\s+as|"
    r"i\s+know\s+you\s+as|"
    r"and\s+you\s+(?:are|know)|"
    r"while\s+you\s+are|"
    r"whereas\s+you|"
    r"we\s+(?:are|have)\b|"
    r"our\s+(?:relationship|work|project)|"
    r"together\s+we"
    r")",
    re.I,
)

# Assistant must never address the user on a simple Who are you?
_USER_ADDRESS = re.compile(
    r"\b(?:your\s+name\s+is|you\s+are|you\s+prefer|you\s+live|call\s+you)\b",
    re.I,
)

# User path must never claim assistant first-person autobiography.
_ASSISTANT_SELF_CLAIM = re.compile(
    r"\b(?:i\s+am|i'?m|my\s+name\s+is|i\s+am\s+known\s+as)\b",
    re.I,
)

_I_AM_KNOWN_AS = re.compile(r"\bi\s+am\s+known\s+as\s+([^.]+)\.?", re.I)


def is_relationship_identity_request(request: str) -> bool:
    """True when the user explicitly asks about the user↔assistant relationship."""
    t = (request or "").lower()
    cues = (
        "how do we know",
        "what have we worked",
        "worked on together",
        "learned about me",
        "know about me",
        "our relationship",
        "describe our relationship",
        "between us",
        "you and i",
        "you and me",
    )
    return any(c in t for c in cues)


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p.strip() for p in parts if p.strip()]


def isolate_identity_text(
    text: str | None,
    *,
    target: IdentityRenderTarget,
    forbidden_values: set[str] | None = None,
) -> str | None:
    """Keep only sentences that belong to the requested identity.

    Drops cross-identity personalization, relationship glue, and foreign names.
    """
    if not text or not str(text).strip():
        return None
    if target == IdentityRenderTarget.RELATIONSHIP:
        return str(text).strip()

    forbidden = {v.casefold() for v in (forbidden_values or set()) if v and str(v).strip()}
    kept: list[str] = []
    for part in _split_sentences(str(text)):
        low = part.lower()
        if _RELATIONSHIP_GLUE.search(part):
            continue
        if target == IdentityRenderTarget.ASSISTANT:
            if _USER_ADDRESS.search(part):
                continue
            m = _I_AM_KNOWN_AS.search(part)
            if m:
                # Legacy blend form — drop entirely from assistant identity speech
                continue
        if target == IdentityRenderTarget.USER:
            # First-person assistant autobiography on the user path is bleed
            if _ASSISTANT_SELF_CLAIM.search(part) and not re.search(
                r"\b(?:your|you)\b", low
            ):
                continue
        if forbidden and any(re.search(rf"\b{re.escape(v)}\b", low) for v in forbidden):
            continue
        kept.append(part if part.endswith((".", "!", "?")) else part + ".")
    out = " ".join(kept).strip()
    return out or None


def assistant_forbidden_from_user(user_attrs: list[tuple[str, str]]) -> set[str]:
    """Values from user identity that must not appear in assistant speech."""
    keys = {"name", "preferred_name", "location"}
    return {v for k, v in user_attrs if k in keys and v}


def user_forbidden_from_assistant(agent_attrs: list[tuple[str, str]], agent_id: str) -> set[str]:
    """Values from assistant identity that must not appear in user speech."""
    vals = {v for k, v in agent_attrs if k == "name" and v}
    if agent_id:
        vals.add(agent_id)
    return vals
