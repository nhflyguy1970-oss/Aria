"""Unified Voice settings — single store for speak, STT, duplex, cloud prefs, profiles."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

VOICE_FILE = DATA_DIR / "voice_product" / "settings.json"
# Migration source only; new writes go to VOICE_FILE.
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


def _read_json(path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_voice_file(data: dict[str, Any]) -> None:
    VOICE_FILE.parent.mkdir(parents=True, exist_ok=True)
    VOICE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _legacy_patch(existing_keys: set[str]) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    legacy = _read_json(LEGACY_VOICE_FILE)
    for key, value in legacy.items():
        if key in DEFAULTS and key not in existing_keys and value is not None:
            patch[key] = value
    try:
        from jarvis.audio_settings import load_settings

        audio = load_settings()
        if "duplex_mode" not in existing_keys and "duplex_mode" not in patch and audio.get("duplex_mode"):
            patch["duplex_mode"] = audio["duplex_mode"]
    except Exception:
        pass
    if LEGACY_VOICE_FILE.is_file():
        try:
            LEGACY_VOICE_FILE.unlink()
        except OSError:
            pass
    return patch


def _load_raw() -> dict[str, Any]:
    voice = _read_json(VOICE_FILE)
    patch = _legacy_patch(set(voice))
    if patch:
        voice = {**voice, **patch}
        payload = {k: voice.get(k, DEFAULTS.get(k)) for k in {**DEFAULTS, **voice}}
        _write_voice_file(payload)
    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in voice.items() if v is not None})
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
    payload = {k: data.get(k, DEFAULTS.get(k)) for k in {**DEFAULTS, **data}}
    _write_voice_file(payload)
    return payload


def speak_replies_enabled() -> bool:
    return bool(load_unified_settings().get("speak_replies"))


def server_whisper_enabled() -> bool:
    return bool(load_unified_settings().get("server_whisper", True))
