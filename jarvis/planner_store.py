"""SQLite planner — life tasks, calendar events, timers, alarms."""

from __future__ import annotations

import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.feature_flags import planner_enabled

DB_PATH = DATA_DIR / "planner.db"


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                description TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS timers (
                id TEXT PRIMARY KEY,
                label TEXT,
                ends_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alarms (
                id TEXT PRIMARY KEY,
                label TEXT,
                fire_at TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                fired INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """
        )


_init_db()


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _row_task(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "text": row["text"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
    }


def _row_event(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "description": row["description"] or "",
    }


def _row_timer(row: sqlite3.Row, *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now()
    ends = datetime.fromisoformat(row["ends_at"])
    remaining = max(0, int((ends - now).total_seconds()))
    return {
        "id": row["id"],
        "label": row["label"] or "",
        "ends_at": row["ends_at"],
        "remaining_seconds": remaining,
    }


def _row_alarm(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "label": row["label"] or "",
        "fire_at": row["fire_at"],
        "enabled": bool(row["enabled"]),
        "fired": bool(row["fired"]),
    }


def _parse_duration(text: str | None) -> int | None:
    """Return seconds from '10 minutes', '1h', etc."""
    if not text:
        return None
    t = str(text).lower().strip()
    if not t:
        return None
    total = 0
    for num, unit in re.findall(
        r"(\d+)\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes|s|sec|secs|second|seconds)",
        t,
    ):
        n = int(num)
        if unit.startswith("h"):
            total += n * 3600
        elif unit.startswith("m"):
            total += n * 60
        else:
            total += n
    if total:
        return total
    if t.isdigit():
        return int(t) * 60
    return None


def _parse_time_today(text: str | None, *, base: datetime | None = None) -> datetime | None:
    """Parse 7am, 14:30, 3:30 pm for today (or tomorrow if past)."""
    if not text:
        return None
    t = str(text).lower().strip()
    if not t:
        return None
    ref = base or datetime.now()
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", t.replace(".", ""))
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    ampm = m.group(3)
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    elif not ampm and hour <= 12 and ":" not in t:
        hour = hour if hour >= 7 else hour + 12
    dt = ref.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if dt <= datetime.now().replace(second=0, microsecond=0) and not base:
        dt += timedelta(days=1)
    return dt


def add_task(text: str | None) -> dict[str, Any]:
    if not planner_enabled():
        raise ValueError("Planner is disabled (JARVIS_PLANNER=0).")
    text = str(text or "").strip()
    if not text:
        raise ValueError("Task text required")
    tid = uuid.uuid4().hex[:10]
    created = _now_iso()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO tasks (id, text, completed, created_at) VALUES (?, ?, 0, ?)",
            (tid, text, created),
        )
    return {"id": tid, "text": text, "completed": False, "created_at": created}


def list_tasks(*, include_completed: bool = False) -> list[dict[str, Any]]:
    with _conn() as conn:
        if include_completed:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at ASC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE completed = 0 ORDER BY created_at ASC"
            ).fetchall()
    return [_row_task(r) for r in rows]


def complete_task(task_id: str | None) -> bool:
    if not task_id:
        return False
    with _conn() as conn:
        cur = conn.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
        if cur.rowcount > 0:
            return True
        cur = conn.execute(
            "UPDATE tasks SET completed = 1 WHERE text = ? AND completed = 0",
            (task_id,),
        )
        return cur.rowcount > 0


def add_event(
    title: str | None,
    *,
    when: str | None = None,
    time_str: str | None = None,
    duration_min: int = 15,
) -> dict[str, Any]:
    title = str(title or "").strip()
    if not title:
        raise ValueError("Event title required")
    start = datetime.now()
    if when:
        w = when.lower().strip()
        if w == "tomorrow":
            start = start + timedelta(days=1)
        elif re.match(r"\d{4}-\d{2}-\d{2}", w):
            start = datetime.fromisoformat(w)
    if time_str:
        parsed = _parse_time_today(time_str, base=start if when else None)
        if parsed:
            start = parsed
    end = start + timedelta(minutes=max(15, int(duration_min)))
    eid = uuid.uuid4().hex[:10]
    created = _now_iso()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO events (id, title, start_time, end_time, description, created_at) VALUES (?, ?, ?, ?, '', ?)",
            (eid, title, start.isoformat(timespec="seconds"), end.isoformat(timespec="seconds"), created),
        )
    return {
        "id": eid,
        "title": title,
        "start_time": start.isoformat(timespec="seconds"),
        "end_time": end.isoformat(timespec="seconds"),
    }


def events_for_day(day: str | None = None) -> list[dict[str, Any]]:
    day = day or datetime.now().date().isoformat()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE substr(start_time, 1, 10) = ? ORDER BY start_time",
            (day,),
        ).fetchall()
    return [_row_event(r) for r in rows]


def set_timer(duration: str | None, label: str | None = None) -> dict[str, Any]:
    secs = _parse_duration(duration)
    if not secs or secs < 1:
        raise ValueError(f"Could not parse duration: {duration}")
    ends = datetime.now() + timedelta(seconds=secs)
    tid = uuid.uuid4().hex[:10]
    created = _now_iso()
    lbl = (label or str(duration or "")).strip()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO timers (id, label, ends_at, created_at) VALUES (?, ?, ?, ?)",
            (tid, lbl, ends.isoformat(timespec="seconds"), created),
        )
    return {
        "id": tid,
        "label": lbl,
        "ends_at": ends.isoformat(timespec="seconds"),
        "remaining_seconds": secs,
    }


def active_timers() -> list[dict[str, Any]]:
    now = datetime.now()
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM timers ORDER BY ends_at").fetchall()
    out = [_row_timer(r, now=now) for r in rows]
    return [t for t in out if t["remaining_seconds"] > 0]


def clear_expired_timers() -> int:
    now = _now_iso()
    with _conn() as conn:
        cur = conn.execute("DELETE FROM timers WHERE ends_at <= ?", (now,))
        return cur.rowcount


def set_alarm(time_str: str | None, label: str | None = None) -> dict[str, Any]:
    fire = _parse_time_today(time_str)
    if not fire:
        raise ValueError(f"Could not parse alarm time: {time_str}")
    aid = uuid.uuid4().hex[:10]
    created = _now_iso()
    lbl = (label or f"Alarm {time_str}").strip()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO alarms (id, label, fire_at, enabled, fired, created_at) VALUES (?, ?, ?, 1, 0, ?)",
            (aid, lbl, fire.isoformat(timespec="seconds"), created),
        )
    return {"id": aid, "label": lbl, "fire_at": fire.isoformat(timespec="seconds")}


def list_alarms(*, include_fired: bool = False) -> list[dict[str, Any]]:
    with _conn() as conn:
        if include_fired:
            rows = conn.execute(
                "SELECT * FROM alarms WHERE enabled = 1 ORDER BY fire_at"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM alarms WHERE enabled = 1 AND fired = 0 ORDER BY fire_at"
            ).fetchall()
    return [_row_alarm(r) for r in rows]


def tick_alarms_and_timers() -> list[dict[str, str]]:
    """Return notifications for expired timers / due alarms; mark fired."""
    notes: list[dict[str, str]] = []
    with _conn() as conn:
        for row in conn.execute(
            "SELECT * FROM timers WHERE ends_at <= ?", (_now_iso(),)
        ).fetchall():
            label = row["label"] or "timer"
            notes.append({"type": "timer", "message": f"Timer done: {label}"})
            conn.execute("DELETE FROM timers WHERE id = ?", (row["id"],))
        for row in conn.execute(
            "SELECT * FROM alarms WHERE enabled = 1 AND fired = 0 AND fire_at <= ?",
            (_now_iso(),),
        ).fetchall():
            label = row["label"] or "alarm"
            notes.append({"type": "alarm", "message": f"Alarm: {label}"})
            conn.execute("UPDATE alarms SET fired = 1 WHERE id = ?", (row["id"],))
    return notes


def planner_snapshot() -> dict[str, Any]:
    if not planner_enabled():
        return {"enabled": False}
    return {
        "enabled": True,
        "tasks": list_tasks(),
        "events_today": events_for_day(),
        "timers": active_timers(),
        "alarms": list_alarms(),
    }


def format_planner_lines() -> str:
    snap = planner_snapshot()
    if not snap.get("enabled"):
        return ""
    parts: list[str] = []
    tasks = snap.get("tasks") or []
    if tasks:
        parts.append("**Tasks:** " + "; ".join(t["text"] for t in tasks[:8]))
    events = snap.get("events_today") or []
    if events:
        ev_lines = []
        for e in events[:6]:
            t = (e.get("start_time") or "")[11:16]
            ev_lines.append(f"{t} {e.get('title', '')}".strip())
        parts.append("**Today:** " + "; ".join(ev_lines))
    timers = snap.get("timers") or []
    if timers:
        parts.append(f"**Timers:** {len(timers)} active")
    return "\n".join(parts)
