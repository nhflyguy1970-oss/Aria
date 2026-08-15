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
        _migrate_schema(conn)


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """Additive migrations for pause/due/priority/soft-delete without breaking old DBs."""

    def cols(table: str) -> set[str]:
        return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}

    task_cols = cols("tasks")
    if "due_date" not in task_cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
    if "priority" not in task_cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN priority INTEGER DEFAULT 0")
    if "deleted" not in task_cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN deleted INTEGER DEFAULT 0")
    if "source" not in task_cols:
        conn.execute("ALTER TABLE tasks ADD COLUMN source TEXT DEFAULT 'planner'")

    timer_cols = cols("timers")
    if "paused" not in timer_cols:
        conn.execute("ALTER TABLE timers ADD COLUMN paused INTEGER DEFAULT 0")
    if "remaining_sec" not in timer_cols:
        conn.execute("ALTER TABLE timers ADD COLUMN remaining_sec INTEGER")
    if "kind" not in timer_cols:
        conn.execute("ALTER TABLE timers ADD COLUMN kind TEXT DEFAULT 'timer'")

    alarm_cols = cols("alarms")
    if "deleted" not in alarm_cols:
        conn.execute("ALTER TABLE alarms ADD COLUMN deleted INTEGER DEFAULT 0")

    event_cols = cols("events")
    if "deleted" not in event_cols:
        conn.execute("ALTER TABLE events ADD COLUMN deleted INTEGER DEFAULT 0")
    if "recurrence" not in event_cols:
        conn.execute("ALTER TABLE events ADD COLUMN recurrence TEXT")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS planner_undo (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS planner_prefs (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )


_init_db()


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _row_task(row: sqlite3.Row) -> dict[str, Any]:
    keys = set(row.keys())
    return {
        "id": row["id"],
        "text": row["text"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
        "due_date": row["due_date"] if "due_date" in keys else None,
        "priority": int(row["priority"] or 0) if "priority" in keys else 0,
        "source": (row["source"] if "source" in keys else "planner") or "planner",
    }


def _row_event(row: sqlite3.Row) -> dict[str, Any]:
    keys = set(row.keys())
    return {
        "id": row["id"],
        "title": row["title"],
        "start_time": row["start_time"],
        "end_time": row["end_time"],
        "description": row["description"] or "",
        "recurrence": (row["recurrence"] if "recurrence" in keys else None) or "",
    }


def _row_timer(row: sqlite3.Row, *, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now()
    keys = set(row.keys())
    paused = bool(row["paused"]) if "paused" in keys else False
    remaining_sec = row["remaining_sec"] if "remaining_sec" in keys else None
    if paused and remaining_sec is not None:
        remaining = max(0, int(remaining_sec))
        ends_at = row["ends_at"]
    else:
        ends = datetime.fromisoformat(row["ends_at"])
        remaining = max(0, int((ends - now).total_seconds()))
        ends_at = row["ends_at"]
    return {
        "id": row["id"],
        "label": row["label"] or "",
        "ends_at": ends_at,
        "remaining_seconds": remaining,
        "paused": paused,
        "kind": (row["kind"] if "kind" in keys else "timer") or "timer",
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
    from jarvis.production_guard import ProductionIsolationError, assert_owner_write_allowed

    try:
        assert_owner_write_allowed(text, store="planner")
    except ProductionIsolationError as exc:
        raise ValueError(str(exc)) from exc
    tid = uuid.uuid4().hex[:10]
    created = _now_iso()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO tasks (id, text, completed, created_at) VALUES (?, ?, 0, ?)",
            (tid, text, created),
        )
    return {"id": tid, "text": text, "completed": False, "created_at": created}


def list_tasks(*, include_completed: bool = False, include_qa: bool = False) -> list[dict[str, Any]]:
    with _conn() as conn:
        if include_completed:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE COALESCE(deleted, 0) = 0 ORDER BY priority DESC, created_at ASC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE completed = 0 AND COALESCE(deleted, 0) = 0 "
                "ORDER BY priority DESC, created_at ASC"
            ).fetchall()
    out = [_row_task(r) for r in rows]
    if include_qa:
        return out
    from jarvis.integrity_product.tags import looks_like_dev_label

    return [t for t in out if not looks_like_dev_label(str(t.get("text") or ""))]


def purge_qa_planner() -> dict[str, int]:
    """Soft-delete QA/cert planner tasks and events. Returns counts removed."""
    from jarvis.integrity_product.tags import looks_like_dev_label

    tasks_n = events_n = 0
    with _conn() as conn:
        for row in conn.execute("SELECT id, text FROM tasks WHERE COALESCE(deleted, 0) = 0").fetchall():
            if looks_like_dev_label(str(row["text"] or "")):
                conn.execute("UPDATE tasks SET deleted = 1 WHERE id = ?", (row["id"],))
                tasks_n += 1
        for row in conn.execute("SELECT id, title FROM events WHERE COALESCE(deleted, 0) = 0").fetchall():
            if looks_like_dev_label(str(row["title"] or "")):
                conn.execute("UPDATE events SET deleted = 1 WHERE id = ?", (row["id"],))
                events_n += 1
    return {"tasks": tasks_n, "events": events_n}


def complete_task(task_id: str | None) -> bool:
    if not task_id:
        return False
    payload = None
    with _conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            row = conn.execute(
                "SELECT * FROM tasks WHERE text = ? AND completed = 0 LIMIT 1",
                (task_id,),
            ).fetchone()
        if not row:
            return False
        payload = _row_task(row)
        conn.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (row["id"],))
    if payload:
        _push_undo("complete_task", payload)
    return True


def add_event(
    title: str | None,
    *,
    when: str | None = None,
    time_str: str | None = None,
    duration_min: int = 15,
) -> dict[str, Any]:
    from jarvis.modules.automation_event_adapter import automation_calendar_call

    return automation_calendar_call(
        _add_event_impl,
        title,
        when=when,
        time_str=time_str,
        duration_min=duration_min,
    )


def _add_event_impl(
    title: str | None,
    *,
    when: str | None = None,
    time_str: str | None = None,
    duration_min: int = 15,
) -> dict[str, Any]:
    title = str(title or "").strip()
    if not title:
        raise ValueError("Event title required")
    from jarvis.production_guard import ProductionIsolationError, assert_owner_write_allowed

    try:
        assert_owner_write_allowed(title, store="planner")
    except ProductionIsolationError as exc:
        raise ValueError(str(exc)) from exc
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


def events_for_day(day: str | None = None, *, include_qa: bool = False) -> list[dict[str, Any]]:
    day = day or datetime.now().date().isoformat()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE substr(start_time, 1, 10) = ? "
            "AND COALESCE(deleted, 0) = 0 ORDER BY start_time",
            (day,),
        ).fetchall()
    out = [_row_event(r) for r in rows]
    if include_qa:
        return out
    from jarvis.integrity_product.tags import looks_like_dev_label

    return [e for e in out if not looks_like_dev_label(str(e.get("title") or ""))]


def set_timer(duration: str | None, label: str | None = None) -> dict[str, Any]:
    from jarvis.modules.automation_event_adapter import automation_planner_call

    return automation_planner_call("timer", _set_timer_impl, duration, label)


def _set_timer_impl(duration: str | None, label: str | None = None) -> dict[str, Any]:
    secs = _parse_duration(duration)
    if not secs or secs < 1:
        raise ValueError(f"Could not parse duration: {duration}")
    ends = datetime.now() + timedelta(seconds=secs)
    tid = uuid.uuid4().hex[:10]
    created = _now_iso()
    lbl = (label or str(duration or "")).strip()
    kind = "pomodoro" if "pomodoro" in lbl.lower() else "timer"
    with _conn() as conn:
        conn.execute(
            "INSERT INTO timers (id, label, ends_at, created_at, paused, remaining_sec, kind) "
            "VALUES (?, ?, ?, ?, 0, NULL, ?)",
            (tid, lbl, ends.isoformat(timespec="seconds"), created, kind),
        )
    return {
        "id": tid,
        "label": lbl,
        "ends_at": ends.isoformat(timespec="seconds"),
        "remaining_seconds": secs,
        "paused": False,
        "kind": kind,
    }


def active_timers() -> list[dict[str, Any]]:
    now = datetime.now()
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM timers ORDER BY ends_at").fetchall()
    out = []
    for r in rows:
        t = _row_timer(r, now=now)
        if t["paused"] or t["remaining_seconds"] > 0:
            out.append(t)
    return out


def clear_expired_timers() -> int:
    now = _now_iso()
    with _conn() as conn:
        cur = conn.execute(
            "DELETE FROM timers WHERE ends_at <= ? AND COALESCE(paused, 0) = 0",
            (now,),
        )
        return cur.rowcount


def set_alarm(time_str: str | None, label: str | None = None) -> dict[str, Any]:
    from jarvis.modules.automation_event_adapter import automation_planner_call

    return automation_planner_call("alarm", _set_alarm_impl, time_str, label)


def _set_alarm_impl(time_str: str | None, label: str | None = None) -> dict[str, Any]:
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
                "SELECT * FROM alarms WHERE enabled = 1 AND COALESCE(deleted, 0) = 0 ORDER BY fire_at"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM alarms WHERE enabled = 1 AND fired = 0 AND COALESCE(deleted, 0) = 0 "
                "ORDER BY fire_at"
            ).fetchall()
    return [_row_alarm(r) for r in rows]


def tick_alarms_and_timers() -> list[dict[str, str]]:
    from jarvis.modules.automation_event_adapter import automation_reminder_tick

    return automation_reminder_tick(_tick_alarms_and_timers_impl)


def _tick_alarms_and_timers_impl() -> list[dict[str, str]]:
    """Return notifications for expired timers / due alarms; mark fired."""
    notes: list[dict[str, str]] = []
    with _conn() as conn:
        for row in conn.execute(
            "SELECT * FROM timers WHERE ends_at <= ? AND COALESCE(paused, 0) = 0",
            (_now_iso(),),
        ).fetchall():
            label = row["label"] or "timer"
            kind = "pomodoro" if "pomodoro" in (label or "").lower() else "timer"
            notes.append(
                {
                    "type": kind,
                    "id": row["id"],
                    "message": f"Timer done: {label}",
                    "title": "Planner timer",
                }
            )
            conn.execute("DELETE FROM timers WHERE id = ?", (row["id"],))
        for row in conn.execute(
            "SELECT * FROM alarms WHERE enabled = 1 AND fired = 0 AND COALESCE(deleted, 0) = 0 "
            "AND fire_at <= ?",
            (_now_iso(),),
        ).fetchall():
            label = row["label"] or "alarm"
            notes.append(
                {
                    "type": "alarm",
                    "id": row["id"],
                    "message": f"Alarm: {label}",
                    "title": "Planner alarm",
                    "fire_at": row["fire_at"],
                }
            )
            conn.execute("UPDATE alarms SET fired = 1 WHERE id = ?", (row["id"],))
    return notes


def planner_snapshot() -> dict[str, Any]:
    if not planner_enabled():
        return {"enabled": False}
    # Owner snapshot never surfaces test/QA labels. Isolated test DATA_DIR may
    # still create those rows; Integrity scans use list_tasks(include_qa=True).
    return {
        "enabled": True,
        "tasks": list_tasks(include_qa=False),
        "events_today": events_for_day(include_qa=False),
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
        parts.append("**Planner priorities:** " + "; ".join(t["text"] for t in tasks[:8]))
    events = snap.get("events_today") or []
    if events:
        ev_lines = []
        for e in events[:6]:
            t = (e.get("start_time") or "")[11:16]
            ev_lines.append(f"{t} {e.get('title', '')}".strip())
        parts.append("**Planner today:** " + "; ".join(ev_lines))
    timers = snap.get("timers") or []
    if timers:
        tlines = []
        for t in timers[:4]:
            rem = int(t.get("remaining_seconds") or 0)
            m, s = rem // 60, rem % 60
            pause = " (paused)" if t.get("paused") else ""
            tlines.append(f"{t.get('label') or 'timer'} {m}m{s:02d}s{pause}")
        parts.append("**Running timers:** " + "; ".join(tlines))
    alarms = snap.get("alarms") or []
    if alarms:
        alines = []
        for a in alarms[:4]:
            alines.append(f"{(a.get('fire_at') or '')[11:16]} {a.get('label') or 'alarm'}".strip())
        parts.append("**Upcoming alarms:** " + "; ".join(alines))
    return "\n".join(parts)


def load_planner() -> dict[str, Any]:
    """Compatibility snapshot for daily workflows / morning briefing.

    Returns tasks with both ``completed`` and ``done`` keys so callers that
    filter either way keep working.
    """
    snap = planner_snapshot()
    if not snap.get("enabled"):
        return {"tasks": [], "events": [], "timers": [], "alarms": [], "enabled": False}
    tasks = []
    for t in snap.get("tasks") or []:
        row = dict(t)
        row["done"] = bool(row.get("completed"))
        row["title"] = row.get("text") or ""
        tasks.append(row)
    return {
        "enabled": True,
        "tasks": tasks,
        "events": snap.get("events_today") or [],
        "timers": snap.get("timers") or [],
        "alarms": snap.get("alarms") or [],
        "events_today": snap.get("events_today") or [],
    }


def _push_undo(kind: str, payload: dict[str, Any]) -> str:
    uid = uuid.uuid4().hex[:10]
    with _conn() as conn:
        conn.execute(
            "INSERT INTO planner_undo (id, kind, payload, created_at) VALUES (?, ?, ?, ?)",
            (uid, kind, json_dumps(payload), _now_iso()),
        )
        # keep last 30
        rows = conn.execute("SELECT id FROM planner_undo ORDER BY created_at DESC").fetchall()
        for r in rows[30:]:
            conn.execute("DELETE FROM planner_undo WHERE id = ?", (r["id"],))
    return uid


def json_dumps(obj: Any) -> str:
    import json

    return json.dumps(obj, default=str)


def json_loads(text: str) -> Any:
    import json

    return json.loads(text)


def undo_last() -> dict[str, Any]:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM planner_undo ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return {"ok": False, "message": "Nothing to undo"}
        payload = json_loads(row["payload"])
        kind = row["kind"]
        conn.execute("DELETE FROM planner_undo WHERE id = ?", (row["id"],))
        if kind == "delete_task":
            conn.execute(
                "UPDATE tasks SET deleted = 0 WHERE id = ?",
                (payload.get("id"),),
            )
        elif kind == "delete_alarm":
            conn.execute(
                "UPDATE alarms SET deleted = 0, enabled = 1 WHERE id = ?",
                (payload.get("id"),),
            )
        elif kind == "delete_event":
            conn.execute(
                "UPDATE events SET deleted = 0 WHERE id = ?",
                (payload.get("id"),),
            )
        elif kind == "cancel_timer":
            conn.execute(
                "INSERT INTO timers (id, label, ends_at, created_at, paused, remaining_sec, kind) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    payload.get("id"),
                    payload.get("label"),
                    payload.get("ends_at"),
                    payload.get("created_at") or _now_iso(),
                    int(bool(payload.get("paused"))),
                    payload.get("remaining_sec"),
                    payload.get("kind") or "timer",
                ),
            )
        elif kind == "complete_task":
            conn.execute(
                "UPDATE tasks SET completed = 0 WHERE id = ?",
                (payload.get("id"),),
            )
        else:
            return {"ok": False, "message": f"Unknown undo kind: {kind}"}
    return {"ok": True, "kind": kind, "payload": payload}


def update_task(task_id: str, *, text: str | None = None, due_date: str | None = None, priority: int | None = None) -> dict[str, Any]:
    if not task_id:
        raise ValueError("task id required")
    with _conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise ValueError("Task not found")
        new_text = text if text is not None else row["text"]
        new_due = due_date if due_date is not None else (row["due_date"] if "due_date" in row.keys() else None)
        new_pri = priority if priority is not None else (int(row["priority"] or 0) if "priority" in row.keys() else 0)
        conn.execute(
            "UPDATE tasks SET text = ?, due_date = ?, priority = ? WHERE id = ?",
            (str(new_text).strip(), new_due, int(new_pri), task_id),
        )
        updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row_task(updated)


def delete_task(task_id: str, *, soft: bool = True) -> dict[str, Any]:
    payload = None
    with _conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return {"ok": False, "message": "Task not found"}
        payload = _row_task(row)
        if soft:
            conn.execute("UPDATE tasks SET deleted = 1 WHERE id = ?", (task_id,))
        else:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    if soft and payload:
        _push_undo("delete_task", payload)
    return {"ok": True, "task": payload}


def pause_timer(timer_id: str) -> dict[str, Any]:
    now = datetime.now()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM timers WHERE id = ?", (timer_id,)).fetchone()
        if not row:
            raise ValueError("Timer not found")
        if "paused" in row.keys() and row["paused"]:
            return _row_timer(row, now=now)
        ends = datetime.fromisoformat(row["ends_at"])
        remaining = max(0, int((ends - now).total_seconds()))
        conn.execute(
            "UPDATE timers SET paused = 1, remaining_sec = ? WHERE id = ?",
            (remaining, timer_id),
        )
        row = conn.execute("SELECT * FROM timers WHERE id = ?", (timer_id,)).fetchone()
    return _row_timer(row, now=now)


def resume_timer(timer_id: str) -> dict[str, Any]:
    now = datetime.now()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM timers WHERE id = ?", (timer_id,)).fetchone()
        if not row:
            raise ValueError("Timer not found")
        if not (row["paused"] if "paused" in row.keys() else 0):
            return _row_timer(row, now=now)
        remaining = int(row["remaining_sec"] or 0)
        ends = now + timedelta(seconds=max(1, remaining))
        conn.execute(
            "UPDATE timers SET paused = 0, remaining_sec = NULL, ends_at = ? WHERE id = ?",
            (ends.isoformat(timespec="seconds"), timer_id),
        )
        row = conn.execute("SELECT * FROM timers WHERE id = ?", (timer_id,)).fetchone()
    return _row_timer(row, now=now)


def cancel_timer(timer_id: str) -> dict[str, Any]:
    payload = None
    with _conn() as conn:
        row = conn.execute("SELECT * FROM timers WHERE id = ?", (timer_id,)).fetchone()
        if not row:
            return {"ok": False, "message": "Timer not found"}
        payload = dict(_row_timer(row))
        payload["created_at"] = row["created_at"]
        payload["remaining_sec"] = row["remaining_sec"] if "remaining_sec" in row.keys() else None
        payload["ends_at"] = row["ends_at"]
        payload["kind"] = row["kind"] if "kind" in row.keys() else "timer"
        payload["paused"] = bool(row["paused"]) if "paused" in row.keys() else False
        conn.execute("DELETE FROM timers WHERE id = ?", (timer_id,))
    if payload:
        _push_undo("cancel_timer", payload)
    return {"ok": True, "timer": payload}


def update_timer(timer_id: str, *, label: str | None = None, duration: str | None = None) -> dict[str, Any]:
    now = datetime.now()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM timers WHERE id = ?", (timer_id,)).fetchone()
        if not row:
            raise ValueError("Timer not found")
        new_label = label if label is not None else row["label"]
        if duration:
            secs = _parse_duration(duration)
            if not secs:
                raise ValueError(f"Could not parse duration: {duration}")
            ends = now + timedelta(seconds=secs)
            conn.execute(
                "UPDATE timers SET label = ?, ends_at = ?, paused = 0, remaining_sec = NULL WHERE id = ?",
                (new_label, ends.isoformat(timespec="seconds"), timer_id),
            )
        else:
            conn.execute("UPDATE timers SET label = ? WHERE id = ?", (new_label, timer_id))
        row = conn.execute("SELECT * FROM timers WHERE id = ?", (timer_id,)).fetchone()
    return _row_timer(row, now=now)


def duplicate_timer(timer_id: str) -> dict[str, Any]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM timers WHERE id = ?", (timer_id,)).fetchone()
        if not row:
            raise ValueError("Timer not found")
        t = _row_timer(row)
    secs = max(1, int(t.get("remaining_seconds") or 60))
    return set_timer(f"{secs} seconds", label=f"{t.get('label') or 'timer'} (copy)")


def cancel_alarm(alarm_id: str) -> dict[str, Any]:
    payload = None
    with _conn() as conn:
        row = conn.execute("SELECT * FROM alarms WHERE id = ?", (alarm_id,)).fetchone()
        if not row:
            return {"ok": False, "message": "Alarm not found"}
        payload = _row_alarm(row)
        conn.execute("UPDATE alarms SET deleted = 1, enabled = 0 WHERE id = ?", (alarm_id,))
    if payload:
        _push_undo("delete_alarm", payload)
    return {"ok": True, "alarm": payload}


def update_alarm(alarm_id: str, *, time_str: str | None = None, label: str | None = None) -> dict[str, Any]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM alarms WHERE id = ?", (alarm_id,)).fetchone()
        if not row:
            raise ValueError("Alarm not found")
        new_label = label if label is not None else row["label"]
        fire_at = row["fire_at"]
        if time_str:
            fire = _parse_time_today(time_str)
            if not fire:
                raise ValueError(f"Could not parse alarm time: {time_str}")
            fire_at = fire.isoformat(timespec="seconds")
        conn.execute(
            "UPDATE alarms SET label = ?, fire_at = ?, fired = 0, enabled = 1, deleted = 0 WHERE id = ?",
            (new_label, fire_at, alarm_id),
        )
        row = conn.execute("SELECT * FROM alarms WHERE id = ?", (alarm_id,)).fetchone()
    return _row_alarm(row)


def update_event(
    event_id: str,
    *,
    title: str | None = None,
    time_str: str | None = None,
    when: str | None = None,
    duration_min: int | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            raise ValueError("Event not found")
        new_title = title if title is not None else row["title"]
        start = datetime.fromisoformat(row["start_time"])
        end = datetime.fromisoformat(row["end_time"]) if row["end_time"] else start + timedelta(minutes=15)
        if when or time_str:
            base = start
            if when:
                w = when.lower().strip()
                if w == "tomorrow":
                    base = datetime.now() + timedelta(days=1)
                elif re.match(r"\d{4}-\d{2}-\d{2}", w):
                    base = datetime.fromisoformat(w)
            if time_str:
                parsed = _parse_time_today(time_str, base=base)
                if parsed:
                    start = parsed
            dur = duration_min if duration_min is not None else max(15, int((end - start).total_seconds() // 60) or 15)
            end = start + timedelta(minutes=dur)
        elif duration_min is not None:
            end = start + timedelta(minutes=max(15, int(duration_min)))
        desc = description if description is not None else (row["description"] or "")
        conn.execute(
            "UPDATE events SET title = ?, start_time = ?, end_time = ?, description = ? WHERE id = ?",
            (
                new_title,
                start.isoformat(timespec="seconds"),
                end.isoformat(timespec="seconds"),
                desc,
                event_id,
            ),
        )
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return _row_event(row)


def delete_event(event_id: str) -> dict[str, Any]:
    payload = None
    with _conn() as conn:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            return {"ok": False, "message": "Event not found"}
        payload = _row_event(row)
        conn.execute("UPDATE events SET deleted = 1 WHERE id = ?", (event_id,))
    if payload:
        _push_undo("delete_event", payload)
    return {"ok": True, "event": payload}


def get_pref(key: str, default: Any = None) -> Any:
    with _conn() as conn:
        row = conn.execute("SELECT value FROM planner_prefs WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json_loads(row["value"])
    except Exception:
        return row["value"]


def set_pref(key: str, value: Any) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO planner_prefs (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, json_dumps(value)),
        )


def recently_completed_tasks(*, limit: int = 8) -> list[dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE completed = 1 AND COALESCE(deleted, 0) = 0 "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_task(r) for r in rows]
