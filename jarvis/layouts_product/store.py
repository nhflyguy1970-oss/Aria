"""Layouts persistence — custom layouts, settings, history (no secrets)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.layouts_product.schema import make_snapshot, migrate_snapshot, validate_snapshot

ROOT = Path(DATA_DIR) / "layouts_product"
CUSTOM_FILE = ROOT / "custom.json"
SETTINGS_FILE = ROOT / "settings.json"
HISTORY_FILE = ROOT / "history.json"
UNDO_FILE = ROOT / "undo.json"

DEFAULT_SETTINGS = {
    "restore_on_boot": False,
    "confirm_overwrite": True,
    "confirm_delete": True,
    "show_preview": True,
    "active_layout": "",
    "default_layout": "",
    "density_default": "comfortable",
    "role_default": "default",
}


def _ensure() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)


def _read(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write(path: Path, data: Any) -> None:
    _ensure()
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def load_settings() -> dict[str, Any]:
    data = _read(SETTINGS_FILE, {})
    if not isinstance(data, dict):
        data = {}
    out = dict(DEFAULT_SETTINGS)
    out.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS or k.startswith("experimental_")})
    return out


def save_settings(patch: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_settings()
    if isinstance(patch, dict):
        for k, v in patch.items():
            if k in DEFAULT_SETTINGS or str(k).startswith("experimental_"):
                data[k] = v
    _write(SETTINGS_FILE, data)
    return data


def load_customs() -> dict[str, dict[str, Any]]:
    raw = _read(CUSTOM_FILE, {})
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for k, v in raw.items():
        if isinstance(v, dict):
            out[str(k)] = migrate_snapshot(v)
    return out


def save_customs(customs: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    clean: dict[str, dict[str, Any]] = {}
    for k, v in (customs or {}).items():
        snap = migrate_snapshot(v)
        errs = validate_snapshot(snap)
        if errs:
            continue
        clean[str(k)] = snap
    _write(CUSTOM_FILE, clean)
    return clean


def upsert_custom(layout_id: str, snap: dict[str, Any], *, label: str = "") -> dict[str, Any]:
    lid = (layout_id or "").strip().lower().replace(" ", "-")[:40]
    if not lid:
        raise ValueError("layout id required")
    customs = load_customs()
    entry = make_snapshot(snap, label=label or snap.get("label") or lid, kind="custom")
    entry["id"] = lid
    entry["updated_at"] = time.time()
    errs = validate_snapshot(entry)
    if errs:
        raise ValueError(",".join(errs))
    customs[lid] = entry
    save_customs(customs)
    return entry


def delete_custom(layout_id: str) -> bool:
    customs = load_customs()
    if layout_id not in customs:
        return False
    customs.pop(layout_id, None)
    save_customs(customs)
    settings = load_settings()
    if settings.get("active_layout") == layout_id:
        settings["active_layout"] = ""
        save_settings(settings)
    return True


def load_history(*, limit: int = 40) -> list[dict[str, Any]]:
    raw = _read(HISTORY_FILE, [])
    if not isinstance(raw, list):
        return []
    return raw[-limit:]


def push_history(event: dict[str, Any]) -> None:
    hist = load_history(limit=200)
    entry = {
        "ts": time.time(),
        "action": event.get("action") or "apply",
        "layout_id": event.get("layout_id") or "",
        "label": event.get("label") or "",
        "ok": bool(event.get("ok", True)),
        "detail": event.get("detail") or "",
        "changes": event.get("changes") or [],
    }
    hist.append(entry)
    _write(HISTORY_FILE, hist[-100:])


def load_undo() -> dict[str, Any] | None:
    raw = _read(UNDO_FILE, None)
    return raw if isinstance(raw, dict) else None


def save_undo(payload: dict[str, Any] | None) -> None:
    if payload is None:
        if UNDO_FILE.is_file():
            UNDO_FILE.unlink()
        return
    _write(UNDO_FILE, payload)
