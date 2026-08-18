"""SQLite collaboration store — collaborations, delegated tasks, structured results.

Same conventions as jarvis.missions.store and jarvis.research.store: SQLite
under DATA_DIR, WAL, concurrency-safe initialisation. Execution durability
still comes from the mission system; this store owns collaboration-specific
state (who delegated what to whom, what came back, and what disagreed).
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "collaboration.db"
_init_lock = threading.Lock()

# Collaboration lifecycle, mirroring the mission vocabulary.
PENDING = "pending"
RUNNING = "running"
PAUSED = "paused"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"
BOUNDED = "bounded"  # stopped because a safety limit was reached
TERMINAL_STATES = (COMPLETED, FAILED, CANCELLED, BOUNDED)

# Delegated task outcomes. "partial" and "unresolved" exist so a receiving
# agent can tell what was actually achieved rather than assuming success.
TASK_PENDING = "pending"
TASK_RUNNING = "running"
TASK_SUCCESS = "success"
TASK_PARTIAL = "partial"
TASK_UNRESOLVED = "unresolved"
TASK_FAILED = "failed"
TASK_DENIED = "denied"
TASK_SKIPPED = "skipped"
TASK_TERMINAL = (
    TASK_SUCCESS,
    TASK_PARTIAL,
    TASK_UNRESOLVED,
    TASK_FAILED,
    TASK_DENIED,
    TASK_SKIPPED,
)
TASK_SATISFIED = (TASK_SUCCESS, TASK_PARTIAL)


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=FULL")
    return conn


def _init_db() -> None:
    with _init_lock:
        for attempt in range(3):
            try:
                _init_db_once()
                return
            except sqlite3.OperationalError:
                if attempt == 2:
                    raise
                time.sleep(0.05 * (attempt + 1))


def _init_db_once() -> None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='collaborations'"
        ).fetchone()
        if row:
            return
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS collaborations (
                id TEXT PRIMARY KEY,
                mission_id TEXT,
                objective TEXT NOT NULL,
                initiator TEXT NOT NULL,
                status TEXT NOT NULL,
                bounds TEXT NOT NULL DEFAULT '{}',
                synthesis TEXT,
                reason TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                collaboration_id TEXT NOT NULL,
                requester TEXT NOT NULL,
                target TEXT NOT NULL,
                objective TEXT NOT NULL,
                capability TEXT NOT NULL DEFAULT '',
                action TEXT NOT NULL DEFAULT '',
                params TEXT NOT NULL DEFAULT '{}',
                depends_on TEXT NOT NULL DEFAULT '[]',
                depth INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                result TEXT,
                error TEXT,
                selection TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collaboration_id TEXT NOT NULL,
                description TEXT NOT NULL,
                task_ids TEXT NOT NULL DEFAULT '[]',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collaboration_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_task_collab ON tasks(collaboration_id, status);
            CREATE INDEX IF NOT EXISTS idx_evt_collab ON events(collaboration_id, id);
            """
        )


def _json(value: str | None, default: Any) -> Any:
    try:
        return json.loads(value) if value else default
    except (TypeError, ValueError):
        return default


def record_event(collaboration_id: str, kind: str, detail: str = "") -> None:
    _init_db()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO events (collaboration_id, kind, detail, created_at) VALUES (?,?,?,?)",
            (collaboration_id, kind, detail[:2000], time.time()),
        )


# ------------------------------------------------------------- collaborations


def create(objective: str, initiator: str, *, bounds: dict[str, Any] | None = None) -> str:
    _init_db()
    cid = uuid.uuid4().hex[:12]
    now = time.time()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO collaborations (id, objective, initiator, status, bounds, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?)""",
            (cid, objective[:2000], initiator, PENDING, json.dumps(bounds or {}), now, now),
        )
    record_event(cid, "created", f"{initiator}: {objective[:150]}")
    return cid


def get(collaboration_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM collaborations WHERE id=?", (collaboration_id,)
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["bounds"] = _json(data.get("bounds"), {})
    return data


def list_collaborations(limit: int = 50) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM collaborations ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["bounds"] = _json(d.get("bounds"), {})
        out.append(d)
    return out


def update(collaboration_id: str, **fields: Any) -> None:
    if not fields:
        return
    _init_db()
    fields["updated_at"] = time.time()
    sets = ", ".join(f"{k}=?" for k in fields)
    with _conn() as conn:
        conn.execute(
            f"UPDATE collaborations SET {sets} WHERE id=?", (*fields.values(), collaboration_id)
        )


def set_status(collaboration_id: str, status: str, *, reason: str = "") -> None:
    update(collaboration_id, status=status, reason=reason or None)
    record_event(collaboration_id, f"status:{status}", reason)


def set_mission(collaboration_id: str, mission_id: str) -> None:
    update(collaboration_id, mission_id=mission_id)


def save_synthesis(collaboration_id: str, synthesis: str) -> None:
    update(collaboration_id, synthesis=synthesis, status=COMPLETED)
    record_event(collaboration_id, "synthesis", f"{len(synthesis)} chars")


# ------------------------------------------------------------------- tasks


def add_task(
    collaboration_id: str,
    *,
    requester: str,
    target: str,
    objective: str,
    capability: str = "",
    action: str = "",
    params: dict[str, Any] | None = None,
    depends_on: list[str] | None = None,
    depth: int = 0,
    status: str = TASK_PENDING,
    selection: dict[str, Any] | None = None,
) -> str:
    _init_db()
    tid = uuid.uuid4().hex[:10]
    now = time.time()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO tasks (id, collaboration_id, requester, target, objective, capability,
                                  action, params, depends_on, depth, status, selection, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                tid,
                collaboration_id,
                requester,
                target,
                objective[:2000],
                capability,
                action,
                json.dumps(params or {}),
                json.dumps(depends_on or []),
                depth,
                status,
                json.dumps(selection or {}),
                now,
                now,
            ),
        )
    record_event(collaboration_id, "delegated", f"{requester} -> {target}: {objective[:120]}")
    return tid


def _row_to_task(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["params"] = _json(d.get("params"), {})
    d["depends_on"] = _json(d.get("depends_on"), [])
    d["result"] = _json(d.get("result"), None)
    d["selection"] = _json(d.get("selection"), {})
    return d


def get_task(task_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return _row_to_task(row) if row else None


def tasks(collaboration_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE collaboration_id=? ORDER BY created_at, id",
            (collaboration_id,),
        ).fetchall()
    return [_row_to_task(r) for r in rows]


def set_task_status(
    task_id: str,
    status: str,
    *,
    result: dict[str, Any] | None = None,
    error: str = "",
    bump_attempts: bool = False,
) -> None:
    _init_db()
    with _conn() as conn:
        if bump_attempts:
            conn.execute("UPDATE tasks SET attempts=attempts+1 WHERE id=?", (task_id,))
        conn.execute(
            "UPDATE tasks SET status=?, result=?, error=?, updated_at=? WHERE id=?",
            (
                status,
                json.dumps(result) if result is not None else None,
                error[:2000] or None,
                time.time(),
                task_id,
            ),
        )


# --------------------------------------------------------------- conflicts


def add_conflict(collaboration_id: str, description: str, task_ids: list[str]) -> None:
    _init_db()
    with _conn() as conn:
        existing = conn.execute(
            "SELECT id FROM conflicts WHERE collaboration_id=? AND description=?",
            (collaboration_id, description[:1000]),
        ).fetchone()
        if existing:
            return
        conn.execute(
            "INSERT INTO conflicts (collaboration_id, description, task_ids, created_at) VALUES (?,?,?,?)",
            (collaboration_id, description[:1000], json.dumps(task_ids), time.time()),
        )
    record_event(collaboration_id, "conflict", description[:200])


def conflicts(collaboration_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM conflicts WHERE collaboration_id=? ORDER BY id", (collaboration_id,)
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["task_ids"] = _json(d.get("task_ids"), [])
        out.append(d)
    return out


def history(collaboration_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE collaboration_id=? ORDER BY id", (collaboration_id,)
        ).fetchall()
    return [dict(r) for r in rows]
