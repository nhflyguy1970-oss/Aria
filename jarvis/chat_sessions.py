"""SQLite chat sessions (named threads, pin, branch link)."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.p1_flags import chat_sessions_enabled

DB_PATH = DATA_DIR / "chat_sessions.db"


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init() -> None:
    with _conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                branch_id TEXT,
                pinned INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


_init()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "branch_id": row["branch_id"],
        "pinned": bool(row["pinned"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_session(title: str | None = None, *, branch_id: str | None = None) -> dict[str, Any]:
    sid = uuid.uuid4().hex[:12]
    now = _now()
    title = (title or "New chat").strip() or "New chat"
    with _conn() as conn:
        conn.execute(
            "INSERT INTO sessions (id, title, branch_id, pinned, created_at, updated_at) VALUES (?, ?, ?, 0, ?, ?)",
            (sid, title, branch_id, now, now),
        )
    return {
        "id": sid,
        "title": title,
        "branch_id": branch_id,
        "pinned": False,
        "created_at": now,
        "updated_at": now,
    }


def list_sessions(*, limit: int = 50) -> list[dict[str, Any]]:
    if not chat_sessions_enabled():
        return []
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY pinned DESC, updated_at DESC LIMIT ?",
            (max(1, int(limit)),),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def rename_session(session_id: str, title: str) -> bool:
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (title.strip(), _now(), session_id),
        )
    return cur.rowcount > 0


def pin_session(session_id: str, pinned: bool = True) -> bool:
    with _conn() as conn:
        cur = conn.execute(
            "UPDATE sessions SET pinned = ?, updated_at = ? WHERE id = ?",
            (1 if pinned else 0, _now(), session_id),
        )
    return cur.rowcount > 0


def touch_session(session_id: str) -> None:
    with _conn() as conn:
        conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (_now(), session_id),
        )


def get_session(session_id: str) -> dict[str, Any] | None:
    with _conn() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    return _row_to_dict(row) if row else None


def seed_default_sessions() -> None:
    """Ensure starter named sessions exist for the sidebar UX."""
    if not chat_sessions_enabled():
        return
    if list_sessions(limit=1):
        return
    for title, branch_id in (("Main chat", "main"), ("Work", "work"), ("Personal", "personal")):
        create_session(title, branch_id=branch_id)


seed_default_sessions()
