"""Fly Tying profiles — reusable bench / search presets."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.flytying_product.settings import save_settings

PROFILES_FILE = DATA_DIR / "flytying_product" / "profiles.json"

BUILTIN: list[dict[str, Any]] = [
    {
        "id": "beginner",
        "name": "Beginner",
        "builtin": True,
        "region": "Northeast US",
        "min_quality": 60,
        "preferred_fly_types": ["dry", "nymph"],
        "favorite_waters": "",
        "preferred_substitutions": True,
        "favorite_hook_types": ["standard dry", "nymph"],
        "chat_model": "",
        "citation_style": "inline",
        "inventory_preferences": {"show_low_stock": True, "suggest_basics": True},
    },
    {
        "id": "competition",
        "name": "Competition",
        "builtin": True,
        "region": "Northeast US",
        "min_quality": 80,
        "preferred_fly_types": ["nymph", "euro"],
        "favorite_waters": "",
        "preferred_substitutions": False,
        "favorite_hook_types": ["competition barbless"],
        "chat_model": "",
        "citation_style": "footnote",
        "inventory_preferences": {"show_low_stock": True, "suggest_basics": False},
    },
    {
        "id": "bass",
        "name": "Bass",
        "builtin": True,
        "region": "Northeast US",
        "min_quality": 50,
        "preferred_fly_types": ["streamer", "popper", "bass"],
        "favorite_waters": "warmwater ponds and rivers",
        "preferred_substitutions": True,
        "favorite_hook_types": ["streamer", "bass bug"],
        "chat_model": "",
        "citation_style": "inline",
        "inventory_preferences": {"show_low_stock": True, "suggest_basics": False},
    },
    {
        "id": "trout",
        "name": "Trout",
        "builtin": True,
        "region": "Northeast US",
        "min_quality": 65,
        "preferred_fly_types": ["dry", "nymph", "emerger", "streamer"],
        "favorite_waters": "coldwater streams",
        "preferred_substitutions": True,
        "favorite_hook_types": ["standard dry", "nymph", "streamer"],
        "chat_model": "",
        "citation_style": "inline",
        "inventory_preferences": {"show_low_stock": True, "suggest_basics": True},
    },
    {
        "id": "saltwater",
        "name": "Saltwater",
        "builtin": True,
        "region": "Northeast US",
        "min_quality": 55,
        "preferred_fly_types": ["saltwater", "streamer", "crab"],
        "favorite_waters": "coastal flats and inlets",
        "preferred_substitutions": True,
        "favorite_hook_types": ["saltwater", "stainless"],
        "chat_model": "",
        "citation_style": "inline",
        "inventory_preferences": {"show_low_stock": True, "suggest_basics": False},
    },
    {
        "id": "travel_kit",
        "name": "Travel Kit",
        "builtin": True,
        "region": "Northeast US",
        "min_quality": 50,
        "preferred_fly_types": ["dry", "nymph", "streamer"],
        "favorite_waters": "",
        "preferred_substitutions": True,
        "favorite_hook_types": ["compact"],
        "chat_model": "",
        "citation_style": "inline",
        "inventory_preferences": {"show_low_stock": True, "suggest_basics": True, "compact": True},
    },
    {
        "id": "minimal_bench",
        "name": "Minimal Bench",
        "builtin": True,
        "region": "Northeast US",
        "min_quality": 40,
        "preferred_fly_types": ["dry", "nymph"],
        "favorite_waters": "",
        "preferred_substitutions": True,
        "favorite_hook_types": ["standard dry"],
        "chat_model": "",
        "citation_style": "none",
        "inventory_preferences": {"show_low_stock": False, "suggest_basics": True, "minimal": True},
    },
]

_PROFILE_KEYS = (
    "region",
    "min_quality",
    "preferred_fly_types",
    "favorite_waters",
    "preferred_substitutions",
    "favorite_hook_types",
    "chat_model",
    "citation_style",
    "inventory_preferences",
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
        "region": body.get("region") or "Northeast US",
        "min_quality": float(body.get("min_quality") or 0),
        "preferred_fly_types": list(body.get("preferred_fly_types") or []),
        "favorite_waters": body.get("favorite_waters") or "",
        "preferred_substitutions": bool(body.get("preferred_substitutions", True)),
        "favorite_hook_types": list(body.get("favorite_hook_types") or []),
        "chat_model": body.get("chat_model") or "",
        "citation_style": body.get("citation_style") or "inline",
        "inventory_preferences": dict(body.get("inventory_preferences") or {}),
        "project_id": body.get("project_id") or "",
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
