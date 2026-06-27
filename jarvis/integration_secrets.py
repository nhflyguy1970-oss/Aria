"""Integration API keys — saved from the GUI into data/jarvis.env (same as HA token)."""

from __future__ import annotations

import os
import re
from typing import Any

_SECRET_FIELDS: dict[str, str] = {
    "gemini_api_key": "GEMINI_API_KEY",
    "google_api_key": "GOOGLE_API_KEY",
    "openai_api_key": "OPENAI_API_KEY",
    "hf_token": "HF_TOKEN",
    "meshy_api_key": "JARVIS_MESHY_API_KEY",
}


def _mask(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    return "••••••••"


def _env_value(name: str) -> str:
    return (os.getenv(name) or "").strip()


def secrets_status() -> dict[str, Any]:
    """Which integration keys are set (masked previews only)."""
    gemini = _env_value("GEMINI_API_KEY") or _env_value("GOOGLE_API_KEY")
    openai = _env_value("OPENAI_API_KEY")
    hf = _env_value("HF_TOKEN") or _env_value("HUGGING_FACE_HUB_TOKEN")
    meshy = _env_value("JARVIS_MESHY_API_KEY")
    return {
        "gemini_api_key_set": bool(gemini),
        "gemini_api_key_preview": _mask(gemini),
        "openai_api_key_set": bool(openai),
        "openai_api_key_preview": _mask(openai),
        "hf_token_set": bool(hf),
        "hf_token_preview": _mask(hf),
        "meshy_api_key_set": bool(meshy),
        "meshy_api_key_preview": _mask(meshy),
        "storage": "data/jarvis.env",
        "hint": "Keys are saved on this PC only (not synced to git). Restart not required.",
    }


def save_secrets(patch: dict[str, Any]) -> dict[str, Any]:
    """Persist non-empty keys from the settings UI."""
    from jarvis.env_loader import load_jarvis_env, upsert_env_vars

    updates: dict[str, str] = {}
    for field, env_name in _SECRET_FIELDS.items():
        if field not in patch:
            continue
        raw = patch.get(field)
        if raw is None:
            continue
        value = str(raw).strip()
        if not value:
            continue
        if field == "hf_token" and not value.startswith("hf_"):
            value = f"hf_{value}" if not value.startswith("hf") else value
        updates[env_name] = value

    if "gemini_api_key" in patch and str(patch.get("gemini_api_key") or "").strip():
        updates.pop("GOOGLE_API_KEY", None)

    changed = upsert_env_vars(updates) if updates else []
    load_jarvis_env(force=True)

    if updates.get("GEMINI_API_KEY") or updates.get("OPENAI_API_KEY"):
        explicit = os.getenv("JARVIS_CLOUD_LIVE_VOICE", "").strip().lower()
        if explicit not in ("0", "false", "no", "off"):
            upsert_env_vars({"JARVIS_CLOUD_LIVE_VOICE": "1"})
            load_jarvis_env(force=True)
            changed = list(set(changed + ["JARVIS_CLOUD_LIVE_VOICE"]))

    out = secrets_status()
    out["ok"] = True
    out["changed"] = changed
    return out


def clear_secret(field: str) -> dict[str, Any]:
    """Remove a key from jarvis.env (empty string in UI)."""
    env_name = _SECRET_FIELDS.get(field)
    if not env_name:
        return {"ok": False, "message": f"Unknown field: {field}"}
    from jarvis.env_loader import ENV_FILE, load_jarvis_env

    if not ENV_FILE.is_file():
        return {"ok": True, **secrets_status()}
    text = ENV_FILE.read_text(encoding="utf-8")
    pattern = re.compile(rf"^export\s+{re.escape(env_name)}=.*$\n?", re.MULTILINE)
    new_text = pattern.sub("", text)
    if new_text != text:
        ENV_FILE.write_text(new_text, encoding="utf-8")
    os.environ.pop(env_name, None)
    load_jarvis_env(force=True)
    return {"ok": True, **secrets_status()}
