"""Mission Control notifications — concise operational alerts (not chat spam)."""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

_MAX = 80
_LOCK = threading.Lock()
_EVENTS: deque[dict[str, Any]] = deque(maxlen=_MAX)
_STORE = PROJECT_ROOT / "data" / "logs" / "platform_notifications.jsonl"


def notify(
    title: str,
    *,
    level: str = "info",
    detail: str = "",
    component: str = "platform",
) -> dict[str, Any]:
    """Record a user-visible platform notification."""
    item = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "title": (title or "")[:120],
        "detail": (detail or "")[:400],
        "level": level,
        "component": component,
    }
    with _LOCK:
        _EVENTS.appendleft(item)
    try:
        _STORE.parent.mkdir(parents=True, exist_ok=True)
        with _STORE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return item


def list_notifications(*, limit: int = 20) -> list[dict[str, Any]]:
    with _LOCK:
        return list(_EVENTS)[:limit]


def load_notifications_from_disk(*, limit: int = 50) -> None:
    if not _STORE.is_file():
        return
    try:
        lines = _STORE.read_text(encoding="utf-8").splitlines()[-limit:]
    except OSError:
        return
    loaded: list[dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            loaded.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    with _LOCK:
        _EVENTS.clear()
        for item in reversed(loaded):
            _EVENTS.append(item)
