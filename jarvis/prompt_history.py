"""Persist image generation prompts for reuse."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from jarvis.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "prompt_history.json"
MAX_ENTRIES = 200


def _load() -> list[dict[str, Any]]:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _save(entries: list[dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(entries[-MAX_ENTRIES:], indent=2), encoding="utf-8")


def add_entry(
    prompt: str,
    *,
    enhanced: str = "",
    negative: str = "",
    image_path: str = "",
    checkpoint: str = "",
) -> dict[str, Any]:
    prompt = (prompt or "").strip()
    if not prompt:
        return {}
    entries = _load()
    entry = {
        "id": str(uuid.uuid4())[:8],
        "ts": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt[:2000],
        "enhanced": (enhanced or "")[:4000],
        "negative": (negative or "")[:2000],
        "image_path": image_path,
        "checkpoint": checkpoint,
        "favorite": False,
    }
    entries.append(entry)
    _save(entries)
    return entry


def list_entries(*, favorites_only: bool = False, limit: int = 50) -> list[dict[str, Any]]:
    entries = _load()
    if favorites_only:
        entries = [e for e in entries if e.get("favorite")]
    return entries[-limit:][::-1]


def toggle_favorite(entry_id: str) -> dict[str, Any] | None:
    entries = _load()
    for e in entries:
        if e.get("id") == entry_id:
            e["favorite"] = not bool(e.get("favorite"))
            _save(entries)
            return e
    return None


def delete_entry(entry_id: str) -> dict[str, Any] | None:
    """Remove an entry; returns the removed entry so it can be restored (undo)."""
    entries = _load()
    removed = next((e for e in entries if e.get("id") == entry_id), None)
    if removed is None:
        return None
    _save([e for e in entries if e.get("id") != entry_id])
    return removed


def restore_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Re-insert a previously deleted entry (undo), keeping chronological order."""
    prompt = (entry.get("prompt") or "").strip() if isinstance(entry, dict) else ""
    if not prompt:
        return None
    entries = _load()
    if any(e.get("id") == entry.get("id") for e in entries):
        return entry
    entries.append(entry)
    entries.sort(key=lambda e: e.get("ts") or "")
    _save(entries)
    return entry

