"""Instructional / meta-language stripping — never part of cognitive facts."""

from __future__ import annotations

import re

_INSTRUCTIONAL = re.compile(
    r"""
    (?:^|[.\s,;:!?])
    (?:
        please\s+remember(?:\s+that)?
      | remember\s+that
      | don'?t\s+forget(?:\s+that)?
      | keep\s+in\s+mind(?:\s+that)?
      | make\s+a\s+note(?:\s+of\s+that)?
      | note\s+that
      | for\s+future\s+reference
      | just\s+so\s+you\s+know
      | fyi
    )
    \s*[.!?]?\s*
    """,
    re.I | re.VERBOSE,
)

_REMEMBER_CUE = re.compile(
    r"\b(please\s+remember|remember\s+that|don'?t\s+forget|keep\s+in\s+mind)\b",
    re.I,
)


def has_remember_instruction(text: str) -> bool:
    return bool(_REMEMBER_CUE.search(text or ""))


def strip_instructional(text: str) -> tuple[str, bool]:
    """Remove instructional language; return (cleaned, stripped?)."""
    raw = (text or "").strip()
    if not raw:
        return "", False
    cleaned = _INSTRUCTIONAL.sub(" ", raw)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.!?])", r"\1", cleaned)
    cleaned = cleaned.strip(" ,;:")
    cleaned = cleaned.strip()
    cleaned = re.sub(r"[.]{2,}", ".", cleaned)
    changed = cleaned.casefold() != raw.casefold()
    return cleaned or raw, changed
