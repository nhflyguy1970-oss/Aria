"""Low-latency TTS chunking helpers (#26)."""

from __future__ import annotations

import re
import time
from typing import Any

from jarvis.voice_settings import load_voice_settings


def chunk_max_chars() -> int:
    return max(40, min(400, int(load_voice_settings().get("tts_chunk_max_chars") or 220)))


def min_chunk_chars() -> int:
    return max(8, min(80, int(load_voice_settings().get("tts_min_chunk_chars") or 24)))


_SOURCE_PREFIX_RE = re.compile(
    r"^(?:according to (?:the )?sources?(?: i(?:'ve| have) found)?|based on (?:my )?search|"
    r"from (?:my )?search|sources?:|references?:|"
    r"this (?:information|estimation) comes from|i(?:'ve| have) found|from historical records)"
    r"[,:]?\s*",
    re.I,
)
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
_CITATION_RE = re.compile(r"\[\d+\]|\(\s*source\s*:\s*[^)]+\)", re.I)


def sanitize_for_speech(text: str) -> str:
    """Strip markdown, citations, and source narration for natural TTS."""
    if not text:
        return ""
    out = str(text).strip()
    out = re.sub(r"```[\s\S]*?```", " ", out)
    out = re.sub(r"`([^`]+)`", r"\1", out)
    out = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", out)
    out = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", out)
    out = re.sub(r"^#{1,6}\s+", "", out, flags=re.M)
    out = re.sub(r"\*\*([^*]+)\*\*", r"\1", out)
    out = re.sub(r"\*([^*]+)\*", r"\1", out)
    out = _URL_RE.sub(" ", out)
    out = _CITATION_RE.sub(" ", out)
    lines = []
    for line in out.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^(?:source|reference|via)\s*:", stripped, re.I):
            continue
        if re.match(r"^[-*•]\s*(?:https?://|www\.)", stripped, re.I):
            continue
        stripped = _SOURCE_PREFIX_RE.sub("", stripped).strip()
        if not stripped or re.match(r"^[-*•]\s*$", stripped):
            continue
        lines.append(stripped)
    out = " ".join(lines)
    out = re.sub(
        r"\baccording to (?:the )?sources?(?: i(?:'ve| have) found)?[,.]?\s*",
        "",
        out,
        flags=re.I,
    )
    out = re.sub(r"\bbased on (?:my )?search[,.]?\s*", "", out, flags=re.I)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def split_speak_chunks(text: str, *, max_chars: int | None = None) -> list[str]:
    """Split plain text into speakable chunks (sentences, then max length)."""
    limit = max_chars or chunk_max_chars()
    plain = re.sub(r"\s+", " ", (text or "").strip())
    if not plain:
        return []
    parts: list[str] = []
    buf = ""
    for sentence in re.split(r"(?<=[.!?])\s+", plain):
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= limit:
            if buf and len(buf) + 1 + len(sentence) > limit:
                parts.append(buf)
                buf = sentence
            else:
                buf = f"{buf} {sentence}".strip() if buf else sentence
            continue
        if buf:
            parts.append(buf)
            buf = ""
        for i in range(0, len(sentence), limit):
            parts.append(sentence[i : i + limit].strip())
    if buf:
        parts.append(buf)
    return [p for p in parts if p]


def speak_chunk_metrics(text: str, *, generate_ms: int) -> dict[str, Any]:
    return {
        "chars": len(text or ""),
        "generate_ms": generate_ms,
        "chunk_max_chars": chunk_max_chars(),
    }
