"""Bookmarks + browsing history (per project)."""

from __future__ import annotations

import json
import time
from typing import Any

from jarvis.config import DATA_DIR

HIST_FILE = DATA_DIR / "browser_product" / "history.json"
BOOK_FILE = DATA_DIR / "browser_product" / "bookmarks.json"
_MAX = 300


def _load(path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows[:_MAX], indent=2), encoding="utf-8")


def record_visit(url: str, *, title: str = "", profile: str = "") -> dict[str, Any]:
    rows = _load(HIST_FILE)
    row = {
        "url": url,
        "title": title or "",
        "profile": profile or "",
        "ts": time.time(),
    }
    rows = [r for r in rows if r.get("url") != url]
    rows.insert(0, row)
    _save(HIST_FILE, rows)
    return row


def list_history(*, query: str = "", profile: str = "", limit: int = 50) -> dict[str, Any]:
    q = (query or "").lower().strip()
    prof = (profile or "").strip()
    rows = []
    for r in _load(HIST_FILE):
        if prof and r.get("profile") != prof:
            continue
        if q and q not in (r.get("url") or "").lower() and q not in (r.get("title") or "").lower():
            continue
        rows.append(r)
    return {"ok": True, "items": rows[:limit], "total": len(rows)}


def add_bookmark(url: str, *, title: str = "", notes: str = "") -> dict[str, Any]:
    rows = _load(BOOK_FILE)
    row = {"url": url, "title": title or url, "notes": notes, "ts": time.time()}
    rows = [r for r in rows if r.get("url") != url]
    rows.insert(0, row)
    _save(BOOK_FILE, rows)
    return {"ok": True, "item": row}


def remove_bookmark(url: str) -> dict[str, Any]:
    rows = _load(BOOK_FILE)
    new = [r for r in rows if r.get("url") != url]
    _save(BOOK_FILE, new)
    return {"ok": True, "removed": len(rows) - len(new)}


def list_bookmarks(*, limit: int = 100) -> dict[str, Any]:
    rows = _load(BOOK_FILE)
    return {"ok": True, "items": rows[:limit]}


NOTES_FILE = DATA_DIR / "browser_product" / "notes.json"


def add_note(text: str, *, url: str = "") -> dict[str, Any]:
    rows = _load(NOTES_FILE)
    row = {"text": (text or "")[:2000], "url": url or "", "ts": time.time()}
    rows.insert(0, row)
    _save(NOTES_FILE, rows)
    return {"ok": True, "item": row}


def list_notes(*, limit: int = 50) -> dict[str, Any]:
    return {"ok": True, "items": _load(NOTES_FILE)[:limit]}
