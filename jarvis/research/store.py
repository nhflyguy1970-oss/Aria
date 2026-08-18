"""SQLite research store — jobs, questions, sources, evidence, claims, citations.

Follows the same conventions as jarvis.missions.store and jarvis.planner_store:
a SQLite database under DATA_DIR, WAL, created on demand, initialised
concurrency-safely because the background mission worker and request threads
both reach it.

The schema preserves the chain the milestone requires:

    SOURCE -> EVIDENCE -> CLAIM -> SYNTHESIS

so a synthesised statement can always be traced back to the material that
supports it, and disagreement between sources is recorded rather than resolved
by silently picking a winner.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "research.db"

_init_lock = threading.Lock()

# Job lifecycle mirrors the mission vocabulary so the two read alike.
PENDING = "pending"
RUNNING = "running"
PAUSED = "paused"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"
TERMINAL_STATES = (COMPLETED, FAILED, CANCELLED)

# How evidence relates to a claim.
SUPPORTS = "supports"
CONTRADICTS = "contradicts"
VERIFIES = "verifies"
STANCES = (SUPPORTS, CONTRADICTS, VERIFIES)

# A claim is either drawn directly from a source or inferred across sources.
FACT = "fact"
INFERENCE = "inference"


def canonical_url(url: str) -> str:
    """Deduplication key for a URL.

    The scheme is dropped, not normalised: http://x/a and https://x/a are the
    same page for research purposes, and keeping the scheme would store it
    twice. Also drops "www.", the fragment, and a trailing slash.
    """
    raw = (url or "").strip()
    if not raw:
        return ""
    if "//" not in raw:
        raw = "//" + raw
    parts = urlsplit(raw if "://" in raw else "https:" + raw)
    host = (parts.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return ""
    path = parts.path.rstrip("/") or "/"
    return urlunsplit(("", host, path, parts.query, "")).lstrip("/") or host


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _init_db() -> None:
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
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='research_jobs'"
        ).fetchone()
        if row:
            return
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            pass
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS research_jobs (
                id TEXT PRIMARY KEY,
                mission_id TEXT,
                objective TEXT NOT NULL,
                status TEXT NOT NULL,
                plan TEXT NOT NULL DEFAULT '[]',
                synthesis TEXT,
                confidence TEXT,
                error TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_id TEXT NOT NULL,
                url TEXT NOT NULL,
                url_canonical TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                snippet TEXT NOT NULL DEFAULT '',
                tier INTEGER NOT NULL DEFAULT 3,
                query TEXT NOT NULL DEFAULT '',
                inspected INTEGER NOT NULL DEFAULT 0,
                inspected_at REAL,
                retrieval_error TEXT,
                content TEXT,
                created_at REAL NOT NULL,
                UNIQUE(research_id, url_canonical)
            );
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_id TEXT NOT NULL,
                source_id INTEGER NOT NULL,
                question_id INTEGER,
                excerpt TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_id TEXT NOT NULL,
                text TEXT NOT NULL,
                kind TEXT NOT NULL DEFAULT 'fact',
                verified INTEGER NOT NULL DEFAULT 0,
                confidence TEXT NOT NULL DEFAULT 'unknown',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS claim_evidence (
                claim_id INTEGER NOT NULL,
                evidence_id INTEGER NOT NULL,
                stance TEXT NOT NULL,
                created_at REAL NOT NULL,
                PRIMARY KEY (claim_id, evidence_id, stance)
            );
            CREATE TABLE IF NOT EXISTS unresolved (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_id TEXT NOT NULL,
                text TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                research_id TEXT NOT NULL,
                query TEXT NOT NULL,
                hits INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_src_research ON sources(research_id);
            CREATE INDEX IF NOT EXISTS idx_ev_research ON evidence(research_id);
            CREATE INDEX IF NOT EXISTS idx_claim_research ON claims(research_id);
            """
        )


# ---------------------------------------------------------------- jobs


def create_job(objective: str, *, mission_id: str = "") -> str:
    _init_db()
    rid = uuid.uuid4().hex[:12]
    now = time.time()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO research_jobs (id, mission_id, objective, status, created_at, updated_at)
               VALUES (?,?,?,?,?,?)""",
            (rid, mission_id, objective[:2000], PENDING, now, now),
        )
    return rid


def get_job(research_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM research_jobs WHERE id=?", (research_id,)).fetchone()
    if not row:
        return None
    data = dict(row)
    data["plan"] = json.loads(data.get("plan") or "[]")
    return data


def list_jobs(limit: int = 50) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM research_jobs ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["plan"] = json.loads(d.get("plan") or "[]")
        out.append(d)
    return out


def _update(research_id: str, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = time.time()
    sets = ", ".join(f"{k}=?" for k in fields)
    with _conn() as conn:
        conn.execute(f"UPDATE research_jobs SET {sets} WHERE id=?", (*fields.values(), research_id))


def set_status(research_id: str, status: str, *, error: str | None = None) -> None:
    _init_db()
    if error is not None:
        _update(research_id, status=status, error=error[:2000])
    else:
        _update(research_id, status=status)


def set_mission(research_id: str, mission_id: str) -> None:
    _init_db()
    _update(research_id, mission_id=mission_id)


def save_plan(research_id: str, plan: list[str]) -> None:
    _init_db()
    _update(research_id, plan=json.dumps(plan))


def save_synthesis(research_id: str, synthesis: str, confidence: str) -> None:
    _init_db()
    _update(research_id, synthesis=synthesis, confidence=confidence, status=COMPLETED)


# ---------------------------------------------------------------- questions


def add_question(research_id: str, text: str, seq: int) -> int:
    _init_db()
    with _conn() as conn:
        # Idempotent: re-running the planning phase must not duplicate questions.
        existing = conn.execute(
            "SELECT id FROM questions WHERE research_id=? AND seq=?", (research_id, seq)
        ).fetchone()
        if existing:
            return int(existing["id"])
        cur = conn.execute(
            "INSERT INTO questions (research_id, seq, text, created_at) VALUES (?,?,?,?)",
            (research_id, seq, text[:500], time.time()),
        )
        return int(cur.lastrowid)


def questions(research_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM questions WHERE research_id=? ORDER BY seq", (research_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- searches & sources


def record_search(research_id: str, query: str, hits: int, error: str = "") -> None:
    _init_db()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO searches (research_id, query, hits, error, created_at) VALUES (?,?,?,?,?)",
            (research_id, query[:400], hits, error[:500] or None, time.time()),
        )


def searches(research_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM searches WHERE research_id=? ORDER BY id", (research_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def add_source(
    research_id: str,
    url: str,
    *,
    title: str = "",
    snippet: str = "",
    tier: int = 3,
    query: str = "",
) -> int | None:
    """Insert a source, deduplicated by canonical URL. Returns id, or None if invalid."""
    _init_db()
    canon = canonical_url(url)
    if not canon:
        return None
    with _conn() as conn:
        existing = conn.execute(
            "SELECT id FROM sources WHERE research_id=? AND url_canonical=?", (research_id, canon)
        ).fetchone()
        if existing:
            return int(existing["id"])
        cur = conn.execute(
            """INSERT INTO sources (research_id, url, url_canonical, title, snippet, tier, query, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (research_id, url, canon, title[:400], snippet[:2000], tier, query[:400], time.time()),
        )
        return int(cur.lastrowid)


def sources(research_id: str, *, inspected_only: bool = False) -> list[dict[str, Any]]:
    _init_db()
    sql = "SELECT * FROM sources WHERE research_id=?"
    if inspected_only:
        sql += " AND inspected=1"
    sql += " ORDER BY tier ASC, id ASC"
    with _conn() as conn:
        rows = conn.execute(sql, (research_id,)).fetchall()
    return [dict(r) for r in rows]


def get_source(source_id: int) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM sources WHERE id=?", (source_id,)).fetchone()
    return dict(row) if row else None


def mark_inspected(source_id: int, content: str) -> None:
    """Record that a source really was retrieved, with what was retrieved."""
    _init_db()
    with _conn() as conn:
        conn.execute(
            "UPDATE sources SET inspected=1, inspected_at=?, content=?, retrieval_error=NULL WHERE id=?",
            (time.time(), content[:8000], source_id),
        )


def mark_retrieval_failed(source_id: int, error: str) -> None:
    """A source that could not be read is recorded as such — never as inspected."""
    _init_db()
    with _conn() as conn:
        conn.execute(
            "UPDATE sources SET inspected=0, retrieval_error=? WHERE id=?",
            (error[:500], source_id),
        )


# ---------------------------------------------------------------- evidence & claims


def add_evidence(
    research_id: str, source_id: int, excerpt: str, *, question_id: int | None = None
) -> int:
    _init_db()
    with _conn() as conn:
        cur = conn.execute(
            """INSERT INTO evidence (research_id, source_id, question_id, excerpt, created_at)
               VALUES (?,?,?,?,?)""",
            (research_id, source_id, question_id, excerpt[:4000], time.time()),
        )
        return int(cur.lastrowid)


def evidence(research_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM evidence WHERE research_id=? ORDER BY id", (research_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def add_claim(research_id: str, text: str, *, kind: str = FACT, confidence: str = "unknown") -> int:
    _init_db()
    with _conn() as conn:
        existing = conn.execute(
            "SELECT id FROM claims WHERE research_id=? AND text=?", (research_id, text[:1000])
        ).fetchone()
        if existing:
            return int(existing["id"])
        cur = conn.execute(
            "INSERT INTO claims (research_id, text, kind, confidence, created_at) VALUES (?,?,?,?,?)",
            (research_id, text[:1000], kind, confidence, time.time()),
        )
        return int(cur.lastrowid)


def link_evidence(claim_id: int, evidence_id: int, stance: str) -> None:
    if stance not in STANCES:
        raise ValueError(f"Unknown stance: {stance}")
    _init_db()
    with _conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO claim_evidence (claim_id, evidence_id, stance, created_at)
               VALUES (?,?,?,?)""",
            (claim_id, evidence_id, stance, time.time()),
        )


def set_claim_verdict(claim_id: int, *, verified: bool, confidence: str) -> None:
    _init_db()
    with _conn() as conn:
        conn.execute(
            "UPDATE claims SET verified=?, confidence=? WHERE id=?",
            (1 if verified else 0, confidence, claim_id),
        )


def claims(research_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM claims WHERE research_id=? ORDER BY id", (research_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def claim_evidence(claim_id: int) -> list[dict[str, Any]]:
    """Evidence rows attached to a claim, joined to their source for citation."""
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            """SELECT ce.stance, e.id AS evidence_id, e.excerpt,
                      s.id AS source_id, s.url, s.title, s.tier, s.inspected
               FROM claim_evidence ce
               JOIN evidence e ON e.id = ce.evidence_id
               JOIN sources  s ON s.id = e.source_id
               WHERE ce.claim_id=?
               ORDER BY ce.stance, e.id""",
            (claim_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_unresolved(research_id: str, text: str) -> None:
    _init_db()
    with _conn() as conn:
        existing = conn.execute(
            "SELECT id FROM unresolved WHERE research_id=? AND text=?", (research_id, text[:500])
        ).fetchone()
        if existing:
            return
        conn.execute(
            "INSERT INTO unresolved (research_id, text, created_at) VALUES (?,?,?)",
            (research_id, text[:500], time.time()),
        )


def unresolved(research_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM unresolved WHERE research_id=? ORDER BY id", (research_id,)
        ).fetchall()
    return [dict(r) for r in rows]
