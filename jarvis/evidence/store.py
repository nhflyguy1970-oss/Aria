"""Durable evidence model — sources, evidence, claims, relationships, verifications.

Lives in the same database as the research engine (research.db) rather than a
separate evidence.db, so ARIA has one authoritative evidence model. The
Milestone 4 research tables are untouched and remain readable; these tables
generalise the same concepts so evidence is usable outside research too —
every row is scoped by a free-form `context_id` (a research id, a
collaboration id, or a standalone context).

Source canonicalisation and quality tiering reuse the existing helpers rather
than reimplementing them.

The schema encodes the honesty rules the milestone requires. A source's access
state is what determines whether it was inspected — callers cannot assert it —
and evidence records the kind of material it came from, so a search snippet can
never be mistaken for a retrieved document.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from typing import Any
from urllib.parse import urlsplit

from jarvis.research.store import DB_PATH, canonical_url

_init_lock = threading.Lock()

# --- source access state: strictly ordered, and only the fetcher may raise it.
DISCOVERED = "discovered"  # seen in results; nothing retrieved
RETRIEVED = "retrieved"  # bytes fetched but not usable/parsed
INSPECTED = "inspected"  # content actually retrieved and readable
UNAVAILABLE = "unavailable"  # fetch attempted and failed
ACCESS_STATES = (DISCOVERED, RETRIEVED, INSPECTED, UNAVAILABLE)

# --- evidence kinds. A model assertion is never independent corroboration.
SNIPPET = "snippet"
FULL_TEXT = "full_text"
STRUCTURED = "structured"
MODEL_ASSERTION = "model_assertion"
EVIDENCE_TYPES = (SNIPPET, FULL_TEXT, STRUCTURED, MODEL_ASSERTION)

# --- claim ↔ evidence relationships.
SUPPORTS = "supports"
CONTRADICTS = "contradicts"
VERIFIES = "verifies"
WEAKENS = "weakens"
CONTEXTUALIZES = "contextualizes"
DERIVED_FROM = "derived_from"
SUPERSEDES = "supersedes"
RELATIONS = (SUPPORTS, CONTRADICTS, VERIFIES, WEAKENS, CONTEXTUALIZES, DERIVED_FROM, SUPERSEDES)

# --- claim lifecycle.
PROPOSED = "proposed"
SUPPORTED = "supported"
CONTRADICTED = "contradicted"
CONTESTED = "contested"
VERIFIED = "verified"
UNRESOLVED = "unresolved"
REJECTED = "rejected"
CLAIM_STATES = (PROPOSED, SUPPORTED, CONTRADICTED, CONTESTED, VERIFIED, UNRESOLVED, REJECTED)

# --- independence.
INDEPENDENT = "independent"
LIKELY_INDEPENDENT = "likely_independent"
NOT_INDEPENDENT = "not_independent"
UNKNOWN_INDEPENDENCE = "unknown"


class EvidenceError(ValueError):
    """An evidence operation violated the model's integrity rules."""


def domain_of(url: str) -> str:
    host = (urlsplit(url if "://" in (url or "") else f"https://{url or ''}").netloc or "").lower()
    return host[4:] if host.startswith("www.") else host


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=FULL")
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
    # The research engine owns this file's creation; ensure its schema exists
    # first so the two layers never race to create the database.
    from jarvis.research import store as research_store

    research_store._init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ev_claims'"
        ).fetchone()
        if row:
            return
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ev_sources (
                id TEXT PRIMARY KEY,
                context_id TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL,
                url_canonical TEXT NOT NULL,
                domain TEXT NOT NULL DEFAULT '',
                source_type TEXT NOT NULL DEFAULT 'web',
                title TEXT NOT NULL DEFAULT '',
                publisher TEXT NOT NULL DEFAULT '',
                published_at TEXT,
                retrieved_at REAL,
                access_state TEXT NOT NULL DEFAULT 'discovered',
                tier INTEGER NOT NULL DEFAULT 3,
                error TEXT,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                UNIQUE(context_id, url_canonical)
            );
            CREATE TABLE IF NOT EXISTS ev_claims (
                id TEXT PRIMARY KEY,
                context_id TEXT NOT NULL DEFAULT '',
                text TEXT NOT NULL,
                normalized TEXT NOT NULL DEFAULT '',
                origin TEXT NOT NULL DEFAULT 'agent',
                status TEXT NOT NULL DEFAULT 'proposed',
                confidence TEXT NOT NULL DEFAULT 'unknown',
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ev_evidence (
                id TEXT PRIMARY KEY,
                context_id TEXT NOT NULL DEFAULT '',
                source_id TEXT NOT NULL,
                claim_id TEXT,
                excerpt TEXT NOT NULL,
                evidence_type TEXT NOT NULL DEFAULT 'snippet',
                provenance TEXT NOT NULL DEFAULT '',
                inspected INTEGER NOT NULL DEFAULT 0,
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ev_links (
                claim_id TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                relation TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL,
                PRIMARY KEY (claim_id, evidence_id, relation)
            );
            CREATE TABLE IF NOT EXISTS ev_verifications (
                id TEXT PRIMARY KEY,
                claim_id TEXT NOT NULL,
                method TEXT NOT NULL,
                verifier TEXT NOT NULL DEFAULT '',
                result TEXT NOT NULL,
                confidence TEXT NOT NULL DEFAULT 'unknown',
                independent_sources INTEGER NOT NULL DEFAULT 0,
                independence TEXT NOT NULL DEFAULT 'unknown',
                explanation TEXT NOT NULL DEFAULT '',
                inputs TEXT NOT NULL DEFAULT '{}',
                model TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ev_conflicts (
                id TEXT PRIMARY KEY,
                claim_id TEXT NOT NULL,
                evidence_a TEXT NOT NULL,
                evidence_b TEXT NOT NULL,
                conflict_type TEXT NOT NULL DEFAULT 'contradiction',
                resolution TEXT NOT NULL DEFAULT 'unresolved',
                explanation TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ev_unresolved (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context_id TEXT NOT NULL DEFAULT '',
                claim_id TEXT,
                text TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_ev_src_ctx ON ev_sources(context_id);
            CREATE INDEX IF NOT EXISTS idx_ev_ev_ctx ON ev_evidence(context_id);
            CREATE INDEX IF NOT EXISTS idx_ev_claim_ctx ON ev_claims(context_id);
            CREATE INDEX IF NOT EXISTS idx_ev_ver_claim ON ev_verifications(claim_id, id);
            """
        )


def _row(row: sqlite3.Row | None, *json_fields: str) -> dict[str, Any] | None:
    if not row:
        return None
    d = dict(row)
    for f in json_fields:
        try:
            d[f] = json.loads(d.get(f) or "{}")
        except (TypeError, ValueError):
            d[f] = {}
    return d


def _nid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


# ------------------------------------------------------------------ sources


def add_source(
    url: str,
    *,
    context_id: str = "",
    title: str = "",
    publisher: str = "",
    published_at: str = "",
    source_type: str = "web",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Record a discovered source. Discovery is not retrieval."""
    _init_db()
    canon = canonical_url(url)
    if not canon:
        raise EvidenceError(f"Invalid source URL: {url!r}")
    try:
        from jarvis.research_verification import classify_source_tier

        tier = int(classify_source_tier(url, title, ""))
    except Exception:  # noqa: BLE001
        tier = 3
    with _conn() as conn:
        existing = conn.execute(
            "SELECT id FROM ev_sources WHERE context_id=? AND url_canonical=?", (context_id, canon)
        ).fetchone()
        if existing:
            return str(existing["id"])
        sid = _nid("src")
        conn.execute(
            """INSERT INTO ev_sources (id, context_id, url, url_canonical, domain, source_type,
                                       title, publisher, published_at, access_state, tier,
                                       metadata, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sid,
                context_id,
                url,
                canon,
                domain_of(url),
                source_type,
                title[:400],
                publisher[:200],
                published_at or None,
                DISCOVERED,
                tier,
                json.dumps(metadata or {}),
                time.time(),
            ),
        )
        return sid


def get_source(source_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        return _row(
            conn.execute("SELECT * FROM ev_sources WHERE id=?", (source_id,)).fetchone(), "metadata"
        )


def sources(context_id: str = "") -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM ev_sources WHERE context_id=? ORDER BY tier, created_at", (context_id,)
        ).fetchall()
    return [_row(r, "metadata") for r in rows]  # type: ignore[misc]


def mark_source_inspected(source_id: str, *, retrieved_at: float | None = None) -> None:
    """Only the retrieval path may call this — it asserts real inspection."""
    _init_db()
    with _conn() as conn:
        conn.execute(
            "UPDATE ev_sources SET access_state=?, retrieved_at=?, error=NULL WHERE id=?",
            (INSPECTED, retrieved_at or time.time(), source_id),
        )


def mark_source_unavailable(source_id: str, error: str) -> None:
    _init_db()
    with _conn() as conn:
        conn.execute(
            "UPDATE ev_sources SET access_state=?, error=? WHERE id=?",
            (UNAVAILABLE, error[:500], source_id),
        )


# ----------------------------------------------------------------- claims


def add_claim(
    text: str,
    *,
    context_id: str = "",
    origin: str = "agent",
    metadata: dict[str, Any] | None = None,
) -> str:
    _init_db()
    normalized = " ".join((text or "").lower().split()).rstrip("?.!")
    if not normalized:
        raise EvidenceError("A claim needs text")
    with _conn() as conn:
        existing = conn.execute(
            "SELECT id FROM ev_claims WHERE context_id=? AND normalized=?", (context_id, normalized)
        ).fetchone()
        if existing:
            return str(existing["id"])
        cid = _nid("clm")
        now = time.time()
        conn.execute(
            """INSERT INTO ev_claims (id, context_id, text, normalized, origin, status,
                                      metadata, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                cid,
                context_id,
                text[:2000],
                normalized[:2000],
                origin,
                PROPOSED,
                json.dumps(metadata or {}),
                now,
                now,
            ),
        )
        return cid


def get_claim(claim_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        return _row(
            conn.execute("SELECT * FROM ev_claims WHERE id=?", (claim_id,)).fetchone(), "metadata"
        )


def claims(context_id: str = "") -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM ev_claims WHERE context_id=? ORDER BY created_at", (context_id,)
        ).fetchall()
    return [_row(r, "metadata") for r in rows]  # type: ignore[misc]


def set_claim_state(claim_id: str, status: str, confidence: str) -> None:
    if status not in CLAIM_STATES:
        raise EvidenceError(f"Unknown claim status: {status}")
    _init_db()
    with _conn() as conn:
        conn.execute(
            "UPDATE ev_claims SET status=?, confidence=?, updated_at=? WHERE id=?",
            (status, confidence, time.time(), claim_id),
        )


# --------------------------------------------------------------- evidence


def add_evidence(
    source_id: str,
    excerpt: str,
    *,
    context_id: str = "",
    claim_id: str | None = None,
    evidence_type: str = SNIPPET,
    provenance: str = "",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Attach evidence to a real source.

    Evidence cannot exist without provenance: the source must already be
    recorded, and whether it counts as inspected is read from the source's
    access state rather than accepted from the caller.
    """
    _init_db()
    if evidence_type not in EVIDENCE_TYPES:
        raise EvidenceError(f"Unknown evidence type: {evidence_type}")
    if not (excerpt or "").strip():
        raise EvidenceError("Evidence needs an excerpt")
    source = get_source(source_id)
    if not source:
        raise EvidenceError(f"Evidence must reference a recorded source (got {source_id!r})")
    if source["access_state"] == UNAVAILABLE and evidence_type == FULL_TEXT:
        raise EvidenceError(
            "Cannot record full-text evidence from a source that could not be retrieved"
        )
    inspected = 1 if source["access_state"] == INSPECTED and evidence_type == FULL_TEXT else 0
    with _conn() as conn:
        eid = _nid("evd")
        conn.execute(
            """INSERT INTO ev_evidence (id, context_id, source_id, claim_id, excerpt,
                                        evidence_type, provenance, inspected, metadata, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                eid,
                context_id or source["context_id"],
                source_id,
                claim_id,
                excerpt[:4000],
                evidence_type,
                provenance or f"{source['access_state']}:{source['url']}",
                inspected,
                json.dumps(metadata or {}),
                time.time(),
            ),
        )
        return eid


def get_evidence(evidence_id: str) -> dict[str, Any] | None:
    _init_db()
    with _conn() as conn:
        return _row(
            conn.execute("SELECT * FROM ev_evidence WHERE id=?", (evidence_id,)).fetchone(),
            "metadata",
        )


def evidence(context_id: str = "") -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM ev_evidence WHERE context_id=? ORDER BY created_at", (context_id,)
        ).fetchall()
    return [_row(r, "metadata") for r in rows]  # type: ignore[misc]


def link(claim_id: str, evidence_id: str, relation: str, *, note: str = "") -> None:
    if relation not in RELATIONS:
        raise EvidenceError(f"Unknown relation: {relation}")
    _init_db()
    if not get_claim(claim_id):
        raise EvidenceError(f"No such claim: {claim_id}")
    if not get_evidence(evidence_id):
        raise EvidenceError(f"No such evidence: {evidence_id}")
    with _conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO ev_links (claim_id, evidence_id, relation, note, created_at)
               VALUES (?,?,?,?,?)""",
            (claim_id, evidence_id, relation, note[:500], time.time()),
        )


def claim_evidence(claim_id: str) -> list[dict[str, Any]]:
    """Evidence attached to a claim, joined to its source for provenance."""
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            """SELECT l.relation, l.note, e.id AS evidence_id, e.excerpt, e.evidence_type,
                      e.inspected, e.provenance,
                      s.id AS source_id, s.url, s.domain, s.title, s.tier, s.access_state
               FROM ev_links l
               JOIN ev_evidence e ON e.id = l.evidence_id
               JOIN ev_sources  s ON s.id = e.source_id
               WHERE l.claim_id=?
               ORDER BY l.relation, e.created_at""",
            (claim_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------- verifications/conflicts


def add_verification(
    claim_id: str,
    *,
    method: str,
    result: str,
    confidence: str,
    verifier: str = "",
    independent_sources: int = 0,
    independence: str = UNKNOWN_INDEPENDENCE,
    explanation: str = "",
    inputs: dict[str, Any] | None = None,
    model: str = "",
) -> str:
    _init_db()
    if not get_claim(claim_id):
        raise EvidenceError(f"No such claim: {claim_id}")
    with _conn() as conn:
        vid = _nid("ver")
        conn.execute(
            """INSERT INTO ev_verifications (id, claim_id, method, verifier, result, confidence,
                                             independent_sources, independence, explanation,
                                             inputs, model, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                vid,
                claim_id,
                method,
                verifier,
                result,
                confidence,
                independent_sources,
                independence,
                explanation[:2000],
                json.dumps(inputs or {}),
                model,
                time.time(),
            ),
        )
        return vid


def verifications(claim_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM ev_verifications WHERE claim_id=? ORDER BY created_at", (claim_id,)
        ).fetchall()
    return [_row(r, "inputs") for r in rows]  # type: ignore[misc]


def add_conflict(
    claim_id: str,
    evidence_a: str,
    evidence_b: str,
    *,
    conflict_type: str = "contradiction",
    explanation: str = "",
    resolution: str = "unresolved",
) -> str:
    _init_db()
    with _conn() as conn:
        existing = conn.execute(
            """SELECT id FROM ev_conflicts WHERE claim_id=? AND evidence_a=? AND evidence_b=?""",
            (claim_id, evidence_a, evidence_b),
        ).fetchone()
        if existing:
            return str(existing["id"])
        cid = _nid("cfl")
        conn.execute(
            """INSERT INTO ev_conflicts (id, claim_id, evidence_a, evidence_b, conflict_type,
                                         resolution, explanation, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                cid,
                claim_id,
                evidence_a,
                evidence_b,
                conflict_type,
                resolution,
                explanation[:1000],
                time.time(),
            ),
        )
        return cid


def conflicts(claim_id: str) -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM ev_conflicts WHERE claim_id=? ORDER BY created_at", (claim_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def add_unresolved(context_id: str, text: str, *, claim_id: str | None = None) -> None:
    _init_db()
    with _conn() as conn:
        existing = conn.execute(
            "SELECT id FROM ev_unresolved WHERE context_id=? AND text=?", (context_id, text[:500])
        ).fetchone()
        if existing:
            return
        conn.execute(
            "INSERT INTO ev_unresolved (context_id, claim_id, text, created_at) VALUES (?,?,?,?)",
            (context_id, claim_id, text[:500], time.time()),
        )


def unresolved(context_id: str = "") -> list[dict[str, Any]]:
    _init_db()
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM ev_unresolved WHERE context_id=? ORDER BY id", (context_id,)
        ).fetchall()
    return [dict(r) for r in rows]
