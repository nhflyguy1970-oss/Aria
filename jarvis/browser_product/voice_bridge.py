"""Voice control verbs for Browser — never purchases or destructive actions."""

from __future__ import annotations

import re
from typing import Any


_SAFE = re.compile(
    r"\b(pause|resume|take\s*over|takeover|stop|summarize(\s+page)?)\b",
    re.I,
)


def handle_voice_command(text: str, *, assistant=None) -> dict[str, Any]:
    lower = (text or "").strip().lower()
    if not lower:
        return {"ok": False, "error": "Empty voice command"}
    if re.search(r"\b(buy|purchase|pay|checkout|submit\s+payment|delete\s+account)\b", lower):
        return {
            "ok": False,
            "error": "Voice cannot execute purchases or destructive actions",
            "blocked": True,
        }
    from jarvis import browser_agent as ba

    if re.search(r"\bpause\b", lower):
        return {"ok": True, **ba.pause(), "voice": "pause"}
    if re.search(r"\bresume\b", lower):
        return {"ok": True, **ba.resume(), "voice": "resume"}
    if re.search(r"\b(take\s*over|takeover)\b", lower):
        return {"ok": True, **ba.takeover(), "voice": "takeover"}
    if re.search(r"\bstop\b", lower):
        return {"ok": True, **ba.stop(), "voice": "stop"}
    if re.search(r"\bsummarize\b", lower):
        from jarvis.browser_product.session import extract_text

        ext = extract_text(limit=3000)
        if not ext.get("ok"):
            return ext
        summary = (ext.get("text") or "")[:1200]
        return {
            "ok": True,
            "voice": "summarize",
            "message": f"Page summary excerpt:\n{summary}",
            "url": ext.get("url"),
            "title": ext.get("title"),
        }
    if not _SAFE.search(lower):
        return {
            "ok": False,
            "error": "Unsupported voice browser command",
            "allowed": ["pause", "resume", "takeover", "stop", "summarize page"],
        }
    return {"ok": False, "error": "Unrecognized command"}
