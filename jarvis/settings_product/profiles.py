"""Preference profiles — named chrome/global snapshots."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.settings_product.appearance import load_appearance, load_global, save_appearance, save_global

PROFILES_FILE = DATA_DIR / "settings_product" / "profiles.json"


def _load() -> dict[str, Any]:
    if not PROFILES_FILE.is_file():
        return {"active": "default", "profiles": {"default": {"id": "default", "name": "Default", "built_in": True}}}
    try:
        raw = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw.setdefault("active", "default")
            raw.setdefault("profiles", {})
            return raw
    except (json.JSONDecodeError, OSError):
        pass
    return {"active": "default", "profiles": {}}


def _save(data: dict[str, Any]) -> dict[str, Any]:
    PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILES_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def list_profiles() -> dict[str, Any]:
    return _load()


def save_profile(name: str, *, profile_id: str = "") -> dict[str, Any]:
    data = _load()
    pid = profile_id or uuid.uuid4().hex[:10]
    data["profiles"][pid] = {
        "id": pid,
        "name": (name or "Profile")[:80],
        "built_in": False,
        "appearance": load_appearance(),
        "global": load_global(),
        "ts": time.time(),
    }
    data["active"] = pid
    _save(data)
    return {"ok": True, "profile": data["profiles"][pid], "active": pid}


def activate_profile(profile_id: str) -> dict[str, Any]:
    data = _load()
    prof = data["profiles"].get(profile_id)
    if not prof:
        return {"ok": False, "error": "profile not found"}
    if prof.get("appearance"):
        save_appearance(prof["appearance"])
    if prof.get("global"):
        save_global(prof["global"])
    data["active"] = profile_id
    _save(data)
    return {"ok": True, "active": profile_id, "profile": prof}


def delete_profile(profile_id: str) -> dict[str, Any]:
    data = _load()
    prof = data["profiles"].get(profile_id)
    if not prof:
        return {"ok": False, "error": "not found"}
    if prof.get("built_in"):
        return {"ok": False, "error": "cannot delete built-in profile"}
    del data["profiles"][profile_id]
    if data.get("active") == profile_id:
        data["active"] = "default"
    _save(data)
    return {"ok": True, "deleted": profile_id}


def export_bundle() -> dict[str, Any]:
    return {
        "ok": True,
        "version": 1,
        "appearance": load_appearance(),
        "global": load_global(),
        "profiles": _load(),
        "exported_at": time.time(),
    }


def import_bundle(body: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(body, dict):
        return {"ok": False, "error": "invalid bundle"}
    if isinstance(body.get("appearance"), dict):
        save_appearance(body["appearance"])
    if isinstance(body.get("global"), dict):
        save_global(body["global"])
    if isinstance(body.get("profiles"), dict):
        _save(body["profiles"])
    return {"ok": True, "imported": True}
