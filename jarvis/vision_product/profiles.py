"""Vision profiles — reusable analysis presets."""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.vision_product.settings import save_settings

PROFILES_FILE = DATA_DIR / "vision_product" / "profiles.json"

BUILTIN: list[dict[str, Any]] = [
    {
        "id": "document_ocr",
        "name": "Document OCR",
        "builtin": True,
        "quality_mode": "quality",
        "ocr_mode": "hybrid",
        "confidence_threshold": 0.6,
        "compare_auto": False,
        "output_style": "detailed",
        "auto_enhancement": False,
        "region_default": "",
    },
    {
        "id": "research",
        "name": "Research",
        "builtin": True,
        "quality_mode": "quality",
        "ocr_mode": "vlm",
        "confidence_threshold": 0.55,
        "compare_auto": True,
        "output_style": "detailed",
        "auto_enhancement": False,
        "region_default": "",
    },
    {
        "id": "accessibility",
        "name": "Accessibility",
        "builtin": True,
        "quality_mode": "quality",
        "ocr_mode": "hybrid",
        "confidence_threshold": 0.5,
        "compare_auto": False,
        "output_style": "detailed",
        "auto_enhancement": True,
        "region_default": "",
    },
    {
        "id": "coding",
        "name": "Coding",
        "builtin": True,
        "quality_mode": "quality",
        "ocr_mode": "vlm",
        "confidence_threshold": 0.55,
        "compare_auto": False,
        "output_style": "balanced",
        "auto_enhancement": False,
        "region_default": "",
    },
    {
        "id": "ui_review",
        "name": "UI Review",
        "builtin": True,
        "quality_mode": "quality",
        "ocr_mode": "vlm",
        "confidence_threshold": 0.55,
        "compare_auto": True,
        "output_style": "detailed",
        "auto_enhancement": False,
        "region_default": "",
    },
    {
        "id": "fast_scan",
        "name": "Fast Scan",
        "builtin": True,
        "quality_mode": "fast",
        "ocr_mode": "auto",
        "confidence_threshold": 0.45,
        "compare_auto": True,
        "output_style": "brief",
        "auto_enhancement": False,
        "region_default": "",
    },
    {
        "id": "deep_analysis",
        "name": "Deep Analysis",
        "builtin": True,
        "quality_mode": "quality",
        "ocr_mode": "vlm",
        "confidence_threshold": 0.65,
        "compare_auto": True,
        "output_style": "detailed",
        "auto_enhancement": False,
        "region_default": "",
    },
    {
        "id": "naturalist",
        "name": "Naturalist",
        "builtin": True,
        "quality_mode": "quality",
        "ocr_mode": "vlm",
        "confidence_threshold": 0.5,
        "compare_auto": False,
        "output_style": "detailed",
        "auto_enhancement": False,
        "region_default": "",
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
    for p in list_profiles():
        if p.get("id") == profile_id:
            return deepcopy(p)
    return None


def create_profile(body: dict[str, Any]) -> dict[str, Any]:
    store = _store()
    profile = {
        "id": str(body.get("id") or uuid.uuid4().hex[:12]),
        "name": str(body.get("name") or "Custom").strip() or "Custom",
        "builtin": False,
        "quality_mode": body.get("quality_mode") or "fast",
        "ocr_mode": body.get("ocr_mode") or "auto",
        "confidence_threshold": float(body.get("confidence_threshold") or 0.55),
        "compare_auto": bool(body.get("compare_auto", True)),
        "output_style": body.get("output_style") or "balanced",
        "auto_enhancement": bool(body.get("auto_enhancement")),
        "region_default": body.get("region_default") or "",
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
    save_settings(
        {
            "active_profile": profile_id,
            "quality_mode": profile.get("quality_mode") or "fast",
            "ocr_mode": profile.get("ocr_mode") or "auto",
            "confidence_threshold": profile.get("confidence_threshold") or 0.55,
            "compare_auto": bool(profile.get("compare_auto", True)),
            "output_style": profile.get("output_style") or "balanced",
            "auto_enhancement": bool(profile.get("auto_enhancement")),
            "region_default": profile.get("region_default") or "",
        }
    )
    return profile


def active_profile_id() -> str:
    return str(_store().get("active") or "")
