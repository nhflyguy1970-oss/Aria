"""Voice mode settings — duplex, STT backend, latency prefs.

Delegates persistence to voice_product.settings (unified store) while keeping
the legacy API for existing callers.
"""

from __future__ import annotations

from typing import Any

_LEGACY_KEYS = (
    "duplex_mode",
    "stt_backend",
    "interrupt_on_speak",
    "speak_chunk_sentences",
    "tts_chunk_max_chars",
    "tts_latency_target_ms",
    "tts_min_chunk_chars",
)


def load_voice_settings() -> dict[str, Any]:
    from jarvis.voice_product.settings import load_unified_settings

    data = load_unified_settings()
    return {k: data.get(k) for k in _LEGACY_KEYS}


def save_voice_settings(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    from jarvis.voice_product.settings import save_unified_settings

    patch = patch or {}
    # Accept speak_replies / server_whisper through this API too
    saved = save_unified_settings(patch)
    return {k: saved.get(k) for k in _LEGACY_KEYS}


def duplex_mode() -> str:
    from jarvis.p1_flags import duplex_voice_enabled
    from jarvis.voice_product.settings import load_unified_settings

    if not duplex_voice_enabled():
        return "off"
    data = load_unified_settings()
    mode = str(data.get("duplex_mode") or "half").strip().lower()
    if mode == "full" and not data.get("full_duplex_enabled", True):
        return "half"
    return mode if mode in ("off", "half", "full") else "half"


def stt_backend() -> str:
    from jarvis.p1_flags import realtime_stt_enabled
    from jarvis.voice_product.settings import load_unified_settings

    saved = str(load_unified_settings().get("stt_backend") or "whisper").strip().lower()
    if saved == "realtimestt" and realtime_stt_enabled():
        return "realtimestt"
    return "whisper"
