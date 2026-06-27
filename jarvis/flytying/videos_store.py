"""Persist custom fly-tying videos and article embed cache."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from jarvis.config import DATA_DIR

CUSTOM_VIDEOS_FILE = DATA_DIR / "flytying_custom_videos.json"
VIDEO_CACHE_FILE = DATA_DIR / "flytying_video_cache.json"


def _read_json(path, default):
    if not path.is_file():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, (dict, list)):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return default


def _write_json(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _youtube_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{6,})", url)
    return m.group(1) if m else ""


def list_custom_videos() -> list[dict[str, Any]]:
    rows = _read_json(CUSTOM_VIDEOS_FILE, [])
    return rows if isinstance(rows, list) else []


def get_cached_videos(source_url: str) -> list[dict[str, Any]]:
    """Article embed cache keyed by source URL."""
    url = (source_url or "").strip()
    if not url:
        return []
    cache = _read_json(VIDEO_CACHE_FILE, {})
    if not isinstance(cache, dict):
        return []
    rows = cache.get(url) or cache.get(url.rstrip("/")) or []
    return rows if isinstance(rows, list) else []


def remove_custom_video(key: str) -> list[dict[str, Any]]:
    needle = (key or "").strip()
    rows = [r for r in list_custom_videos() if str(r.get("video_id") or r.get("url") or "") != needle]
    _write_json(CUSTOM_VIDEOS_FILE, rows)
    return rows


def add_custom_video(url: str | None, *, title: str = "") -> list[dict[str, Any]]:
    url = str(url or "").strip()
    if not url:
        raise ValueError("url required")
    video_id = _youtube_id(url)
    rows = list_custom_videos()
    row = {
        "provider": "youtube",
        "url": url,
        "video_id": video_id,
        "title": title or url,
        "added_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    rows.insert(0, row)
    _write_json(CUSTOM_VIDEOS_FILE, rows)
    return rows
