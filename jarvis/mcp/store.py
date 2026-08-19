"""Durable MCP provider configuration and invocation audit.

One store, following the same DATA_DIR + WAL + busy_timeout conventions as the
other ARIA databases. Provider environment values are deliberately *not*
persisted here: configuration that carries a credential is held in the separate
secrets file, which is not part of the audit trail.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "mcp.db"

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
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mcp_providers'"
        ).fetchone()
        if row:
            return
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS mcp_providers (
                provider_id TEXT PRIMARY KEY,
                config TEXT NOT NULL,
                trust TEXT NOT NULL DEFAULT 'untrusted',
                enabled INTEGER NOT NULL DEFAULT 1,
                health TEXT NOT NULL DEFAULT 'unknown',
                last_error TEXT NOT NULL DEFAULT '',
                last_seen REAL,
                invocations INTEGER NOT NULL DEFAULT 0,
                failures INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS mcp_invocations (
                id TEXT PRIMARY KEY,
                provider_id TEXT NOT NULL,
                operation TEXT NOT NULL,
                target TEXT NOT NULL DEFAULT '',
                requester TEXT NOT NULL DEFAULT '',
                skill_id TEXT NOT NULL DEFAULT '',
                mission_id TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                impact TEXT NOT NULL DEFAULT 'read',
                arguments TEXT NOT NULL DEFAULT '{}',
                result TEXT,
                error TEXT,
                error_kind TEXT NOT NULL DEFAULT '',
                truncated INTEGER NOT NULL DEFAULT 0,
                provenance TEXT NOT NULL DEFAULT '{}',
                started_at REAL NOT NULL,
                duration_ms REAL
            );
            CREATE INDEX IF NOT EXISTS idx_mcp_inv_provider ON mcp_invocations(provider_id);
            CREATE INDEX IF NOT EXISTS idx_mcp_inv_started ON mcp_invocations(started_at DESC);
            """
        )


def new_id() -> str:
    return f"mcx_{uuid.uuid4().hex[:10]}"


def _json(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


# ------------------------------------------------------------------- providers


def save_provider(provider_id: str, config: dict[str, Any], *, trust: str, enabled: bool) -> None:
    _init_db()
    now = time.time()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO mcp_providers (provider_id, config, trust, enabled, created_at,
                                          updated_at)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(provider_id) DO UPDATE SET
                 config=excluded.config, trust=excluded.trust,
                 enabled=excluded.enabled, updated_at=excluded.updated_at""",
            (provider_id, json.dumps(config), trust, int(enabled), now, now),
        )


def delete_provider(provider_id: str) -> bool:
    _init_db()
    with _conn() as conn:
        cur = conn.execute("DELETE FROM mcp_providers WHERE provider_id=?", (provider_id,))
        return cur.rowcount > 0


def get_provider(provider_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM mcp_providers WHERE provider_id=?", (provider_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["config"] = _json(d.get("config"), {})
    return d


def list_providers() -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM mcp_providers ORDER BY provider_id").fetchall()
    out = []
    for row in rows:
        d = dict(row)
        d["config"] = _json(d.get("config"), {})
        out.append(d)
    return out


def _ensure_row(conn: sqlite3.Connection, provider_id: str) -> None:
    """A provider registered in-process still needs a row to be audited against."""
    now = time.time()
    conn.execute(
        """INSERT OR IGNORE INTO mcp_providers (provider_id, config, created_at, updated_at)
           VALUES (?,?,?,?)""",
        (provider_id, "{}", now, now),
    )


def record_health(provider_id: str, health: str, *, error: str = "", seen: bool = True) -> None:
    _init_db()
    with _conn() as conn:
        _ensure_row(conn, provider_id)
        conn.execute(
            """UPDATE mcp_providers
               SET health=?, last_error=?, last_seen=COALESCE(?, last_seen), updated_at=?
               WHERE provider_id=?""",
            (health, error[:2000], time.time() if seen else None, time.time(), provider_id),
        )


def bump_counters(provider_id: str, *, failed: bool) -> None:
    _init_db()
    with _conn() as conn:
        _ensure_row(conn, provider_id)
        conn.execute(
            """UPDATE mcp_providers
               SET invocations=invocations+1, failures=failures+?, updated_at=?
               WHERE provider_id=?""",
            (1 if failed else 0, time.time(), provider_id),
        )


# ----------------------------------------------------------------- invocations


def record_invocation(envelope: dict[str, Any]) -> str:
    """Persist one operation. Arguments and results are already redacted."""
    _init_db()
    invocation_id = envelope.get("invocation_id") or new_id()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO mcp_invocations
               (id, provider_id, operation, target, requester, skill_id, mission_id, status,
                impact, arguments, result, error, error_kind, truncated, provenance,
                started_at, duration_ms)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                invocation_id,
                envelope.get("provider_id", ""),
                envelope.get("operation", ""),
                envelope.get("target", ""),
                envelope.get("requester", ""),
                envelope.get("skill_id", ""),
                envelope.get("mission_id", ""),
                envelope.get("status", "failed"),
                envelope.get("impact", "read"),
                json.dumps(envelope.get("arguments") or {}),
                json.dumps(envelope.get("result")),
                envelope.get("error"),
                envelope.get("error_kind") or "",
                int(bool(envelope.get("truncated"))),
                json.dumps(envelope.get("provenance") or {}),
                envelope.get("started_at") or time.time(),
                envelope.get("duration_ms"),
            ),
        )
    return invocation_id


def get_invocation(invocation_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM mcp_invocations WHERE id=?", (invocation_id,)).fetchone()
    return _inv_row(row) if row else None


def history(*, provider_id: str = "", requester: str = "", limit: int = 50) -> list[dict[str, Any]]:
    _init_db()
    clauses, params = [], []
    if provider_id:
        clauses.append("provider_id=?")
        params.append(provider_id)
    if requester:
        clauses.append("requester=?")
        params.append(requester)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(int(limit))
    with _conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM mcp_invocations {where} ORDER BY started_at DESC LIMIT ?", params
        ).fetchall()
    return [_inv_row(r) for r in rows]


def _inv_row(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["arguments"] = _json(d.get("arguments"), {})
    d["result"] = _json(d.get("result"), None)
    d["provenance"] = _json(d.get("provenance"), {})
    d["truncated"] = bool(d.get("truncated"))
    return d
