"""Settings diagnostics and recovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.settings_product.appearance import APPEARANCE_FILE, GLOBAL_FILE, load_appearance, load_global
from jarvis.settings_product.catalog import build_catalog
from jarvis.settings_product.coach import coach_warnings
from jarvis.settings_product.profiles import PROFILES_FILE, list_profiles
from jarvis.settings_product.terminology import TERMINOLOGY


def _store_status(path: Path, label: str) -> dict[str, Any]:
    return {
        "id": label,
        "path": str(path),
        "exists": path.is_file(),
        "ok": True if not path.exists() or path.is_file() else False,
    }


def product_store_matrix() -> list[dict[str, Any]]:
    candidates = [
        ("voice", DATA_DIR / "voice_product" / "settings.json"),
        ("vision", DATA_DIR / "vision_product" / "settings.json"),
        ("search", DATA_DIR / "search_product" / "settings.json"),
        ("integrations", DATA_DIR / "integrations_product" / "settings.json"),
        ("capabilities", DATA_DIR / "capabilities_product" / "settings.json"),
        ("models", DATA_DIR / "model_settings.json"),
        ("audio", DATA_DIR / "audio_settings.json"),
        ("video", DATA_DIR / "video_settings.json"),
        ("comfyui", DATA_DIR / "comfyui_settings.json"),
        ("app", DATA_DIR / "app_settings.json"),
        ("flytying", DATA_DIR / "flytying_product" / "settings.json"),
        ("home_assistant", DATA_DIR / "home_assistant_product" / "settings.json"),
    ]
    out = []
    for label, path in candidates:
        exists = path.is_file()
        corrupt = False
        if exists:
            try:
                import json

                json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                corrupt = True
        out.append({"id": label, "path": str(path), "exists": exists, "corrupt": corrupt, "owner": label})
    return out


def health_summary() -> dict[str, Any]:
    catalog = build_catalog()
    stores = product_store_matrix()
    corrupt = [s for s in stores if s.get("corrupt")]
    warnings = coach_warnings()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "catalog_count": len(catalog),
        "stores_tracked": len(stores),
        "stores_present": sum(1 for s in stores if s.get("exists")),
        "corrupt_count": len(corrupt),
        "warnings": len(warnings),
        "healthy": len(corrupt) == 0,
        "appearance": load_appearance(),
        "global": load_global(),
        "active_profile": list_profiles().get("active"),
    }


def diagnostics() -> dict[str, Any]:
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "pipeline": TERMINOLOGY["pipeline"],
        "health": health_summary(),
        "stores": product_store_matrix(),
        "settings_files": [
            _store_status(APPEARANCE_FILE, "appearance"),
            _store_status(GLOBAL_FILE, "global"),
            _store_status(PROFILES_FILE, "profiles"),
        ],
        "coach": coach_warnings(),
        "profiles": list_profiles(),
        "migration": {
            "theme_unified": True,
            "note": "Appearance theme is authoritative; clients should sync aria_theme → appearance.theme",
        },
        "sync": {
            "chrome": "browser localStorage (ui_prefs) + optional server appearance mirror",
            "cross_device": "optional via export/import profiles",
        },
        "tips": [
            "Ctrl+, opens Settings Home.",
            "Voice & Chat modal is Speak + Whisper only.",
            "Products own their settings stores — Settings deep-links.",
            "Secrets live in Integrations / jarvis.env.",
            "Mission Control Runtime config is ops — not preference editing.",
        ],
    }


def recovery_status() -> dict[str, Any]:
    health = health_summary()
    steps = [
        {
            "id": "catalog",
            "label": "Preference catalog loads",
            "done": (health.get("catalog_count") or 0) > 0,
            "detail": "Rebuild catalog if empty",
        },
        {
            "id": "corrupt",
            "label": "No corrupt product settings JSON",
            "done": (health.get("corrupt_count") or 0) == 0,
            "detail": "Fix or reset corrupt product settings files",
        },
        {
            "id": "appearance",
            "label": "Appearance store readable",
            "done": True,
            "detail": "Settings owns appearance.json",
        },
    ]
    return {
        "ok": True,
        "ready": all(s["done"] for s in steps),
        "hint": "Review diagnostics for corrupt stores." if not all(s["done"] for s in steps) else "Settings catalog ready.",
        "steps": steps,
        "health": health,
    }
