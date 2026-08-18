"""Persistent coding-task state — phases, iterations, tests, edits, commits.

Same conventions as the other ARIA stores: SQLite under DATA_DIR, WAL,
concurrency-safe init. Execution durability still comes from the mission
system; this owns coding-specific state so a task can be resumed truthfully
after a crash rather than restarted blind.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "coding_agent.db"
_init_lock = threading.Lock()

# Lifecycle phases.
PENDING = "pending"
PLANNING = "planning"
INSPECTING = "inspecting"
IMPLEMENTING = "implementing"
TESTING = "testing"
DIAGNOSING = "diagnosing"
FIXING = "fixing"
REVIEWING = "reviewing"
COMPLETED = "completed"
FAILED = "failed"
PAUSED = "paused"
CANCELLED = "cancelled"
BOUNDED = "bounded"

PHASES = (
    PENDING,
    PLANNING,
    INSPECTING,
    IMPLEMENTING,
    TESTING,
    DIAGNOSING,
    FIXING,
    REVIEWING,
    COMPLETED,
    FAILED,
    PAUSED,
    CANCELLED,
    BOUNDED,
)
TERMINAL = (COMPLETED, FAILED, CANCELLED, BOUNDED)

_ALLOWED: dict[str, tuple[str, ...]] = {
    PENDING: (PLANNING, INSPECTING, IMPLEMENTING, CANCELLED, FAILED),
    PLANNING: (INSPECTING, IMPLEMENTING, PAUSED, CANCELLED, FAILED, BOUNDED),
    INSPECTING: (IMPLEMENTING, PLANNING, PAUSED, CANCELLED, FAILED, BOUNDED),
    IMPLEMENTING: (TESTING, PAUSED, CANCELLED, FAILED, BOUNDED),
    TESTING: (DIAGNOSING, REVIEWING, PAUSED, CANCELLED, FAILED, BOUNDED),
    DIAGNOSING: (IMPLEMENTING, FIXING, REVIEWING, PAUSED, CANCELLED, FAILED, BOUNDED),
    FIXING: (IMPLEMENTING, TESTING, PAUSED, CANCELLED, FAILED, BOUNDED),
    REVIEWING: (COMPLETED, DIAGNOSING, FIXING, PAUSED, CANCELLED, FAILED, BOUNDED),
    PAUSED: (
        PENDING,
        PLANNING,
        INSPECTING,
        IMPLEMENTING,
        TESTING,
        DIAGNOSING,
        FIXING,
        REVIEWING,
        CANCELLED,
        FAILED,
    ),
    COMPLETED: (),
    FAILED: (),
    CANCELLED: (),
    BOUNDED: (),
}

BOUNDS = {
    "max_iterations": 6,
    "max_test_runs": 12,
    "max_files_changed": 40,
    "max_commands": 200,
    "max_runtime_s": 1800,
}


class CodingTaskError(RuntimeError):
    """Invalid coding-task operation or transition."""


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
                _init_once()
                return
            except sqlite3.OperationalError:
                if attempt == 2:
                    raise
                time.sleep(0.05 * (attempt + 1))


def _init_once() -> None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='coding_tasks_v2'"
        ).fetchone()
        if row:
            return
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS coding_tasks_v2 (
                id TEXT PRIMARY KEY,
                mission_id TEXT,
                workspace TEXT NOT NULL,
                objective TEXT NOT NULL,
                phase TEXT NOT NULL,
                plan TEXT NOT NULL DEFAULT '[]',
                iterations INTEGER NOT NULL DEFAULT 0,
                test_runs INTEGER NOT NULL DEFAULT 0,
                commands INTEGER NOT NULL DEFAULT 0,
                files_changed TEXT NOT NULL DEFAULT '[]',
                baseline_dirty TEXT NOT NULL DEFAULT '[]',
                baseline_failures TEXT NOT NULL DEFAULT '[]',
                last_test TEXT,
                branch TEXT NOT NULL DEFAULT '',
                head_commit TEXT NOT NULL DEFAULT '',
                commit_sha TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                result TEXT,
                error TEXT,
                stop_reason TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS coding_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                phase TEXT NOT NULL DEFAULT '',
                kind TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS coding_locks (
                workspace TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                acquired_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cev_task ON coding_events(task_id, id);
            """
        )


def _json(v, default):
    try:
        return json.loads(v) if v else default
    except (TypeError, ValueError):
        return default


def record_event(task_id: str, kind: str, detail: str = "", phase: str = "") -> None:
    _init_db()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO coding_events (task_id, phase, kind, detail, created_at) VALUES (?,?,?,?,?)",
            (task_id, phase, kind, detail[:2000], time.time()),
        )


def create(objective: str, workspace: str, *, mission_id: str = "", model: str = "") -> str:
    _init_db()
    tid = f"cod_{uuid.uuid4().hex[:10]}"
    now = time.time()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO coding_tasks_v2
               (id, mission_id, workspace, objective, phase, model, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (tid, mission_id, workspace, objective[:2000], PENDING, model, now, now),
        )
    record_event(tid, "created", objective[:200], PENDING)
    return tid


def get(task_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM coding_tasks_v2 WHERE id=?", (task_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    for f, default in (
        ("plan", []),
        ("files_changed", []),
        ("baseline_dirty", []),
        ("baseline_failures", []),
        ("last_test", None),
        ("result", None),
    ):
        d[f] = _json(d.get(f), default)
    return d


def list_tasks(limit: int = 50) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM coding_tasks_v2 ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [get(r["id"]) for r in rows]  # type: ignore[misc]


def update(task_id: str, **fields: Any) -> None:
    if not fields:
        return
    _init_db()
    encoded = {}
    for k, v in fields.items():
        encoded[k] = json.dumps(v) if isinstance(v, (list, dict)) else v
    encoded["updated_at"] = time.time()
    sets = ", ".join(f"{k}=?" for k in encoded)
    with _conn() as conn:
        conn.execute(f"UPDATE coding_tasks_v2 SET {sets} WHERE id=?", (*encoded.values(), task_id))


def set_phase(task_id: str, phase: str, *, detail: str = "") -> dict[str, Any]:
    if phase not in PHASES:
        raise CodingTaskError(f"Unknown phase: {phase}")
    task = get(task_id)
    if not task:
        raise CodingTaskError(f"No such coding task: {task_id}")
    current = task["phase"]
    if current == phase:
        return task
    if phase not in _ALLOWED[current]:
        raise CodingTaskError(f"Illegal phase transition {current} -> {phase}")
    update(task_id, phase=phase)
    record_event(task_id, f"phase:{phase}", detail, phase)
    return get(task_id)  # type: ignore[return-value]


def bump(task_id: str, field: str, by: int = 1) -> None:
    _init_db()
    with _conn() as conn:
        conn.execute(
            f"UPDATE coding_tasks_v2 SET {field}={field}+?, updated_at=? WHERE id=?",
            (by, time.time(), task_id),
        )


def add_changed_file(task_id: str, path: str) -> None:
    task = get(task_id)
    if not task:
        return
    files = task["files_changed"]
    if path not in files:
        files.append(path)
        update(task_id, files_changed=files)


def events(task_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM coding_events WHERE task_id=? ORDER BY id", (task_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ------------------------------------------------------------------- locking


def acquire_lock(workspace: str, task_id: str) -> bool:
    """One active coding task per workspace, so two tasks cannot overwrite each other."""
    _init_db()
    with _conn() as conn:
        existing = conn.execute(
            "SELECT task_id FROM coding_locks WHERE workspace=?", (workspace,)
        ).fetchone()
        if existing:
            holder = get(str(existing["task_id"]))
            if holder and holder["phase"] not in TERMINAL:
                return str(existing["task_id"]) == task_id
            conn.execute("DELETE FROM coding_locks WHERE workspace=?", (workspace,))
        conn.execute(
            "INSERT INTO coding_locks (workspace, task_id, acquired_at) VALUES (?,?,?)",
            (workspace, task_id, time.time()),
        )
    return True


def lock_holder(workspace: str) -> str:
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT task_id FROM coding_locks WHERE workspace=?", (workspace,)
        ).fetchone()
    return str(row["task_id"]) if row else ""


def release_lock(workspace: str, task_id: str) -> bool:
    _init_db()
    with _conn() as conn:
        cur = conn.execute(
            "DELETE FROM coding_locks WHERE workspace=? AND task_id=?", (workspace, task_id)
        )
        return cur.rowcount > 0


def interrupted_tasks() -> list[dict[str, Any]]:
    """Tasks left in a working phase — their process died."""
    working = (PLANNING, INSPECTING, IMPLEMENTING, TESTING, DIAGNOSING, FIXING, REVIEWING)
    return [t for t in list_tasks(limit=200) if t["phase"] in working]


def recover_interrupted() -> list[str]:
    """Move crash-interrupted tasks to a safe, resumable state."""
    out = []
    for task in interrupted_tasks():
        record_event(task["id"], "recovered", f"interrupted during {task['phase']}", task["phase"])
        update(task["id"], phase=PAUSED, stop_reason="recovered after interruption")
        out.append(task["id"])
    return out
