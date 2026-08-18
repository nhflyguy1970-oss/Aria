"""SQLite mission store — durable tasks, checkpoints and lifecycle history.

Follows the storage conventions already used by jarvis.planner_store: a SQLite
database under DATA_DIR, created on demand. SQLite rather than a JSON document
because missions outlive the process that started them, may be observed or
cancelled from a different process, and must not lose state to a partial
rewrite of a whole-file payload.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "missions.db"

# Lifecycle states. PENDING/RUNNING/PAUSED are live; the rest are terminal.
PENDING = "pending"
RUNNING = "running"
PAUSED = "paused"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"

STATES = (PENDING, RUNNING, PAUSED, COMPLETED, FAILED, CANCELLED)
LIVE_STATES = (PENDING, RUNNING, PAUSED)
TERMINAL_STATES = (COMPLETED, FAILED, CANCELLED)

# Error classification, mirroring the retryable/terminal split the job queues use.
RETRYABLE = "retryable"
TERMINAL = "terminal"

_ALLOWED: dict[str, tuple[str, ...]] = {
    PENDING: (RUNNING, CANCELLED, FAILED),
    RUNNING: (PAUSED, COMPLETED, FAILED, CANCELLED),
    PAUSED: (RUNNING, CANCELLED, FAILED),
    COMPLETED: (),
    FAILED: (),
    CANCELLED: (),
}


class MissionStateError(RuntimeError):
    """Raised when a caller asks for an illegal lifecycle transition."""


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    # WAL keeps a reader (status query) from blocking the executing process.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    return conn


def _init_db() -> None:
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS missions (
                id TEXT PRIMARY KEY,
                objective TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'generic',
                state TEXT NOT NULL,
                steps TEXT NOT NULL DEFAULT '[]',
                total_steps INTEGER NOT NULL DEFAULT 0,
                completed_steps INTEGER NOT NULL DEFAULT 0,
                result TEXT,
                error TEXT,
                error_kind TEXT,
                cancel_requested INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                started_at REAL,
                finished_at REAL
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                step_index INTEGER NOT NULL,
                payload TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mission_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_ckpt_mission ON checkpoints(mission_id, seq);
            CREATE INDEX IF NOT EXISTS idx_evt_mission ON mission_events(mission_id, id);
            """
        )


def _row_to_mission(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["steps"] = json.loads(data.get("steps") or "[]")
    data["result"] = json.loads(data["result"]) if data.get("result") else None
    data["cancel_requested"] = bool(data.get("cancel_requested"))
    return data


def record_event(mission_id: str, kind: str, detail: str = "") -> None:
    """Append to the mission's lifecycle history. Never overwrites."""
    _init_db()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO mission_events (mission_id, kind, detail, created_at) VALUES (?,?,?,?)",
            (mission_id, kind, detail[:2000], time.time()),
        )


def create(
    objective: str, *, steps: list[dict[str, Any]] | None = None, kind: str = "generic"
) -> str:
    """Create a durable mission and return its id."""
    _init_db()
    mission_id = uuid.uuid4().hex[:12]
    steps = steps or []
    now = time.time()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO missions
               (id, objective, kind, state, steps, total_steps, completed_steps,
                cancel_requested, created_at, updated_at)
               VALUES (?,?,?,?,?,?,0,0,?,?)""",
            (mission_id, objective[:2000], kind, PENDING, json.dumps(steps), len(steps), now, now),
        )
    record_event(mission_id, "created", objective[:200])
    return mission_id


def get(mission_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM missions WHERE id=?", (mission_id,)).fetchone()
    return _row_to_mission(row) if row else None


def list_missions(state: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        if state:
            rows = conn.execute(
                "SELECT * FROM missions WHERE state=? ORDER BY updated_at DESC LIMIT ?",
                (state, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM missions ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
    return [_row_to_mission(r) for r in rows]


def transition(mission_id: str, new_state: str, *, detail: str = "") -> dict[str, Any]:
    """Move a mission to new_state, rejecting illegal transitions."""
    if new_state not in STATES:
        raise MissionStateError(f"Unknown state: {new_state}")
    mission = get(mission_id)
    if not mission:
        raise MissionStateError(f"No such mission: {mission_id}")
    current = mission["state"]
    if current == new_state:
        return mission
    if new_state not in _ALLOWED[current]:
        raise MissionStateError(f"Illegal transition {current} -> {new_state}")

    now = time.time()
    fields = {"state": new_state, "updated_at": now}
    if new_state == RUNNING and not mission.get("started_at"):
        fields["started_at"] = now
    if new_state in TERMINAL_STATES:
        fields["finished_at"] = now
    sets = ", ".join(f"{k}=?" for k in fields)
    with _conn() as conn:
        conn.execute(f"UPDATE missions SET {sets} WHERE id=?", (*fields.values(), mission_id))
    record_event(mission_id, f"state:{new_state}", detail)
    return get(mission_id)  # type: ignore[return-value]


def save_checkpoint(mission_id: str, step_index: int, payload: dict[str, Any] | None = None) -> int:
    """Append a durable checkpoint and return its sequence number.

    Checkpoints are append-only so a mission's progress history survives; the
    engine resumes from the highest sequence number.
    """
    _init_db()
    payload = payload or {}
    with _conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(seq), 0) AS s FROM checkpoints WHERE mission_id=?", (mission_id,)
        ).fetchone()
        seq = int(row["s"]) + 1
        now = time.time()
        conn.execute(
            """INSERT INTO checkpoints (mission_id, seq, step_index, payload, created_at)
               VALUES (?,?,?,?,?)""",
            (mission_id, seq, step_index, json.dumps(payload), now),
        )
        conn.execute(
            "UPDATE missions SET completed_steps=?, updated_at=? WHERE id=?",
            (step_index, now, mission_id),
        )
    record_event(mission_id, "checkpoint", f"step={step_index} seq={seq}")
    return seq


def latest_checkpoint(mission_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM checkpoints WHERE mission_id=? ORDER BY seq DESC LIMIT 1",
            (mission_id,),
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["payload"] = json.loads(data.get("payload") or "{}")
    return data


def checkpoints(mission_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM checkpoints WHERE mission_id=? ORDER BY seq ASC", (mission_id,)
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d.get("payload") or "{}")
        out.append(d)
    return out


def history(mission_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM mission_events WHERE mission_id=? ORDER BY id ASC", (mission_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def request_cancel(mission_id: str) -> bool:
    """Flag a mission for cancellation.

    Persisted rather than signalled in memory, so a mission executing in another
    process observes the request at its next step boundary.
    """
    mission = get(mission_id)
    if not mission or mission["state"] in TERMINAL_STATES:
        return False
    with _conn() as conn:
        conn.execute(
            "UPDATE missions SET cancel_requested=1, updated_at=? WHERE id=?",
            (time.time(), mission_id),
        )
    record_event(mission_id, "cancel_requested")
    if mission["state"] in (PENDING, PAUSED):
        transition(mission_id, CANCELLED, detail="cancelled while not executing")
    return True


def cancel_requested(mission_id: str) -> bool:
    """Re-read the cancellation flag from disk (never from a cached object)."""
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT cancel_requested FROM missions WHERE id=?", (mission_id,)
        ).fetchone()
    return bool(row["cancel_requested"]) if row else False


def record_failure(mission_id: str, error: str, *, kind: str = TERMINAL) -> dict[str, Any]:
    """Persist failure detail, then move to failed (terminal) or paused (retryable)."""
    with _conn() as conn:
        conn.execute(
            "UPDATE missions SET error=?, error_kind=?, updated_at=? WHERE id=?",
            (error[:4000], kind, time.time(), mission_id),
        )
    record_event(mission_id, "error", f"[{kind}] {error[:400]}")
    target = PAUSED if kind == RETRYABLE else FAILED
    return transition(mission_id, target, detail=f"{kind} failure")


def record_result(mission_id: str, result: dict[str, Any]) -> dict[str, Any]:
    with _conn() as conn:
        conn.execute(
            "UPDATE missions SET result=?, updated_at=? WHERE id=?",
            (json.dumps(result), time.time(), mission_id),
        )
    return transition(mission_id, COMPLETED, detail="result recorded")


def interrupted_missions() -> list[dict[str, Any]]:
    """Missions left in RUNNING state — i.e. their executing process died.

    Nothing transitions out of RUNNING without the engine writing a terminal or
    paused state, so a RUNNING row at startup means the process was killed.
    """
    return list_missions(state=RUNNING)


def recover_interrupted() -> list[str]:
    """Make crash-interrupted missions resumable. Returns the ids recovered."""
    recovered = []
    for mission in interrupted_missions():
        mission_id = mission["id"]
        record_event(mission_id, "recovered", "process died while running")
        transition(mission_id, PAUSED, detail="interrupted; recovered for resume")
        recovered.append(mission_id)
    return recovered
