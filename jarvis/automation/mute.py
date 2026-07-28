"""Automation mute list — per-automation Activity mute."""

from __future__ import annotations

import json
from typing import Any

from jarvis.automation.paths import MUTED_FILE, ensure_dirs


def _load() -> list[str]:
    ensure_dirs()
    if not MUTED_FILE.is_file():
        return []
    try:
        data = json.loads(MUTED_FILE.read_text(encoding="utf-8"))
        return list(data.get("muted") or [])
    except Exception:
        return []


def _save(items: list[str]) -> None:
    ensure_dirs()
    try:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(MUTED_FILE)
    except Exception:
        pass
    MUTED_FILE.write_text(json.dumps({"muted": items}, indent=2), encoding="utf-8")


def list_muted() -> list[str]:
    return _load()


def mute(automation_id: str, muted: bool = True) -> dict[str, Any]:
    aid = str(automation_id or "").strip()
    if not aid:
        return {"ok": False, "error": "id required"}
    items = _load()
    if muted and aid not in items:
        items.append(aid)
    if not muted:
        items = [x for x in items if x != aid]
    _save(items)
    return {"ok": True, "muted": items}


def is_muted(automation_id: str) -> bool:
    return str(automation_id) in _load()
