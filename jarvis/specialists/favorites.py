"""Favorites and frequently used specialist teams."""

from __future__ import annotations

import json
import threading
import time
from typing import Any

from jarvis.config import DATA_DIR

_FILE = DATA_DIR / "specialists" / "favorites.json"
_lock = threading.Lock()


def _load() -> dict[str, Any]:
    if not _FILE.is_file():
        return {"favorites": [], "recent": [], "stats": {}}
    try:
        return json.loads(_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"favorites": [], "recent": [], "stats": {}}


def _save(data: dict[str, Any]) -> None:
    _FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(_FILE)
    except Exception:
        pass
    _FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_favorites() -> list[dict[str, Any]]:
    with _lock:
        return list(_load().get("favorites") or [])


def save_favorite(name: str, team: list[str]) -> dict[str, Any]:
    with _lock:
        data = _load()
        favs = [f for f in (data.get("favorites") or []) if f.get("name") != name]
        entry = {"name": name, "team": team, "saved_at": time.time()}
        favs.append(entry)
        data["favorites"] = favs[-30:]
        _save(data)
    return {"ok": True, "favorite": entry}


def record_team_usage(team: list[str]) -> None:
    key = ",".join(team)
    with _lock:
        data = _load()
        stats = data.get("stats") or {}
        entry = stats.get(key) or {"team": team, "count": 0}
        entry["count"] = int(entry.get("count") or 0) + 1
        entry["last_used"] = time.time()
        stats[key] = entry
        data["stats"] = stats
        recent = data.get("recent") or []
        recent = [r for r in recent if r.get("key") != key]
        recent.insert(0, {"key": key, "team": team, "ts": time.time()})
        data["recent"] = recent[:20]
        _save(data)


def frequent_teams(limit: int = 8) -> list[dict[str, Any]]:
    with _lock:
        stats = list((_load().get("stats") or {}).values())
    stats.sort(key=lambda x: int(x.get("count") or 0), reverse=True)
    return stats[:limit]


def recent_teams(limit: int = 8) -> list[dict[str, Any]]:
    with _lock:
        return list(_load().get("recent") or [])[:limit]
