"""Workstation activity log — transparent live events for the dashboard."""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

_MAX_EVENTS = 500
_LOCK = threading.Lock()
_EVENTS: deque[dict[str, Any]] = deque(maxlen=_MAX_EVENTS)
_ACTIVITY_FILE = PROJECT_ROOT / "data" / "logs" / "workstation_activity.jsonl"


def record_event(
    event_type: str,
    *,
    component: str = "workstation",
    status: str = "ok",
    detail: str = "",
    duration_ms: float | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a workstation activity event (thread-safe, in-memory + disk)."""
    event = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "type": event_type,
        "component": component,
        "status": status,
        "detail": (detail or "")[:500],
        "duration_ms": round(duration_ms, 1) if duration_ms is not None else None,
        "meta": meta or {},
    }
    with _LOCK:
        _EVENTS.appendleft(event)
    try:
        _ACTIVITY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _ACTIVITY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return event


def list_events(
    *,
    limit: int = 80,
    query: str = "",
    component: str = "",
    event_type: str = "",
    status: str = "",
) -> list[dict[str, Any]]:
    """Return recent events, newest first, with optional filters."""
    q = (query or "").strip().lower()
    comp = (component or "").strip().lower()
    etype = (event_type or "").strip().lower()
    st = (status or "").strip().lower()
    with _LOCK:
        items = list(_EVENTS)
    out: list[dict[str, Any]] = []
    for ev in items:
        if comp and comp not in (ev.get("component") or "").lower():
            continue
        if etype and etype not in (ev.get("type") or "").lower():
            continue
        if st and st != (ev.get("status") or "").lower():
            continue
        if q:
            blob = " ".join(
                str(ev.get(k, "")) for k in ("type", "component", "detail", "status")
            ).lower()
            if q not in blob:
                continue
        out.append(ev)
        if len(out) >= limit:
            break
    return out


def activity_snapshot(*, limit: int = 40) -> dict[str, Any]:
    events = list_events(limit=limit)
    types: dict[str, int] = {}
    for ev in events:
        t = ev.get("type") or "unknown"
        types[t] = types.get(t, 0) + 1
    return {
        "ok": True,
        "count": len(events),
        "types": types,
        "events": events,
    }


def load_recent_from_disk(*, limit: int = 100) -> None:
    """Hydrate in-memory buffer from JSONL on startup."""
    if not _ACTIVITY_FILE.is_file():
        return
    try:
        lines = _ACTIVITY_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    loaded: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            loaded.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    with _LOCK:
        _EVENTS.clear()
        for ev in reversed(loaded):
            _EVENTS.append(ev)
