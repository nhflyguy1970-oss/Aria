"""Smart Home profiles — reusable home / presence presets."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.home_assistant_product.settings import save_settings

PROFILES_FILE = DATA_DIR / "home_assistant_product" / "profiles.json"

BUILTIN: list[dict[str, Any]] = [
    {
        "id": "home",
        "name": "Home",
        "builtin": True,
        "favorite_rooms": [],
        "favorite_devices": [],
        "preferred_scenes": [],
        "default_brightness": 70,
        "default_color_temp_kelvin": 3000,
        "confirmation_policy": "ask",
        "speak_status": False,
        "voice_confirm": True,
        "notes": "Everyday at-home defaults",
    },
    {
        "id": "away",
        "name": "Away",
        "builtin": True,
        "favorite_rooms": [],
        "favorite_devices": [],
        "preferred_scenes": ["leaving"],
        "default_brightness": 0,
        "default_color_temp_kelvin": 2700,
        "confirmation_policy": "ask",
        "speak_status": True,
        "voice_confirm": True,
        "notes": "Leaving / away — prefer leave scene",
    },
    {
        "id": "office",
        "name": "Office",
        "builtin": True,
        "favorite_rooms": ["office"],
        "favorite_devices": [],
        "preferred_scenes": ["focus mode", "work mode"],
        "default_brightness": 80,
        "default_color_temp_kelvin": 4500,
        "confirmation_policy": "ask",
        "speak_status": False,
        "voice_confirm": False,
        "notes": "Desk / focus lighting",
    },
    {
        "id": "workshop",
        "name": "Workshop",
        "builtin": True,
        "favorite_rooms": ["workshop"],
        "favorite_devices": [],
        "preferred_scenes": [],
        "default_brightness": 90,
        "default_color_temp_kelvin": 5000,
        "confirmation_policy": "ask",
        "speak_status": False,
        "voice_confirm": True,
        "notes": "Bright task lighting",
    },
    {
        "id": "night",
        "name": "Night",
        "builtin": True,
        "favorite_rooms": [],
        "favorite_devices": [],
        "preferred_scenes": ["goodnight", "movie mode"],
        "default_brightness": 15,
        "default_color_temp_kelvin": 2200,
        "confirmation_policy": "ask",
        "speak_status": False,
        "voice_confirm": True,
        "notes": "Dim warm evening",
    },
    {
        "id": "vacation",
        "name": "Vacation",
        "builtin": True,
        "favorite_rooms": [],
        "favorite_devices": [],
        "preferred_scenes": ["leaving"],
        "default_brightness": 0,
        "default_color_temp_kelvin": 2700,
        "confirmation_policy": "ask",
        "speak_status": True,
        "voice_confirm": True,
        "notes": "Extended away — confirm before changes",
    },
    {
        "id": "quiet_hours",
        "name": "Quiet Hours",
        "builtin": True,
        "favorite_rooms": [],
        "favorite_devices": [],
        "preferred_scenes": ["relax"],
        "default_brightness": 25,
        "default_color_temp_kelvin": 2400,
        "confirmation_policy": "ask",
        "speak_status": False,
        "voice_confirm": True,
        "notes": "Low disturbance — soft lights, confirm scenes",
    },
]

_PROFILE_KEYS = (
    "favorite_rooms",
    "favorite_devices",
    "preferred_scenes",
    "default_brightness",
    "default_color_temp_kelvin",
    "confirmation_policy",
    "speak_status",
    "voice_confirm",
    "project_id",
)


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
    for p in list_profiles():
        if p.get("id") == profile_id:
            return deepcopy(p)
    return None


def create_profile(body: dict[str, Any]) -> dict[str, Any]:
    store = _store()
    profile: dict[str, Any] = {
        "id": str(body.get("id") or uuid.uuid4().hex[:12]),
        "name": str(body.get("name") or "Custom").strip() or "Custom",
        "builtin": False,
        "favorite_rooms": list(body.get("favorite_rooms") or []),
        "favorite_devices": list(body.get("favorite_devices") or []),
        "preferred_scenes": list(body.get("preferred_scenes") or []),
        "default_brightness": int(body.get("default_brightness") or 60),
        "default_color_temp_kelvin": int(body.get("default_color_temp_kelvin") or 2700),
        "confirmation_policy": body.get("confirmation_policy") or "ask",
        "speak_status": bool(body.get("speak_status", False)),
        "voice_confirm": bool(body.get("voice_confirm", True)),
        "project_id": body.get("project_id") or "",
        "notes": str(body.get("notes") or ""),
    }
    custom = list(store.get("custom") or [])
    custom.append(profile)
    store["custom"] = custom
    _save(store)
    return profile


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
    imported = 0
    for p in payload.get("profiles") or []:
        if not isinstance(p, dict) or p.get("builtin"):
            continue
        p = dict(p)
        p["id"] = uuid.uuid4().hex[:12]
        p["builtin"] = False
        create_profile(p)
        imported += 1
    return {"ok": True, "imported": imported}


def activate_profile(profile_id: str) -> dict[str, Any]:
    profile = get_profile(profile_id)
    if not profile:
        raise ValueError("profile_not_found")
    store = _store()
    store["active"] = profile_id
    _save(store)
    patch = {k: profile.get(k) for k in _PROFILE_KEYS if k in profile}
    patch["active_profile"] = profile_id
    save_settings(patch)
    return profile


def active_profile_id() -> str:
    return str(_store().get("active") or "")
