"""Continuity index — a rebuildable SQLite view over ARIA's source history.

This is not a memory engine and asserts nothing on its own. ACM stays the
authority for what ARIA knows about the user. This index answers the narrower
question "what was actually said and done, when, and where": it mirrors the
append-only conversation archive (Phase 1) and the mission/tool records, and
derives continuity records — ideas, decisions, rejections, corrections, open
work, outcomes — that each point back to the episodes they came from.

Everything here can be rebuilt from the archive and the mission store; nothing
is the only copy of anything.

Tables
  episodes   one row per archived turn (id = the archive event id)
  episodes_fts  full-text index over episode content
  records    derived continuity records, each citing supporting episodes
  outbox     idempotent queue of user statements to encode into ACM
  sync_state per-source ingestion offsets (archive file byte offsets)
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "continuity.db"

# Record kinds.
IDEA = "idea"
DECISION = "decision"
REJECTION = "rejection"
CORRECTION = "correction"
TASK = "task"
SUGGESTION = "suggestion"
OUTCOME = "outcome"
CHECKPOINT = "checkpoint"
KINDS = (IDEA, DECISION, REJECTION, CORRECTION, TASK, SUGGESTION, OUTCOME, CHECKPOINT)

# Record statuses.
OPEN = "open"  # an idea, task or decision currently in force
PROPOSED = "proposed"  # an assistant suggestion nobody has acted on
ACCEPTED = "accepted"
REJECTED = "rejected"
SUPERSEDED = "superseded"  # replaced by a later correction or decision
DONE = "done"
FAILED = "failed"
STATUSES = (OPEN, PROPOSED, ACCEPTED, REJECTED, SUPERSEDED, DONE, FAILED)

# Who a record's content came from. Kept distinct on purpose: a user decision,
# an assistant suggestion and a tool's report are different kinds of evidence.
USER = "user"
ASSISTANT = "assistant"
TOOL = "tool"
MISSION = "mission"
ACTORS = (USER, ASSISTANT, TOOL, MISSION)

_init_lock = threading.Lock()
_initialised: set[str] = set()


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    return conn


def _init_db() -> None:
    key = str(DB_PATH)
    if key in _initialised and DB_PATH.exists():
        return
    with _init_lock:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(DB_PATH)
        with _conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS episodes (
                    id TEXT PRIMARY KEY,
                    branch TEXT NOT NULL,
                    ts REAL NOT NULL,
                    role TEXT NOT NULL,
                    kind TEXT NOT NULL,          -- message | seed | import
                    content TEXT NOT NULL,
                    origin TEXT NOT NULL DEFAULT '',
                    project TEXT NOT NULL DEFAULT '',
                    erased INTEGER NOT NULL DEFAULT 0,
                    content_hash TEXT NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS ix_episodes_ts ON episodes(ts);
                CREATE INDEX IF NOT EXISTS ix_episodes_branch ON episodes(branch, ts);
                CREATE INDEX IF NOT EXISTS ix_episodes_hash ON episodes(content_hash);
                CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
                    content, content='episodes', content_rowid='rowid',
                    tokenize='porter unicode61'
                );
                CREATE TRIGGER IF NOT EXISTS episodes_ai AFTER INSERT ON episodes BEGIN
                    INSERT INTO episodes_fts(rowid, content) VALUES (new.rowid, new.content);
                END;
                CREATE TRIGGER IF NOT EXISTS episodes_au AFTER UPDATE OF content ON episodes BEGIN
                    INSERT INTO episodes_fts(episodes_fts, rowid, content)
                        VALUES ('delete', old.rowid, old.content);
                    INSERT INTO episodes_fts(rowid, content) VALUES (new.rowid, new.content);
                END;

                CREATE TABLE IF NOT EXISTS records (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    status TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    text TEXT NOT NULL,
                    project TEXT NOT NULL DEFAULT '',
                    branch TEXT NOT NULL DEFAULT '',
                    ts REAL NOT NULL,
                    updated_ts REAL NOT NULL,
                    episode_ids TEXT NOT NULL DEFAULT '[]',
                    acm_ids TEXT NOT NULL DEFAULT '[]',
                    source_ref TEXT NOT NULL DEFAULT '',
                    superseded_by TEXT NOT NULL DEFAULT '',
                    verified INTEGER NOT NULL DEFAULT 0,
                    detail TEXT NOT NULL DEFAULT '{}'
                );
                CREATE INDEX IF NOT EXISTS ix_records_kind ON records(kind, status, ts);
                CREATE UNIQUE INDEX IF NOT EXISTS ux_records_source
                    ON records(source_ref) WHERE source_ref != '';
                CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(
                    text, content='records', content_rowid='rowid',
                    tokenize='porter unicode61'
                );
                CREATE TRIGGER IF NOT EXISTS records_ai AFTER INSERT ON records BEGIN
                    INSERT INTO records_fts(rowid, text) VALUES (new.rowid, new.text);
                END;
                CREATE TRIGGER IF NOT EXISTS records_au AFTER UPDATE OF text ON records BEGIN
                    INSERT INTO records_fts(records_fts, rowid, text)
                        VALUES ('delete', old.rowid, old.text);
                    INSERT INTO records_fts(rowid, text) VALUES (new.rowid, new.text);
                END;

                CREATE TABLE IF NOT EXISTS outbox (
                    episode_id TEXT NOT NULL,
                    target TEXT NOT NULL,           -- 'acm'
                    record_kind TEXT NOT NULL,
                    status TEXT NOT NULL,           -- pending | done | skipped | failed
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT NOT NULL DEFAULT '',
                    acm_id TEXT NOT NULL DEFAULT '',
                    created_ts REAL NOT NULL,
                    updated_ts REAL NOT NULL,
                    PRIMARY KEY (episode_id, target)
                );
                CREATE INDEX IF NOT EXISTS ix_outbox_status ON outbox(status, updated_ts);

                CREATE TABLE IF NOT EXISTS sync_state (
                    source TEXT PRIMARY KEY,
                    position INTEGER NOT NULL DEFAULT 0,
                    updated_ts REAL NOT NULL
                );
                """
            )
        _initialised.add(key)


def reset_for_tests() -> None:
    _initialised.clear()


def _hash(role: str, content: str) -> str:
    import hashlib

    return hashlib.sha256(f"{role}\0{(content or '').strip()}".encode()).hexdigest()


# ------------------------------------------------------------------ episodes


def add_episode(
    episode_id: str,
    *,
    branch: str,
    ts: float,
    role: str,
    kind: str,
    content: str,
    origin: str = "",
    project: str = "",
) -> bool:
    """Insert one archived turn. Returns False if it was already indexed."""
    _init_db()
    with _conn() as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO episodes
               (id, branch, ts, role, kind, content, origin, project, content_hash)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                episode_id,
                branch,
                float(ts),
                role,
                kind,
                content or "",
                origin,
                project,
                _hash(role, content),
            ),
        )
        return cur.rowcount > 0


def get_episode(episode_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM episodes WHERE id=?", (episode_id,)).fetchone()
    return dict(row) if row else None


def episodes_between(
    start: float | None = None,
    end: float | None = None,
    *,
    branch: str | None = None,
    limit: int = 200,
    newest_first: bool = True,
) -> list[dict[str, Any]]:
    _init_db()
    sql = "SELECT * FROM episodes WHERE erased=0"
    args: list[Any] = []
    if start is not None:
        sql += " AND ts >= ?"
        args.append(start)
    if end is not None:
        sql += " AND ts < ?"
        args.append(end)
    if branch:
        sql += " AND branch = ?"
        args.append(branch)
    sql += f" ORDER BY ts {'DESC' if newest_first else 'ASC'} LIMIT ?"
    args.append(int(limit))
    with _conn() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def search_episodes(
    match: str,
    *,
    start: float | None = None,
    end: float | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """FTS5 match over episode content; `match` is an FTS5 query expression."""
    _init_db()
    sql = (
        "SELECT e.*, bm25(episodes_fts) AS score FROM episodes_fts "
        "JOIN episodes e ON e.rowid = episodes_fts.rowid "
        "WHERE episodes_fts MATCH ? AND e.erased=0"
    )
    args: list[Any] = [match]
    if start is not None:
        sql += " AND e.ts >= ?"
        args.append(start)
    if end is not None:
        sql += " AND e.ts < ?"
        args.append(end)
    sql += " ORDER BY score LIMIT ?"
    args.append(int(limit))
    with _conn() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def episode_hashes() -> set[str]:
    _init_db()
    with _conn() as conn:
        return {r[0] for r in conn.execute("SELECT content_hash FROM episodes")}


def counts() -> dict[str, Any]:
    _init_db()
    with _conn() as conn:
        episodes = conn.execute("SELECT count(*), max(ts) FROM episodes WHERE erased=0").fetchone()
        records = {
            r["kind"]: r["n"]
            for r in conn.execute("SELECT kind, count(*) AS n FROM records GROUP BY kind")
        }
        outbox = {
            r["status"]: r["n"]
            for r in conn.execute("SELECT status, count(*) AS n FROM outbox GROUP BY status")
        }
    return {
        "episodes": episodes[0],
        "newest_episode_ts": episodes[1],
        "records": records,
        "outbox": outbox,
    }


# ------------------------------------------------------------------ records


def _record_row(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    for key in ("episode_ids", "acm_ids"):
        d[key] = json.loads(d.get(key) or "[]")
    d["detail"] = json.loads(d.get("detail") or "{}")
    d["verified"] = bool(d.get("verified"))
    return d


def add_record(
    kind: str,
    text: str,
    *,
    actor: str,
    status: str,
    ts: float | None = None,
    project: str = "",
    branch: str = "",
    episode_ids: list[str] | None = None,
    source_ref: str = "",
    verified: bool = False,
    detail: dict[str, Any] | None = None,
) -> str:
    """Add a continuity record. A non-empty source_ref makes the write idempotent."""
    if kind not in KINDS:
        raise ValueError(f"unknown record kind {kind!r}")
    if status not in STATUSES:
        raise ValueError(f"unknown record status {status!r}")
    if actor not in ACTORS:
        raise ValueError(f"unknown actor {actor!r}")
    _init_db()
    now = time.time()
    rid = "rec_" + uuid.uuid4().hex[:12]
    with _conn() as conn:
        if source_ref:
            existing = conn.execute(
                "SELECT id FROM records WHERE source_ref=?", (source_ref,)
            ).fetchone()
            if existing:
                return existing["id"]
        conn.execute(
            """INSERT INTO records (id, kind, status, actor, text, project, branch, ts,
                   updated_ts, episode_ids, source_ref, verified, detail)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                rid,
                kind,
                status,
                actor,
                text,
                project,
                branch,
                float(ts if ts is not None else now),
                now,
                json.dumps(list(episode_ids or [])),
                source_ref,
                1 if verified else 0,
                json.dumps(detail or {}),
            ),
        )
    return rid


def update_record(record_id: str, **fields: Any) -> None:
    allowed = {"status", "superseded_by", "verified", "text", "detail", "acm_ids"}
    sets, args = [], []
    for key, value in fields.items():
        if key not in allowed:
            raise ValueError(f"cannot update {key}")
        if key in ("detail",):
            value = json.dumps(value or {})
        elif key == "acm_ids":
            value = json.dumps(list(value or []))
        elif key == "verified":
            value = 1 if value else 0
        sets.append(f"{key}=?")
        args.append(value)
    if not sets:
        return
    _init_db()
    sets.append("updated_ts=?")
    args.append(time.time())
    args.append(record_id)
    with _conn() as conn:
        conn.execute(f"UPDATE records SET {', '.join(sets)} WHERE id=?", args)


def get_record(record_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()
    return _record_row(row) if row else None


def record_by_source(source_ref: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM records WHERE source_ref=?", (source_ref,)).fetchone()
    return _record_row(row) if row else None


def list_records(
    *,
    kinds: tuple[str, ...] | list[str] | None = None,
    statuses: tuple[str, ...] | list[str] | None = None,
    start: float | None = None,
    end: float | None = None,
    branch: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    _init_db()
    sql = "SELECT * FROM records WHERE 1=1"
    args: list[Any] = []
    if kinds:
        sql += f" AND kind IN ({','.join('?' * len(kinds))})"
        args.extend(kinds)
    if statuses:
        sql += f" AND status IN ({','.join('?' * len(statuses))})"
        args.extend(statuses)
    if start is not None:
        sql += " AND ts >= ?"
        args.append(start)
    if end is not None:
        sql += " AND ts < ?"
        args.append(end)
    if branch:
        sql += " AND branch = ?"
        args.append(branch)
    sql += " ORDER BY ts DESC LIMIT ?"
    args.append(int(limit))
    with _conn() as conn:
        return [_record_row(r) for r in conn.execute(sql, args).fetchall()]


def search_records(match: str, *, limit: int = 30) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT r.*, bm25(records_fts) AS score FROM records_fts "
            "JOIN records r ON r.rowid = records_fts.rowid "
            "WHERE records_fts MATCH ? ORDER BY score LIMIT ?",
            (match, int(limit)),
        ).fetchall()
    return [_record_row(r) for r in rows]


def records_citing(episode_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM records WHERE episode_ids LIKE ?", (f'%"{episode_id}"%',)
        ).fetchall()
    return [_record_row(r) for r in rows]


# ------------------------------------------------------------------ outbox


def enqueue(episode_id: str, *, record_kind: str, target: str = "acm") -> bool:
    _init_db()
    now = time.time()
    with _conn() as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO outbox
               (episode_id, target, record_kind, status, created_ts, updated_ts)
               VALUES (?,?,?,?,?,?)""",
            (episode_id, target, record_kind, "pending", now, now),
        )
        return cur.rowcount > 0


def pending_outbox(*, target: str = "acm", limit: int = 20, max_attempts: int = 5) -> list[dict]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            """SELECT * FROM outbox WHERE target=? AND status IN ('pending','failed')
               AND attempts < ? ORDER BY created_ts LIMIT ?""",
            (target, max_attempts, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def mark_outbox(
    episode_id: str,
    *,
    status: str,
    target: str = "acm",
    error: str = "",
    acm_id: str = "",
    attempted: bool = True,
) -> None:
    _init_db()
    with _conn() as conn:
        conn.execute(
            """UPDATE outbox SET status=?, last_error=?, acm_id=?, updated_ts=?,
                   attempts = attempts + ? WHERE episode_id=? AND target=?""",
            (status, error[:500], acm_id, time.time(), 1 if attempted else 0, episode_id, target),
        )


def outbox_entry(episode_id: str, target: str = "acm") -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM outbox WHERE episode_id=? AND target=?", (episode_id, target)
        ).fetchone()
    return dict(row) if row else None


# ------------------------------------------------------------------ sync state


def get_position(source: str) -> int:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT position FROM sync_state WHERE source=?", (source,)).fetchone()
    return int(row["position"]) if row else 0


def set_position(source: str, position: int) -> None:
    _init_db()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO sync_state (source, position, updated_ts) VALUES (?,?,?)
               ON CONFLICT(source) DO UPDATE SET position=excluded.position,
                   updated_ts=excluded.updated_ts""",
            (source, int(position), time.time()),
        )
