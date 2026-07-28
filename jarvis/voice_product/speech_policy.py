"""Speech policy — when and how to speak (one coherent model)."""

from __future__ import annotations

from typing import Any


def should_speak_reply(*, force: bool = False, muted: bool | None = None) -> bool:
    """Speak replies when enabled (or forced) and not muted."""
    if force:
        return True
    if muted is True:
        return False
    try:
        from jarvis.voice_product.settings import speak_replies_enabled

        return speak_replies_enabled()
    except Exception:
        return False


def sanitize_for_speech(text: str, *, max_chars: int = 4000) -> str:
    """Strip markdown noise for TTS without altering stored transcripts."""
    import re

    out = (text or "").strip()
    if not out:
        return ""
    out = re.sub(r"```[\s\S]*?```", " ", out)
    out = re.sub(r"`([^`]+)`", r"\1", out)
    out = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", out)
    out = re.sub(r"[#*_>~]+", " ", out)
    out = re.sub(r"\s+", " ", out).strip()
    if len(out) > max_chars:
        out = out[: max_chars - 1].rstrip() + "…"
    return out


def presentation_for_profile(
    *,
    transcript: str,
    audio_url: str | None,
    censored: bool,
    reveal: bool = False,
) -> dict[str, Any]:
    """
    Censored vs uncensored share storage. Presentation-only redaction when required.
    Never regenerate or delete original content.
    """
    if not censored or reveal:
        return {
            "transcript": transcript,
            "audio_url": audio_url,
            "redacted": False,
        }
    return {
        "transcript": "[Restricted — reveal to play]",
        "audio_url": None,
        "redacted": True,
        "has_original": bool(transcript or audio_url),
    }
