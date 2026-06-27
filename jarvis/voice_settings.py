"""Voice mode settings — duplex, STT backend, latency prefs."""

from __future__ import annotations

import json
from typing import Any

from jarvis.audio_settings import load_settings, save_settings
from jarvis.config import DATA_DIR

VOICE_FILE = DATA_DIR / "voice_settings.json"

_DEFAULTS = {
    "duplex_mode": "half",
    "stt_backend": "whisper",
    "interrupt_on_speak": True,
    "speak_chunk_sentences": True,
    "tts_chunk_max_chars": 220,
    "tts_latency_target_ms": 800,
    "tts_min_chunk_chars": 24,
}


def load_voice_settings() -> dict[str, Any]:
    merged = dict(_DEFAULTS)
    if VOICE_FILE.is_file():
        try:
            merged.update(json.loads(VOICE_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    try:
        audio = load_settings()
        if audio.get("duplex_mode"):
            merged["duplex_mode"] = audio["duplex_mode"]
    except Exception:
        pass
    return merged


def save_voice_settings(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    patch = patch or {}
    data = load_voice_settings()
    for key, value in patch.items():
        if value is not None:
            data[key] = value
    VOICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    VOICE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if "duplex_mode" in patch:
        try:
            audio = load_settings()
            audio["duplex_mode"] = patch["duplex_mode"]
            save_settings(audio)
        except Exception:
            pass
    return data


def duplex_mode() -> str:
    from jarvis.p1_flags import duplex_voice_enabled

    if not duplex_voice_enabled():
        return "off"
    mode = str(load_voice_settings().get("duplex_mode") or "half").strip().lower()
    return mode if mode in ("off", "half", "full") else "half"


def stt_backend() -> str:
    from jarvis.p1_flags import realtime_stt_enabled

    saved = str(load_voice_settings().get("stt_backend") or "whisper").strip().lower()
    if saved == "realtimestt" and realtime_stt_enabled():
        return "realtimestt"
    return "whisper"
