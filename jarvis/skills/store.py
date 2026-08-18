"""Durable skill invocation history.

Its own store because no existing table describes a skill invocation: missions
record objectives and steps, collaboration records delegations, and neither
carries the skill/version/parent chain an audit of this layer needs. Follows
the same DATA_DIR + WAL + busy_timeout conventions as the other ARIA stores.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "skills.db"

_init_lock = threading.RLock()


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
            "SELECT name FROM sqlite_master WHERE type='table' AND name='skill_invocations'"
        ).fetchone()
        if row:
            return
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS skill_invocations (
                id TEXT PRIMARY KEY,
                skill_id TEXT NOT NULL,
                version TEXT NOT NULL,
                requester TEXT NOT NULL DEFAULT '',
                parent_id TEXT NOT NULL DEFAULT '',
                root_id TEXT NOT NULL DEFAULT '',
                mission_id TEXT NOT NULL DEFAULT '',
                depth INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                impact TEXT NOT NULL DEFAULT 'read',
                inputs TEXT NOT NULL DEFAULT '{}',
                output TEXT,
                error TEXT,
                error_kind TEXT NOT NULL DEFAULT '',
                actions TEXT NOT NULL DEFAULT '[]',
                children TEXT NOT NULL DEFAULT '[]',
                side_effects TEXT NOT NULL DEFAULT '[]',
                provenance TEXT NOT NULL DEFAULT '{}',
                verification TEXT NOT NULL DEFAULT 'none',
                started_at REAL NOT NULL,
                finished_at REAL,
                duration_ms REAL
            );
            CREATE INDEX IF NOT EXISTS idx_skill_inv_skill ON skill_invocations(skill_id);
            CREATE INDEX IF NOT EXISTS idx_skill_inv_root ON skill_invocations(root_id);
            CREATE INDEX IF NOT EXISTS idx_skill_inv_started ON skill_invocations(started_at DESC);
            """
        )


def new_id() -> str:
    return f"skx_{uuid.uuid4().hex[:10]}"


def _json(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def start(
    invocation_id: str,
    skill_id: str,
    version: str,
    *,
    requester: str = "",
    parent_id: str = "",
    root_id: str = "",
    mission_id: str = "",
    depth: int = 0,
    impact: str = "read",
    inputs: dict[str, Any] | None = None,
) -> str:
    _init_db()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO skill_invocations
               (id, skill_id, version, requester, parent_id, root_id, mission_id, depth,
                status, impact, inputs, started_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                invocation_id,
                skill_id,
                version,
                requester,
                parent_id,
                root_id or invocation_id,
                mission_id,
                depth,
                "running",
                impact,
                json.dumps(inputs or {}),
                time.time(),
            ),
        )
    return invocation_id


def finish(invocation_id: str, envelope: dict[str, Any]) -> None:
    _init_db()
    started = envelope.get("started_at") or time.time()
    with _conn() as conn:
        conn.execute(
            """UPDATE skill_invocations SET
                 status=?, output=?, error=?, error_kind=?, actions=?, children=?,
                 side_effects=?, provenance=?, verification=?, impact=?,
                 finished_at=?, duration_ms=?
               WHERE id=?""",
            (
                envelope.get("status", "failed"),
                json.dumps(envelope.get("output")),
                envelope.get("error"),
                envelope.get("error_kind") or "",
                json.dumps(envelope.get("actions") or []),
                json.dumps(envelope.get("children") or []),
                json.dumps(envelope.get("side_effects") or []),
                json.dumps(envelope.get("provenance") or {}),
                envelope.get("verification") or "none",
                envelope.get("impact") or "read",
                time.time(),
                round((time.time() - started) * 1000, 2),
                invocation_id,
            ),
        )


def get(invocation_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM skill_invocations WHERE id=?", (invocation_id,)
        ).fetchone()
    return _row(row) if row else None


def history(
    *, skill_id: str = "", root_id: str = "", requester: str = "", limit: int = 50
) -> list[dict[str, Any]]:
    _init_db()
    clauses, params = [], []
    if skill_id:
        clauses.append("skill_id=?")
        params.append(skill_id)
    if root_id:
        clauses.append("root_id=?")
        params.append(root_id)
    if requester:
        clauses.append("requester=?")
        params.append(requester)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(int(limit))
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM skill_invocations {where} ORDER BY started_at DESC LIMIT ?",
            params,
        ).fetchall()
    return [_row(r) for r in rows]


def children_of(invocation_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM skill_invocations WHERE parent_id=? ORDER BY started_at",
            (invocation_id,),
        ).fetchall()
    return [_row(r) for r in rows]


def _row(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["inputs"] = _json(d.get("inputs"), {})
    d["output"] = _json(d.get("output"), None)
    d["actions"] = _json(d.get("actions"), [])
    d["children"] = _json(d.get("children"), [])
    d["side_effects"] = _json(d.get("side_effects"), [])
    d["provenance"] = _json(d.get("provenance"), {})
    return d
