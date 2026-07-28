"""Voice profiles — reusable STT/TTS/duplex/cloud presets."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

PROFILES_FILE = DATA_DIR / "voice_product" / "profiles.json"

BUILTIN: list[dict[str, Any]] = [
    {
        "id": "quiet_office",
        "name": "Quiet Office",
        "builtin": True,
        "stt_engine": "whisper",
        "whisper_model": "base",
        "tts_engine": "piper",
        "voice": "",
        "speaking_rate": 1.0,
        "pitch": 1.0,
        "volume": 1.0,
        "duplex_mode": "half",
        "wake_word": False,
        "auto_speak": True,
        "cloud_or_local": "local",
        "latency_preference": "balanced",
    },
    {
        "id": "hands_free",
        "name": "Hands-Free",
        "builtin": True,
        "stt_engine": "whisper",
        "whisper_model": "base",
        "tts_engine": "piper",
        "voice": "",
        "speaking_rate": 1.0,
        "pitch": 1.0,
        "volume": 1.0,
        "duplex_mode": "full",
        "wake_word": True,
        "auto_speak": True,
        "cloud_or_local": "local",
        "latency_preference": "low",
    },
    {
        "id": "coding",
        "name": "Coding",
        "builtin": True,
        "stt_engine": "whisper",
        "whisper_model": "base",
        "tts_engine": "piper",
        "voice": "",
        "speaking_rate": 1.05,
        "pitch": 1.0,
        "volume": 0.9,
        "duplex_mode": "half",
        "wake_word": False,
        "auto_speak": False,
        "cloud_or_local": "local",
        "latency_preference": "balanced",
    },
    {
        "id": "presentation",
        "name": "Presentation",
        "builtin": True,
        "stt_engine": "whisper",
        "whisper_model": "small",
        "tts_engine": "piper",
        "voice": "",
        "speaking_rate": 0.95,
        "pitch": 1.0,
        "volume": 1.0,
        "duplex_mode": "half",
        "wake_word": False,
        "auto_speak": True,
        "cloud_or_local": "local",
        "latency_preference": "quality",
    },
    {
        "id": "dictation",
        "name": "Dictation",
        "builtin": True,
        "stt_engine": "whisper",
        "whisper_model": "small",
        "tts_engine": "piper",
        "voice": "",
        "speaking_rate": 1.0,
        "pitch": 1.0,
        "volume": 1.0,
        "duplex_mode": "off",
        "wake_word": False,
        "auto_speak": False,
        "cloud_or_local": "local",
        "latency_preference": "quality",
    },
    {
        "id": "accessibility",
        "name": "Accessibility",
        "builtin": True,
        "stt_engine": "whisper",
        "whisper_model": "base",
        "tts_engine": "piper",
        "voice": "",
        "speaking_rate": 0.9,
        "pitch": 1.0,
        "volume": 1.0,
        "duplex_mode": "half",
        "wake_word": True,
        "auto_speak": True,
        "cloud_or_local": "local",
        "latency_preference": "balanced",
    },
    {
        "id": "cloud_live",
        "name": "Cloud Live",
        "builtin": True,
        "stt_engine": "cloud",
        "whisper_model": "base",
        "tts_engine": "cloud",
        "voice": "",
        "speaking_rate": 1.0,
        "pitch": 1.0,
        "volume": 1.0,
        "duplex_mode": "full",
        "wake_word": False,
        "auto_speak": True,
        "cloud_or_local": "cloud",
        "latency_preference": "low",
    },
]


def _store() -> dict[str, Any]:
    if PROFILES_FILE.is_file():
        try:
            data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"custom": [], "active": ""}


def _save(store: dict[str, Any]) -> None:
    PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILES_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def list_profiles() -> list[dict[str, Any]]:
    store = _store()
    custom = [p for p in (store.get("custom") or []) if isinstance(p, dict)]
    return deepcopy(BUILTIN) + custom


def get_profile(profile_id: str) -> dict[str, Any] | None:
    pid = (profile_id or "").strip()
    for p in list_profiles():
        if p.get("id") == pid:
            return deepcopy(p)
    return None


def create_profile(body: dict[str, Any]) -> dict[str, Any]:
    store = _store()
    profile = {
        "id": str(body.get("id") or uuid.uuid4().hex[:12]),
        "name": str(body.get("name") or "Custom").strip() or "Custom",
        "builtin": False,
        "stt_engine": body.get("stt_engine") or "whisper",
        "whisper_model": body.get("whisper_model") or "base",
        "tts_engine": body.get("tts_engine") or "piper",
        "voice": body.get("voice") or "",
        "speaking_rate": float(body.get("speaking_rate") or 1.0),
        "pitch": float(body.get("pitch") or 1.0),
        "volume": float(body.get("volume") or 1.0),
        "duplex_mode": body.get("duplex_mode") or "half",
        "wake_word": bool(body.get("wake_word")),
        "auto_speak": bool(body.get("auto_speak", True)),
        "cloud_or_local": body.get("cloud_or_local") or "local",
        "latency_preference": body.get("latency_preference") or "balanced",
        "project_id": body.get("project_id") or "",
    }
    custom = list(store.get("custom") or [])
    custom.append(profile)
    store["custom"] = custom
    _save(store)
    return profile


def update_profile(profile_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    store = _store()
    custom = list(store.get("custom") or [])
    for i, p in enumerate(custom):
        if p.get("id") == profile_id and not p.get("builtin"):
            updated = {**p, **{k: v for k, v in patch.items() if k != "id" and k != "builtin"}}
            custom[i] = updated
            store["custom"] = custom
            _save(store)
            return updated
    # Duplicate builtin into custom then update
    base = get_profile(profile_id)
    if not base:
        return None
    if base.get("builtin"):
        base["id"] = uuid.uuid4().hex[:12]
        base["builtin"] = False
        base["name"] = f"{base.get('name')} (copy)"
        custom.append({**base, **{k: v for k, v in patch.items() if k not in ("id", "builtin")}})
        store["custom"] = custom
        _save(store)
        return custom[-1]
    return None


def delete_profile(profile_id: str) -> bool:
    store = _store()
    before = list(store.get("custom") or [])
    after = [p for p in before if p.get("id") != profile_id]
    if len(after) == len(before):
        return False
    store["custom"] = after
    if store.get("active") == profile_id:
        store["active"] = ""
    _save(store)
    return True


def duplicate_profile(profile_id: str) -> dict[str, Any] | None:
    src = get_profile(profile_id)
    if not src:
        return None
    src["id"] = uuid.uuid4().hex[:12]
    src["name"] = f"{src.get('name')} (copy)"
    src["builtin"] = False
    return create_profile(src)


def export_profiles() -> dict[str, Any]:
    return {"profiles": list_profiles(), "active": _store().get("active") or ""}


def import_profiles(payload: dict[str, Any]) -> dict[str, Any]:
    store = _store()
    imported = 0
    for p in payload.get("profiles") or []:
        if not isinstance(p, dict):
            continue
        if p.get("builtin"):
            continue
        p = dict(p)
        p["id"] = uuid.uuid4().hex[:12]
        p["builtin"] = False
        create_profile(p)
        imported += 1
    if payload.get("active"):
        store = _store()
        store["active"] = str(payload["active"])
        _save(store)
    return {"ok": True, "imported": imported}


def activate_profile(profile_id: str) -> dict[str, Any]:
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError("profile_not_found")
    store = _store()
    store["active"] = profile_id
    _save(store)
    from jarvis.voice_product.settings import save_unified_settings

    save_unified_settings(
        {
            "active_profile": profile_id,
            "duplex_mode": profile.get("duplex_mode") or "half",
            "stt_backend": profile.get("stt_engine") or "whisper",
            "tts_engine": profile.get("tts_engine") or "piper",
            "speak_replies": bool(profile.get("auto_speak")),
            "wake_word_enabled": bool(profile.get("wake_word")),
            "cloud_provider": "gemini_live" if profile.get("cloud_or_local") == "cloud" else "auto",
        }
    )
    return profile


def active_profile_id() -> str:
    return str(_store().get("active") or "")
