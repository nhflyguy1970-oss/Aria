"""Durable routing audit.

Enough to answer, later, "which model actually did this, and why that one?" —
without keeping the prompts and responses themselves. Follows the same
DATA_DIR + WAL + busy_timeout conventions as ARIA's other stores.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "model_routing.db"

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
            "SELECT name FROM sqlite_master WHERE type='table' AND name='routing_invocations'"
        ).fetchone()
        if row:
            return
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS routing_invocations (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT '',
                requester TEXT NOT NULL DEFAULT '',
                agent_id TEXT NOT NULL DEFAULT '',
                skill_id TEXT NOT NULL DEFAULT '',
                mission_id TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                selected_model TEXT NOT NULL DEFAULT '',
                final_model TEXT NOT NULL DEFAULT '',
                provider TEXT NOT NULL DEFAULT '',
                selection_method TEXT NOT NULL DEFAULT '',
                fallback_count INTEGER NOT NULL DEFAULT 0,
                fallback_chain TEXT NOT NULL DEFAULT '[]',
                attempts TEXT NOT NULL DEFAULT '[]',
                decision TEXT NOT NULL DEFAULT '{}',
                failure_kind TEXT NOT NULL DEFAULT '',
                error TEXT,
                policy_version TEXT NOT NULL DEFAULT '',
                started_at REAL NOT NULL,
                duration_ms REAL
            );
            CREATE INDEX IF NOT EXISTS idx_routing_model ON routing_invocations(final_model);
            CREATE INDEX IF NOT EXISTS idx_routing_started
                ON routing_invocations(started_at DESC);
            """
        )


def new_id() -> str:
    return f"rt_{uuid.uuid4().hex[:10]}"


def _json(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def record(envelope: dict[str, Any]) -> str:
    """Persist one routed invocation. Prompts and responses are never stored."""
    _init_db()
    invocation_id = envelope.get("invocation_id") or new_id()
    decision = envelope.get("decision") or {}
    with _conn() as conn:
        conn.execute(
            """INSERT INTO routing_invocations
               (id, task_type, role, requester, agent_id, skill_id, mission_id, status,
                selected_model, final_model, provider, selection_method, fallback_count,
                fallback_chain, attempts, decision, failure_kind, error, policy_version,
                started_at, duration_ms)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                invocation_id,
                (decision.get("request") or {}).get("task_type", ""),
                (decision.get("request") or {}).get("role", ""),
                envelope.get("requester", ""),
                envelope.get("agent_id", ""),
                envelope.get("skill_id", ""),
                envelope.get("mission_id", ""),
                envelope.get("status", "failed"),
                decision.get("selected_model", ""),
                envelope.get("final_model", ""),
                envelope.get("provider", ""),
                decision.get("selection_method", ""),
                envelope.get("fallback_count", 0),
                json.dumps(envelope.get("fallback_chain") or []),
                json.dumps(envelope.get("attempts") or []),
                json.dumps(decision),
                envelope.get("failure_kind", ""),
                envelope.get("error"),
                decision.get("policy_version", ""),
                envelope.get("started_at") or time.time(),
                envelope.get("duration_ms"),
            ),
        )
    return invocation_id


def get(invocation_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM routing_invocations WHERE id=?", (invocation_id,)
        ).fetchone()
    return _row(row) if row else None


def history(
    *, model: str = "", requester: str = "", mission_id: str = "", limit: int = 50
) -> list[dict[str, Any]]:
    _init_db()
    clauses, params = [], []
    if model:
        clauses.append("final_model=?")
        params.append(model)
    if requester:
        clauses.append("requester=?")
        params.append(requester)
    if mission_id:
        clauses.append("mission_id=?")
        params.append(mission_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(int(limit))
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM routing_invocations {where} ORDER BY started_at DESC LIMIT ?",
            params,
        ).fetchall()
    return [_row(r) for r in rows]


def counters() -> dict[str, Any]:
    _init_db()
    with _conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM routing_invocations").fetchone()[0]
        by_status = {
            r[0]: r[1]
            for r in conn.execute(
                "SELECT status, COUNT(*) FROM routing_invocations GROUP BY status"
            )
        }
        fallbacks = conn.execute(
            "SELECT COUNT(*) FROM routing_invocations WHERE fallback_count > 0"
        ).fetchone()[0]
        by_model = {
            r[0]: r[1]
            for r in conn.execute(
                "SELECT final_model, COUNT(*) FROM routing_invocations "
                "WHERE final_model != '' GROUP BY final_model ORDER BY 2 DESC LIMIT 10"
            )
        }
    return {
        "total": total,
        "by_status": by_status,
        "with_fallback": fallbacks,
        "top_models": by_model,
    }


def _row(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["fallback_chain"] = _json(d.get("fallback_chain"), [])
    d["attempts"] = _json(d.get("attempts"), [])
    d["decision"] = _json(d.get("decision"), {})
    return d
