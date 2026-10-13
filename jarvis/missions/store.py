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
import threading
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "missions.db"

# Serialises schema creation between the background worker and request threads.
_init_lock = threading.Lock()

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
    PENDING: (RUNNING, PAUSED, CANCELLED, FAILED),  # a queued mission may be paused before it starts
    RUNNING: (PAUSED, COMPLETED, FAILED, CANCELLED),
    PAUSED: (PENDING, RUNNING, CANCELLED, FAILED),
    COMPLETED: (),
    FAILED: (),
    CANCELLED: (),
}


class MissionStateError(RuntimeError):
    """Raised when a caller asks for an illegal lifecycle transition."""


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Wait rather than fail when the background worker holds a write lock.
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=FULL")
    return conn


def _init_db() -> None:
    """Create or migrate the schema, tolerating concurrent initialisation.

    The background worker and a request thread can reach this simultaneously on
    a fresh database; setting journal_mode needs an exclusive lock, so a losing
    racer must retry rather than fail the caller.
    """
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
        # Cheap fast path: the schema is created once, but the file can be
        # removed between test cases, so this is checked rather than cached.
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='missions'"
        ).fetchone()
        if row:
            # Existing database: only ensure Milestone 1 schemas gain the retry
            # columns. Cheap enough to check on every call.
            existing = {r["name"] for r in conn.execute("PRAGMA table_info(missions)")}
            if "attempts" not in existing:
                conn.execute("ALTER TABLE missions ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0")
            if "next_attempt_at" not in existing:
                conn.execute("ALTER TABLE missions ADD COLUMN next_attempt_at REAL")
            if "pause_requested" not in existing:
                conn.execute("ALTER TABLE missions ADD COLUMN pause_requested INTEGER NOT NULL DEFAULT 0")
            conn.execute("""CREATE TABLE IF NOT EXISTS mission_operations (
                operation_id TEXT PRIMARY KEY, mission_id TEXT NOT NULL,
                step_index INTEGER NOT NULL, state TEXT NOT NULL, result TEXT,
                started_at REAL NOT NULL, finished_at REAL,
                UNIQUE(mission_id, step_index))""")
            conn.execute("""CREATE TABLE IF NOT EXISTS agent_task_plans (
                mission_id TEXT PRIMARY KEY, project TEXT NOT NULL, session_ref TEXT NOT NULL,
                plan_hash TEXT NOT NULL, approval_state TEXT NOT NULL,
                approval_expires_at REAL NOT NULL, approved_at REAL,
                scheduled_at REAL, created_at REAL NOT NULL, updated_at REAL NOT NULL)""")
            columns = {r["name"] for r in conn.execute("PRAGMA table_info(agent_task_plans)")}
            if "scheduled_at" not in columns:
                conn.execute("ALTER TABLE agent_task_plans ADD COLUMN scheduled_at REAL")
            return
        # WAL lets a status reader run while the worker writes. Setting it takes
        # an exclusive lock, so it happens only at creation, never per connection —
        # and losing the race to another initialiser is harmless.
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
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
                pause_requested INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                started_at REAL,
                finished_at REAL,
                attempts INTEGER NOT NULL DEFAULT 0,
                next_attempt_at REAL
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
            CREATE INDEX IF NOT EXISTS idx_missions_queue ON missions(state, created_at);
            CREATE TABLE IF NOT EXISTS mission_operations (
                operation_id TEXT PRIMARY KEY, mission_id TEXT NOT NULL,
                step_index INTEGER NOT NULL, state TEXT NOT NULL, result TEXT,
                started_at REAL NOT NULL, finished_at REAL,
                UNIQUE(mission_id, step_index));
            CREATE TABLE IF NOT EXISTS agent_task_plans (
                mission_id TEXT PRIMARY KEY, project TEXT NOT NULL, session_ref TEXT NOT NULL,
                plan_hash TEXT NOT NULL, approval_state TEXT NOT NULL,
                approval_expires_at REAL NOT NULL, approved_at REAL,
                scheduled_at REAL, created_at REAL NOT NULL, updated_at REAL NOT NULL);
            """
        )


def _row_to_mission(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["steps"] = json.loads(data.get("steps") or "[]")
    data["result"] = json.loads(data["result"]) if data.get("result") else None
    data["cancel_requested"] = bool(data.get("cancel_requested"))
    data["pause_requested"] = bool(data.get("pause_requested"))
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
    objective: str, *, steps: list[dict[str, Any]] | None = None, kind: str = "generic",
    initial_state: str = PENDING,
) -> str:
    """Create a durable mission and return its id."""
    _init_db()
    if initial_state not in (PENDING, PAUSED):
        raise MissionStateError("new missions must be pending or paused")
    mission_id = uuid.uuid4().hex[:12]
    steps = steps or []
    now = time.time()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO missions
               (id, objective, kind, state, steps, total_steps, completed_steps,
                cancel_requested, created_at, updated_at)
               VALUES (?,?,?,?,?,?,0,0,?,?)""",
            (mission_id, objective[:2000], kind, initial_state, json.dumps(steps), len(steps), now, now),
        )
    record_event(mission_id, "created", objective[:200])
    return mission_id


def set_steps(mission_id: str, steps: list[dict[str, Any]]) -> None:
    """Replace a mission's steps.

    Needed because a step sometimes has to carry the id of the mission that
    owns it, which only exists once the mission has been created.
    """
    _init_db()
    with _conn() as conn:
        conn.execute(
            "UPDATE missions SET steps=?, total_steps=?, updated_at=? WHERE id=?",
            (json.dumps(steps), len(steps), time.time(), mission_id),
        )


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
        changed = conn.execute(f"UPDATE missions SET {sets} WHERE id=? AND state=?",
                               (*fields.values(), mission_id, current)).rowcount
        if changed != 1:
            raise MissionStateError("mission state changed concurrently")
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


def operation_id(mission_id: str, step_index: int) -> str:
    return f"mission:{mission_id}:step:{step_index}"


def operation(mission_id: str, step_index: int) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM mission_operations WHERE mission_id=? AND step_index=?",
                           (mission_id, step_index)).fetchone()
    if not row:
        return None
    data = dict(row)
    data["result"] = json.loads(data["result"]) if data["result"] else None
    return data


def begin_operation(mission_id: str, step_index: int) -> dict[str, Any]:
    """Persist intent before dispatch; an existing claim must never be dispatched again."""
    _init_db()
    with _conn() as conn:
        created = conn.execute("""INSERT OR IGNORE INTO mission_operations
            (operation_id,mission_id,step_index,state,started_at) VALUES (?,?,?,?,?)""",
            (operation_id(mission_id, step_index), mission_id, step_index, "started", time.time())).rowcount
        retried = conn.execute("""UPDATE mission_operations SET state='started', started_at=?, finished_at=NULL
            WHERE mission_id=? AND step_index=? AND state='retry_allowed'""",
            (time.time(), mission_id, step_index)).rowcount
    row = operation(mission_id, step_index)  # type: ignore[assignment]
    row["claimed"] = bool(created or retried)
    return row


def finish_operation(mission_id: str, step_index: int, result: dict[str, Any]) -> None:
    _init_db()
    with _conn() as conn:
        conn.execute("""UPDATE mission_operations SET state='finished', result=?, finished_at=?
            WHERE mission_id=? AND step_index=? AND state='started'""",
            (json.dumps(result), time.time(), mission_id, step_index))


def uncertain_operation(mission_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("""SELECT * FROM mission_operations WHERE mission_id=?
            AND state='started' ORDER BY step_index LIMIT 1""", (mission_id,)).fetchone()
    return dict(row) if row else None


def hold_uncertain(mission_id: str, operation_id_value: str) -> dict[str, Any]:
    reason = f"Operation {operation_id_value} has an unknown outcome; owner reconciliation required"
    with _conn() as conn:
        conn.execute("UPDATE missions SET error=?, error_kind=?, next_attempt_at=NULL WHERE id=?",
                     (reason, "uncertain_effect", mission_id))
    record_event(mission_id, "operation:uncertain", reason)
    return transition(mission_id, PAUSED, detail=reason)


def hold_approval(mission_id: str, reason: str) -> dict[str, Any]:
    with _conn() as conn:
        conn.execute("UPDATE missions SET error=?,error_kind=?,next_attempt_at=NULL WHERE id=?",
                     (reason[:4000], "awaiting_approval", mission_id))
    record_event(mission_id, "approval:required", reason)
    return transition(mission_id, PAUSED, detail=reason)


def reconcile_operation(mission_id: str, step_index: int, *, outcome: str,
                        evidence: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Owner-reviewed outcome; no automatic inference from a missing response."""
    if outcome not in ("completed", "not_executed") or not evidence.strip():
        raise MissionStateError("reconciliation needs a verified outcome and evidence")
    mission = get(mission_id)
    prior = operation(mission_id, step_index)
    if not mission or mission["state"] != PAUSED or not prior or prior["state"] != "started":
        raise MissionStateError("no paused, uncertain operation to reconcile")
    if outcome == "completed" and not isinstance(result, dict):
        raise MissionStateError("completed operation needs its observed result")
    with _conn() as conn:
        changed = conn.execute(
            """UPDATE mission_operations SET state=?, result=?, finished_at=?
               WHERE operation_id=? AND state='started'""",
            ("finished" if outcome == "completed" else "retry_allowed",
             json.dumps(result) if outcome == "completed" else None,
             time.time(), prior["operation_id"]),
        ).rowcount
        if changed != 1:
            raise MissionStateError("operation was already reconciled")
        conn.execute("UPDATE missions SET error=NULL,error_kind=NULL,next_attempt_at=NULL WHERE id=?", (mission_id,))
    record_event(mission_id, "operation:reconciled", f"{outcome}: {evidence[:500]}")
    return make_runnable(mission_id, detail="owner reconciled external outcome")


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


def request_pause(mission_id: str) -> dict[str, Any]:
    mission = get(mission_id)
    if not mission or mission["state"] in TERMINAL_STATES:
        raise MissionStateError("no live mission to pause")
    with _conn() as conn:
        conn.execute("UPDATE missions SET pause_requested=1,updated_at=? WHERE id=?",
                     (time.time(), mission_id))
    record_event(mission_id, "pause_requested", "owner requested pause")
    if mission["state"] == PENDING:
        return transition(mission_id, PAUSED, detail="paused before execution")
    return get(mission_id)  # type: ignore[return-value]


def clear_pause(mission_id: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE missions SET pause_requested=0,updated_at=? WHERE id=?",
                     (time.time(), mission_id))


def clear_error(mission_id: str, *, kind: str = "") -> None:
    with _conn() as conn:
        if kind:
            conn.execute("UPDATE missions SET error=NULL,error_kind=NULL WHERE id=? AND error_kind=?",
                         (mission_id, kind))
        else:
            conn.execute("UPDATE missions SET error=NULL,error_kind=NULL WHERE id=?", (mission_id,))


def pause_requested(mission_id: str) -> bool:
    row = get(mission_id)
    return bool(row and row["pause_requested"])


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
        uncertain = uncertain_operation(mission_id)
        if uncertain:
            hold_uncertain(mission_id, uncertain["operation_id"])
        elif mission.get("pause_requested"):
            transition(mission_id, PAUSED, detail="owner pause preserved after restart")
        else:
            transition(mission_id, PAUSED, detail="interrupted at a safe step boundary")
        recovered.append(mission_id)
    return recovered


def resume_safe_recovered() -> list[str]:
    """Only startup-recovered boundary pauses may be queued by the worker."""
    resumed = []
    for mission in list_missions(state=PAUSED, limit=1000):
        if mission.get("error_kind") == "uncertain_effect" or mission.get("pause_requested"):
            continue
        events = history(mission["id"])
        if events and events[-1]["kind"] == "state:paused" and events[-1]["detail"] == "interrupted at a safe step boundary":
            make_runnable(mission["id"], detail="safe restart boundary")
            resumed.append(mission["id"])
    return resumed


# --------------------------------------------------------------------------
# Durable queue + retry scheduling (Milestone 2)
#
# The queue is the missions table itself — no second store. "Runnable" means
# PENDING; ordering is by created_at so the oldest pending mission goes first.
# A mission PAUSED by a user is deliberately not runnable: only an explicit
# transition back to PENDING makes it eligible again.
# --------------------------------------------------------------------------

MAX_ATTEMPTS = 5
BACKOFF_BASE_S = 2.0
BACKOFF_CAP_S = 300.0


def backoff_seconds(attempts: int) -> float:
    """Exponential backoff, capped, so retryable work can never spin."""
    return min(BACKOFF_BASE_S * (2 ** max(0, attempts - 1)), BACKOFF_CAP_S)


def next_pending(kinds: tuple[str, ...] | None = None) -> dict[str, Any] | None:
    """Oldest runnable mission, or None. Durable: survives any restart.

    ``kinds`` limits what a background worker may claim; other missions stay queued
    untouched for an explicit run.
    """
    _init_db()
    kind_filter = f" AND kind IN ({','.join('?' * len(kinds))})" if kinds else ""
    with _conn() as conn:
        row = conn.execute(
            f"""SELECT * FROM missions
               WHERE state=? AND cancel_requested=0 AND pause_requested=0{kind_filter}
                 AND (kind!='agent_task' OR EXISTS (
                   SELECT 1 FROM agent_task_plans p WHERE p.mission_id=missions.id
                     AND p.approval_state='approved'
                     AND (p.scheduled_at IS NULL OR p.scheduled_at <= ?)))
               ORDER BY created_at ASC LIMIT 1""",
            (PENDING, *(kinds or ()), time.time()),
        ).fetchone()
    return _row_to_mission(row) if row else None


def pending_count() -> int:
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM missions WHERE state=?", (PENDING,)
        ).fetchone()
    return int(row["n"])


def active_count() -> int:
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM missions WHERE state=?", (RUNNING,)
        ).fetchone()
    return int(row["n"])


def schedule_retry(mission_id: str) -> float | None:
    """Record an attempt and arm a backoff window.

    Returns the epoch time the mission becomes eligible again, or None when the
    attempt budget is exhausted (the mission is then made terminally failed).
    """
    mission = get(mission_id)
    if not mission:
        return None
    attempts = int(mission.get("attempts") or 0) + 1
    if attempts >= MAX_ATTEMPTS:
        with _conn() as conn:
            conn.execute(
                "UPDATE missions SET attempts=?, next_attempt_at=NULL, updated_at=? WHERE id=?",
                (attempts, time.time(), mission_id),
            )
        record_event(mission_id, "retry:exhausted", f"after {attempts} attempts")
        if mission["state"] not in TERMINAL_STATES:
            with _conn() as conn:
                conn.execute("UPDATE missions SET error_kind=? WHERE id=?", (TERMINAL, mission_id))
            transition(mission_id, FAILED, detail="retry budget exhausted")
        return None

    due = time.time() + backoff_seconds(attempts)
    with _conn() as conn:
        conn.execute(
            "UPDATE missions SET attempts=?, next_attempt_at=?, updated_at=? WHERE id=?",
            (attempts, due, time.time(), mission_id),
        )
    record_event(
        mission_id, "retry:scheduled", f"attempt {attempts} due in {due - time.time():.1f}s"
    )
    return due


def due_retries(now: float | None = None) -> list[dict[str, Any]]:
    """Retryable missions whose backoff window has elapsed.

    Only missions parked by a *retryable* failure qualify; a mission paused by
    a user has no error_kind and is never picked up automatically.
    """
    _init_db()
    now = time.time() if now is None else now
    with _conn() as conn:
        rows = conn.execute(
            """SELECT * FROM missions
               WHERE state=? AND error_kind=? AND cancel_requested=0
                 AND next_attempt_at IS NOT NULL AND next_attempt_at <= ?
               ORDER BY next_attempt_at ASC""",
            (PAUSED, RETRYABLE, now),
        ).fetchall()
    return [_row_to_mission(r) for r in rows]


def make_runnable(mission_id: str, *, detail: str = "requeued") -> dict[str, Any]:
    """Return a paused/yielded mission to the queue."""
    return transition(mission_id, PENDING, detail=detail)


def clear_retry_state(mission_id: str) -> None:
    """Forget backoff bookkeeping once a mission makes progress again."""
    with _conn() as conn:
        conn.execute(
            "UPDATE missions SET next_attempt_at=NULL, updated_at=? WHERE id=?",
            (time.time(), mission_id),
        )
