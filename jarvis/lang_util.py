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


def conversation_language(user_text: str, *, prior_user_texts: list[str] | None = None) -> str:
    """Active conversation language. Defaults to English unless user writes otherwise."""
    for blob in [user_text, *(prior_user_texts or [])]:
        code = detect_text_language(blob or "")
        if code and code not in ("und",):
            return code
    return "en"


def is_language_mismatch(user_text: str, reply_text: str) -> bool:
    """True when reply script diverges from the active conversation language."""
    active = conversation_language(user_text)
    reply = reply_text or ""
    # English conversations: any CJK/Cyrillic in the reply is a hard mismatch,
    # even for short strings (detect_text_language has an 8-char floor).
    if active == "en":
        if _CJK.search(reply) or _CYRILLIC.search(reply):
            return True
        reply_code = detect_text_language(reply)
        return bool(reply_code in ("zh", "ru"))
    if active == "zh":
        reply_code = detect_text_language(reply)
        return bool(reply_code and reply_code != "zh" and _CJK.search(user_text or ""))
    return False


def enforce_reply_language(user_text: str, reply_text: str, *, fallback: str = "") -> str:
    """Keep reply in the conversation language; drop mismatched host/LLM output."""
    text = (reply_text or "").strip()
    if not text:
        return fallback or text
    if is_language_mismatch(user_text, text):
        return (fallback or "").strip() or text
    return text


def language_reply_hint(code: str | None) -> str:
    if not code or code in ("en", "und"):
        # Explicit English lock stops unconstrained models from switching languages.
        return (
            "The active conversation language is English. "
            "Reply in English unless the user explicitly asks to switch languages."
        )
    names = {
        "zh": "Chinese",
        "ru": "Russian",
        "es": "Spanish or another Latin-script language",
        "fr": "French",
        "de": "German",
    }
    label = names.get(code, f"language code {code}")
    return f"User message appears to be in {label}. Reply in the same language unless they ask otherwise."
