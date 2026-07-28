"""Unified Voice settings — single store for speak, STT, duplex, cloud prefs, profiles."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

VOICE_FILE = DATA_DIR / "voice_product" / "settings.json"
# Keep legacy path in sync for older readers
LEGACY_VOICE_FILE = DATA_DIR / "voice_settings.json"

DEFAULTS: dict[str, Any] = {
    "speak_replies": False,
    "server_whisper": True,
    "duplex_mode": "half",
    "stt_backend": "whisper",
    "tts_engine": "piper",
    "interrupt_on_speak": True,
    "speak_chunk_sentences": True,
    "tts_chunk_max_chars": 220,
    "tts_latency_target_ms": 800,
    "tts_min_chunk_chars": 24,
    "wake_word_enabled": False,
    "cloud_provider": "auto",  # auto | gemini_live only (openai hidden until WebRTC)
    "active_profile": "",
    "full_duplex_enabled": True,  # production: half + full wired via before_listen / barge-in
}


def _load_raw() -> dict[str, Any]:
    merged = dict(DEFAULTS)
    for path in (VOICE_FILE, LEGACY_VOICE_FILE):
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    merged.update({k: v for k, v in data.items() if v is not None})
            except (json.JSONDecodeError, OSError):
                pass
    # Migrate duplex from audio_settings when unified file has no explicit mode yet
    try:
        from jarvis.audio_settings import load_settings

        audio = load_settings()
        unified_has_duplex = False
        if VOICE_FILE.is_file():
            try:
                raw = json.loads(VOICE_FILE.read_text(encoding="utf-8"))
                unified_has_duplex = isinstance(raw, dict) and "duplex_mode" in raw
            except (json.JSONDecodeError, OSError):
                pass
        if audio.get("duplex_mode") and not unified_has_duplex:
            merged["duplex_mode"] = audio["duplex_mode"]
    except Exception:
        pass
    return merged


def load_unified_settings() -> dict[str, Any]:
    data = _load_raw()
    # Full duplex available when flag true; otherwise force half/off
    mode = str(data.get("duplex_mode") or "half").lower()
    if mode not in ("off", "half", "full"):
        mode = "half"
    if mode == "full" and not data.get("full_duplex_enabled", True):
        mode = "half"
    data["duplex_mode"] = mode
    # Never advertise openai as preferred until WebRTC exists
    if str(data.get("cloud_provider") or "").lower() == "openai_realtime":
        data["cloud_provider"] = "gemini_live"
    return data


def save_unified_settings(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    patch = dict(patch or {})
    data = load_unified_settings()
    for key, value in patch.items():
        if value is not None:
            data[key] = value
    if data.get("cloud_provider") == "openai_realtime":
        data["cloud_provider"] = "gemini_live"
    VOICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {k: data.get(k, DEFAULTS.get(k)) for k in {**DEFAULTS, **data}}
    VOICE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Mirror subset to legacy voice_settings for older modules
    try:
        LEGACY_VOICE_FILE.parent.mkdir(parents=True, exist_ok=True)
        legacy = {
            "duplex_mode": payload.get("duplex_mode"),
            "stt_backend": payload.get("stt_backend"),
            "interrupt_on_speak": payload.get("interrupt_on_speak"),
            "speak_chunk_sentences": payload.get("speak_chunk_sentences"),
            "tts_chunk_max_chars": payload.get("tts_chunk_max_chars"),
            "tts_latency_target_ms": payload.get("tts_latency_target_ms"),
            "tts_min_chunk_chars": payload.get("tts_min_chunk_chars"),
        }
        LEGACY_VOICE_FILE.write_text(json.dumps(legacy, indent=2), encoding="utf-8")
    except Exception:
        pass
    if "duplex_mode" in patch:
        try:
            from jarvis.audio_settings import load_settings, save_settings

            audio = load_settings()
            audio["duplex_mode"] = payload["duplex_mode"]
            save_settings(audio)
        except Exception:
            pass
    return payload


def speak_replies_enabled() -> bool:
    return bool(load_unified_settings().get("speak_replies"))


def server_whisper_enabled() -> bool:
    return bool(load_unified_settings().get("server_whisper", True))
