"""Durable workflow storage.

Its own database because no existing table describes an orchestration: missions
record objectives and steps but not a dependency graph, per-step provenance or a
workflow context. Follows the same DATA_DIR + WAL + busy_timeout conventions as
every other ARIA store.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from typing import Any

from jarvis.autonomous_workflows.definitions import (
    LIVE_STATES,
    STATES,
    STEP_PENDING,
    STEP_STATES,
    WorkflowDefinitionError,
)
from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "workflows.db"

_init_lock = threading.RLock()

# Legal workflow transitions. Anything else is a bug worth surfacing.
_ALLOWED: dict[str, tuple[str, ...]] = {
    # Pausing before a workflow starts is legitimate: it is how you stop
    # queued work from beginning at all.
    "pending": ("running", "paused", "cancelled", "failed"),
    "running": (
        "running",
        "paused",
        "waiting",
        "blocked",
        "completed",
        "partial",
        "failed",
        "cancelled",
    ),
    "paused": ("running", "cancelled", "failed"),
    "waiting": ("running", "paused", "cancelled", "failed", "blocked", "partial"),
    "blocked": ("running", "partial", "failed", "cancelled"),
    "completed": (),
    "partial": (),
    "failed": (),
    "cancelled": (),
}


class WorkflowStateError(RuntimeError):
    """An illegal state transition, or an operation on a finished workflow."""


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
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
            "SELECT name FROM sqlite_master WHERE type='table' AND name='workflows'"
        ).fetchone()
        if row:
            return
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                requester TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL,
                definition TEXT NOT NULL,
                inputs TEXT NOT NULL DEFAULT '{}',
                context TEXT NOT NULL DEFAULT '{}',
                outputs TEXT NOT NULL DEFAULT '{}',
                mission_id TEXT NOT NULL DEFAULT '',
                current_step TEXT NOT NULL DEFAULT '',
                cancel_requested INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                error_kind TEXT NOT NULL DEFAULT '',
                usage TEXT NOT NULL DEFAULT '{}',
                template_id TEXT NOT NULL DEFAULT '',
                schema_version INTEGER NOT NULL DEFAULT 1,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                started_at REAL,
                finished_at REAL
            );
            CREATE TABLE IF NOT EXISTS workflow_steps (
                workflow_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                action TEXT NOT NULL DEFAULT '',
                agent_id TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                output TEXT,
                error TEXT,
                error_kind TEXT NOT NULL DEFAULT '',
                reason TEXT NOT NULL DEFAULT '',
                provenance TEXT NOT NULL DEFAULT '{}',
                started_at REAL,
                finished_at REAL,
                duration_ms REAL,
                PRIMARY KEY (workflow_id, step_id)
            );
            CREATE TABLE IF NOT EXISTS workflow_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                step_id TEXT NOT NULL DEFAULT '',
                kind TEXT NOT NULL,
                detail TEXT NOT NULL DEFAULT '',
                state TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_wf_state ON workflows(state);
            CREATE INDEX IF NOT EXISTS idx_wf_created ON workflows(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_wf_events ON workflow_events(workflow_id, id);
            """
        )


def new_id() -> str:
    return f"wf_{uuid.uuid4().hex[:10]}"


def _json(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


# ------------------------------------------------------------------ workflows


def create(definition: dict[str, Any], *, requester: str = "") -> str:
    _init_db()
    workflow_id = new_id()
    now = time.time()
    steps = definition.get("steps") or []
    with _conn() as conn:
        conn.execute(
            """INSERT INTO workflows
               (id, name, description, requester, state, definition, inputs, context,
                template_id, schema_version, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                workflow_id,
                str(definition.get("name") or "workflow")[:200],
                str(definition.get("description") or "")[:2000],
                requester or str(definition.get("requester") or ""),
                "pending",
                json.dumps(definition),
                json.dumps(definition.get("inputs") or {}),
                "{}",
                str(definition.get("template_id") or ""),
                int(definition.get("schema_version") or 1),
                now,
                now,
            ),
        )
        for step in steps:
            conn.execute(
                """INSERT INTO workflow_steps
                   (workflow_id, step_id, action, agent_id, state)
                   VALUES (?,?,?,?,?)""",
                (
                    workflow_id,
                    str(step.get("step_id") or ""),
                    str(step.get("action") or ""),
                    str(step.get("agent_id") or ""),
                    STEP_PENDING,
                ),
            )
    record_event(workflow_id, "created", str(definition.get("name") or ""), state="pending")
    return workflow_id


def get(workflow_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM workflows WHERE id=?", (workflow_id,)).fetchone()
        if not row:
            return None
        steps = conn.execute(
            "SELECT * FROM workflow_steps WHERE workflow_id=? ORDER BY step_id", (workflow_id,)
        ).fetchall()
    workflow = dict(row)
    workflow["definition"] = _json(workflow.get("definition"), {})
    workflow["inputs"] = _json(workflow.get("inputs"), {})
    workflow["context"] = _json(workflow.get("context"), {})
    workflow["outputs"] = _json(workflow.get("outputs"), {})
    workflow["usage"] = _json(workflow.get("usage"), {})
    workflow["cancel_requested"] = bool(workflow.get("cancel_requested"))
    workflow["steps"] = [_step_row(s) for s in steps]
    return workflow


def _step_row(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["output"] = _json(d.get("output"), None)
    d["provenance"] = _json(d.get("provenance"), {})
    return d


def list_workflows(*, state: str = "", limit: int = 50) -> list[dict[str, Any]]:
    _init_db()
    clause, params = "", []
    if state:
        clause = "WHERE state=?"
        params.append(state)
    params.append(int(limit))
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT id, name, state, requester, current_step, created_at, updated_at "
            f"FROM workflows {clause} ORDER BY created_at DESC LIMIT ?",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def set_state(workflow_id: str, state: str, *, detail: str = "") -> dict[str, Any]:
    """Transition a workflow, refusing moves the state machine does not allow."""
    if state not in STATES:
        raise WorkflowStateError(f"Unknown workflow state: {state}")
    workflow = get(workflow_id)
    if not workflow:
        raise WorkflowStateError(f"No such workflow: {workflow_id}")
    current = workflow["state"]
    if current == state and state in ("running", "waiting", "blocked"):
        return workflow
    if state not in _ALLOWED.get(current, ()):
        raise WorkflowStateError(f"Illegal workflow transition {current} -> {state}")

    now = time.time()
    fields = {"state": state, "updated_at": now}
    if state == "running" and not workflow.get("started_at"):
        fields["started_at"] = now
    if state in ("completed", "partial", "failed", "cancelled"):
        fields["finished_at"] = now
    _update(workflow_id, **fields)
    record_event(workflow_id, "state", detail or f"{current} -> {state}", state=state)
    return get(workflow_id)  # type: ignore[return-value]


def _update(workflow_id: str, **fields: Any) -> None:
    if not fields:
        return
    _init_db()
    encoded = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in fields.items()}
    encoded.setdefault("updated_at", time.time())
    sets = ", ".join(f"{k}=?" for k in encoded)
    with _conn() as conn:
        conn.execute(f"UPDATE workflows SET {sets} WHERE id=?", (*encoded.values(), workflow_id))


def update(workflow_id: str, **fields: Any) -> None:
    _update(workflow_id, **fields)


def request_cancel(workflow_id: str) -> bool:
    """Ask a workflow to stop. Read from disk, so another process sees it."""
    workflow = get(workflow_id)
    if not workflow or workflow["state"] not in LIVE_STATES:
        return False
    _update(workflow_id, cancel_requested=1)
    record_event(workflow_id, "cancel_requested", "cancellation requested")
    return True


def cancel_requested(workflow_id: str) -> bool:
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT cancel_requested FROM workflows WHERE id=?", (workflow_id,)
        ).fetchone()
    return bool(row and row[0])


# ---------------------------------------------------------------------- steps


def set_step(workflow_id: str, step_id: str, **fields: Any) -> None:
    if "state" in fields and fields["state"] not in STEP_STATES:
        raise WorkflowStateError(f"Unknown step state: {fields['state']}")
    _init_db()
    encoded = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in fields.items()}
    sets = ", ".join(f"{k}=?" for k in encoded)
    with _conn() as conn:
        conn.execute(
            f"UPDATE workflow_steps SET {sets} WHERE workflow_id=? AND step_id=?",
            (*encoded.values(), workflow_id, step_id),
        )


def step_states(workflow_id: str) -> dict[str, str]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT step_id, state FROM workflow_steps WHERE workflow_id=?", (workflow_id,)
        ).fetchall()
    return {r["step_id"]: r["state"] for r in rows}


def step_outputs(workflow_id: str) -> dict[str, Any]:
    """Outputs keyed by step id, in the shape references expect."""
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT step_id, state, output FROM workflow_steps WHERE workflow_id=?",
            (workflow_id,),
        ).fetchall()
    return {r["step_id"]: {"output": _json(r["output"], None), "state": r["state"]} for r in rows}


def bump_usage(workflow_id: str, counter: str, amount: int = 1) -> dict[str, Any]:
    """Track bounded resource use. Read-modify-write under the row lock."""
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT usage FROM workflows WHERE id=?", (workflow_id,)).fetchone()
        usage = _json(row["usage"] if row else "{}", {})
        usage[counter] = int(usage.get(counter, 0)) + amount
        conn.execute(
            "UPDATE workflows SET usage=?, updated_at=? WHERE id=?",
            (json.dumps(usage), time.time(), workflow_id),
        )
    return usage


# --------------------------------------------------------------------- events


def record_event(
    workflow_id: str, kind: str, detail: str = "", *, step_id: str = "", state: str = ""
) -> None:
    _init_db()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO workflow_events (workflow_id, step_id, kind, detail, state, created_at)
               VALUES (?,?,?,?,?,?)""",
            (workflow_id, step_id, kind, str(detail)[:2000], state, time.time()),
        )


def events(workflow_id: str, limit: int = 200) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM workflow_events WHERE workflow_id=? ORDER BY id LIMIT ?",
            (workflow_id, int(limit)),
        ).fetchall()
    return [dict(r) for r in rows]


def interrupted() -> list[str]:
    """Workflows left running by a process that died."""
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT id FROM workflows WHERE state IN ('running','waiting')"
        ).fetchall()
    return [r["id"] for r in rows]


__all__ = [
    "DB_PATH",
    "WorkflowDefinitionError",
    "WorkflowStateError",
    "bump_usage",
    "cancel_requested",
    "create",
    "events",
    "get",
    "interrupted",
    "list_workflows",
    "new_id",
    "record_event",
    "request_cancel",
    "set_state",
    "set_step",
    "step_outputs",
    "step_states",
    "update",
]
