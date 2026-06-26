# Source Generated with Decompyle++
# File: chat_sessions.cpython-312.pyc (Python 3.12)

'''SQLite chat sessions (named threads, pin, branch link).'''
from __future__ import annotations
import sqlite3
import uuid
from datetime import datetime
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.p1_flags import chat_sessions_enabled
DB_PATH = DATA_DIR / 'chat_sessions.db'

def _conn():
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init():
    conn = _conn()
    conn.executescript('\n            CREATE TABLE IF NOT EXISTS sessions (\n                id TEXT PRIMARY KEY,\n                title TEXT NOT NULL,\n                branch_id TEXT,\n                pinned INTEGER DEFAULT 0,\n                created_at TEXT NOT NULL,\n                updated_at TEXT NOT NULL\n            );\n            ')
    None(None, None)
    return None
    with None:
        if not None:
            pass

_init()

def _now():
    return datetime.now().isoformat(timespec = 'seconds')


def create_session(title = None, *, branch_id):
    sid = uuid.uuid4().hex[:12]
    now = _now()
    conn = _conn()
    if not title.strip():
        title.strip()
    conn.execute('INSERT INTO sessions (id, title, branch_id, pinned, created_at, updated_at) VALUES (?, ?, ?, 0, ?, ?)', (sid, 'New chat', branch_id, now, now))
    None(None, None)
    return {
        'id': sid,
        'title': title,
        'branch_id': branch_id,
        'pinned': False,
        'created_at': now }
    with None:
        if not None:
            pass
    continue


def list_sessions(*, limit):
    if not chat_sessions_enabled():
        return []
    conn = None()
    rows = conn.execute('SELECT * FROM sessions ORDER BY pinned DESC, updated_at DESC LIMIT ?', (limit,)).fetchall()
    None(None, None)
# WARNING: Decompyle incomplete


def rename_session(session_id = None, title = None):
    conn = _conn()
    cur = conn.execute('UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?', (title.strip(), _now(), session_id))
    None(None, None)
    return 
    with None:
        if not None, cur.rowcount > 0:
            pass


def pin_session(session_id = None, pinned = None):
    conn = _conn()
    cur = conn.execute('UPDATE sessions SET pinned = ?, updated_at = ? WHERE id = ?', (1 if pinned else 0, _now(), session_id))
    None(None, None)
    return 
    with None:
        if not None, cur.rowcount > 0:
            pass


def touch_session(session_id = None):
    conn = _conn()
    conn.execute('UPDATE sessions SET updated_at = ? WHERE id = ?', (_now(), session_id))
    None(None, None)
    return None
    with None:
        if not None:
            pass


def get_session(session_id = None):
    conn = _conn()
    row = conn.execute('SELECT * FROM sessions WHERE id = ?', (session_id,)).fetchone()
    None(None, None)
# WARNING: Decompyle incomplete

