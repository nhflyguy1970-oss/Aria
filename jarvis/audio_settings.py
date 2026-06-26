"""Persisted audio input/output preferences (override jarvis.env when set from GUI)."""

from __future__ import annotations

import json
import os

from jarvis.config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "audio_settings.json"


def load_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_settings(patch: dict) -> dict:
    data = load_settings()
    data.update({k: v for k, v in patch.items() if v is not None})
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def saved_input_source() -> str:
    return (load_settings().get("input_source") or "").strip()


def saved_output_sink() -> str:
    return (load_settings().get("output_sink") or "").strip()


def saved_creative_capture_volume() -> str:
    return (load_settings().get("creative_capture_volume") or "").strip()


def saved_capture_volume() -> str:
    return (load_settings().get("capture_volume") or "").strip()


MIC_PROFILES = {
    "rear": {
        "label": "Rear desk mic (combo jack)",
        "expected_input_source": "Microphone",
        "default_capture_volume": "100%",
        "mic_boost_hint": "20 dB",
        "hint": "Plug mic into rear combo jack. alsamixer → Input Source = Microphone.",
    },
    "front": {
        "label": "Front gaming headset (combo jack)",
        "expected_input_source": "Front Microphone",
        "default_capture_volume": "100%",
        "mic_boost_hint": "10–20 dB",
        "hint": "Plug TRRS headset into front combo jack. alsamixer → Input Source = Front Microphone.",
    },
}


def saved_mic_profile() -> str:
    p = (load_settings().get("mic_profile") or "rear").strip().lower()
    return p if p in MIC_PROFILES else "rear"


WHISPER_MODELS = ("tiny", "base", "small", "medium", "large")


def saved_whisper_model() -> str:
    m = (load_settings().get("whisper_model") or "").strip().lower()
    return m if m in WHISPER_MODELS else ""


WHISPER_LANGUAGES = (
    "auto", "en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "ru", "ar", "hi",
)


def saved_whisper_language() -> str:
    lang = (load_settings().get("whisper_language") or "").strip().lower()
    if lang in WHISPER_LANGUAGES:
        return lang
    env = os.getenv("JARVIS_WHISPER_LANGUAGE", "auto").strip().lower()
    return env if env in WHISPER_LANGUAGES else "auto"


def saved_piper_speed() -> float:
    try:
        v = float(load_settings().get("piper_speed") or 1.0)
        return v if v > 0 else 1.0
    except (TypeError, ValueError):
        return 1.0


PIPER_SPEEDS = (0.8, 0.9, 1.0, 1.1, 1.2)


VST_PLAYBACK_CHAINS = ("flat", "voice", "music", "scout", "gaming", "custom")
VST_LIVE_CHAINS = ("off", "flat", "voice", "music", "scout", "gaming")


def saved_vst_playback_chain() -> str:
    c = (load_settings().get("vst_playback_chain") or "").strip().lower()
    return c if c in VST_PLAYBACK_CHAINS else ""


def saved_vst_live_chain() -> str:
    c = (load_settings().get("vst_live_chain") or "off").strip().lower()
    return c if c in VST_LIVE_CHAINS else "off"


def mic_profile_info(profile: str | None = None) -> dict:
    key = (profile or saved_mic_profile()).strip().lower()
    if key not in MIC_PROFILES:
        key = "rear"
    return {"id": key, **MIC_PROFILES[key]}
