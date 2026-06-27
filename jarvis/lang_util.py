"""Lightweight text language hints for chat (no extra dependencies)."""

from __future__ import annotations

import re

_CYRILLIC = re.compile(r"[\u0400-\u04FF]")
_CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
_LATIN_EXTENDED = re.compile(r"[\u00c0-\u024f]")


def detect_text_language(text: str) -> str | None:
    """
    Rough ISO 639-1 hint for chat context, or None when English/unknown.
    """
    t = (text or "").strip()
    if len(t) < 8:
        return None
    letters = [c for c in t if c.isalpha()]
    if not letters:
        return None
    if _CJK.search(t):
        return "zh"
    if _CYRILLIC.search(t):
        return "ru"
    if _LATIN_EXTENDED.search(t):
        return "es"  # generic non-English Latin; model infers finer detail
    non_ascii = sum(1 for c in t if ord(c) > 127)
    if non_ascii / max(len(t), 1) > 0.08:
        return "und"
    return None


def language_reply_hint(code: str | None) -> str:
    if not code or code in ("en", "und"):
        return ""
    names = {
        "zh": "Chinese",
        "ru": "Russian",
        "es": "Spanish or another Latin-script language",
        "fr": "French",
        "de": "German",
    }
    label = names.get(code, f"language code {code}")
    return f"User message appears to be in {label}. Reply in the same language unless they ask otherwise."
