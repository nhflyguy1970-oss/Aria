"""Local SQLite Personal Health Record — private, on-disk only."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

HEALTH_DIR = DATA_DIR / "health_product"
DB_PATH = HEALTH_DIR / "health.db"
DOCS_DIR = HEALTH_DIR / "documents"

_lock = threading.RLock()
_SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS checkins (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    recorded_at REAL NOT NULL,
    payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_checkins_day ON checkins(day);
CREATE TABLE IF NOT EXISTS medications (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand_name TEXT,
    generic_name TEXT,
    strength TEXT,
    dose TEXT,
    units TEXT,
    frequency TEXT,
    purpose TEXT,
    physician TEXT,
    pharmacy TEXT,
    start_date TEXT,
    stop_date TEXT,
    status TEXT NOT NULL DEFAULT 'current',
    instructions TEXT,
    reason_discontinued TEXT,
    side_effects TEXT,
    notes TEXT,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS supplements (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    dose TEXT,
    frequency TEXT,
    purpose TEXT,
    start_date TEXT,
    stop_date TEXT,
    status TEXT NOT NULL DEFAULT 'current',
    notes TEXT,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS conditions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'condition',
    onset TEXT,
    resolved TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS allergies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'drug',
    reaction TEXT,
    notes TEXT,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS vitals (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    day TEXT NOT NULL,
    recorded_at REAL NOT NULL,
    value REAL,
    value2 REAL,
    units TEXT,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_vitals_kind_day ON vitals(kind, day);
CREATE TABLE IF NOT EXISTS labs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    day TEXT NOT NULL,
    recorded_at REAL NOT NULL,
    value REAL,
    value_text TEXT,
    units TEXT,
    ref_low REAL,
    ref_high REAL,
    physician TEXT,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_labs_name_day ON labs(name, day);
CREATE TABLE IF NOT EXISTS symptoms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    day TEXT NOT NULL,
    recorded_at REAL NOT NULL,
    severity REAL,
    notes TEXT,
    duration TEXT
);
CREATE TABLE IF NOT EXISTS vaccinations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    day TEXT,
    dose_number TEXT,
    notes TEXT,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT,
    path TEXT NOT NULL,
    day TEXT,
    extracted_text TEXT,
    notes TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS reminders (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    schedule TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    last_fired REAL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS medical_notes (
    id TEXT PRIMARY KEY,
    day TEXT,
    title TEXT,
    body TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    ts REAL NOT NULL,
    verb TEXT NOT NULL,
    detail TEXT
);
CREATE TABLE IF NOT EXISTS doctor_questions (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    created_at REAL NOT NULL,
    answered_at REAL,
    notes TEXT
);
CREATE TABLE IF NOT EXISTS pending_mutations (
    id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
);
CREATE TABLE IF NOT EXISTS consultations (
    id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    level TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    question TEXT NOT NULL,
    shared_json TEXT NOT NULL,
    response TEXT,
    approved INTEGER NOT NULL DEFAULT 0,
    stored INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'preview'
);
CREATE TABLE IF NOT EXISTS visits (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    title TEXT,
    physician TEXT,
    reason TEXT,
    summary TEXT,
    instructions TEXT,
    follow_up TEXT,
    questions_asked TEXT,
    questions_answered TEXT,
    next_appointment TEXT,
    document_ids TEXT,
    notes TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS missed_doses (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'medication',
    notes TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS dose_logs (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'medication',
    status TEXT NOT NULL DEFAULT 'taken',
    notes TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dose_logs_day ON dose_logs(day);
CREATE TABLE IF NOT EXISTS recovery_events (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT,
    body_part TEXT,
    pain REAL,
    mobility TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS milestones (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    detail TEXT,
    day TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT,
    start_time TEXT,
    end_time TEXT,
    duration_min REAL,
    intensity TEXT,
    calories REAL,
    distance REAL,
    distance_units TEXT,
    steps REAL,
    heart_rate REAL,
    notes TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_activities_day ON activities(day);
CREATE TABLE IF NOT EXISTS workouts (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    title TEXT,
    template TEXT,
    body_part TEXT,
    duration_min REAL,
    difficulty TEXT,
    pain REAL,
    notes TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_workouts_day ON workouts(day);
CREATE TABLE IF NOT EXISTS workout_sets (
    id TEXT PRIMARY KEY,
    workout_id TEXT NOT NULL,
    exercise TEXT NOT NULL,
    sets REAL,
    reps REAL,
    weight REAL,
    weight_units TEXT,
    band_color TEXT,
    resistance TEXT,
    time_sec REAL,
    rest_sec REAL,
    difficulty TEXT,
    pain REAL,
    notes TEXT,
    body_part TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_workout_sets_wid ON workout_sets(workout_id);
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    target_value REAL,
    target_unit TEXT,
    per_week REAL,
    start_date TEXT,
    deadline TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS health_journal (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    body TEXT NOT NULL,
    mood TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS knowledge (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT,
    url TEXT,
    body TEXT,
    tags TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS providers (
    id TEXT PRIMARY KEY,
    specialty TEXT NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    last_visit TEXT,
    next_visit TEXT,
    notes TEXT,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS procedures (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT,
    day TEXT,
    location TEXT,
    provider TEXT,
    result TEXT,
    follow_up TEXT,
    document_id TEXT,
    notes TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS family_history (
    id TEXT PRIMARY KEY,
    relation TEXT NOT NULL,
    relation_side TEXT,
    display_name TEXT,
    condition TEXT NOT NULL,
    condition_category TEXT,
    hereditary INTEGER NOT NULL DEFAULT 0,
    age_at_diagnosis TEXT,
    living INTEGER,
    age_now TEXT,
    age_at_death TEXT,
    cause_of_death TEXT,
    notes TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    person_id TEXT,
    source_system TEXT,
    external_id TEXT,
    device_id TEXT,
    provenance TEXT,
    provenance_detail TEXT,
    recorded_by TEXT,
    confidence TEXT,
    confirmed INTEGER NOT NULL DEFAULT 0,
    confirmed_at REAL
);
CREATE INDEX IF NOT EXISTS idx_family_relation ON family_history(relation_side, relation);
CREATE TABLE IF NOT EXISTS preventive_care (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT,
    category TEXT,
    interval_months REAL,
    last_done TEXT,
    next_due TEXT,
    scheduled_for TEXT,
    physician TEXT,
    facility TEXT,
    result TEXT,
    result_day TEXT,
    status TEXT NOT NULL DEFAULT 'planned',
    document_id TEXT,
    reminder_id TEXT,
    source_kind TEXT NOT NULL DEFAULT 'user',
    notes TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    person_id TEXT,
    source_system TEXT,
    external_id TEXT,
    device_id TEXT,
    provenance TEXT,
    provenance_detail TEXT,
    recorded_by TEXT,
    confidence TEXT,
    confirmed INTEGER NOT NULL DEFAULT 0,
    confirmed_at REAL
);
CREATE INDEX IF NOT EXISTS idx_preventive_due ON preventive_care(status, next_due);
CREATE TABLE IF NOT EXISTS nutrition_log (
    id TEXT PRIMARY KEY,
    day TEXT NOT NULL,
    recorded_at REAL NOT NULL,
    kind TEXT NOT NULL,
    meal_slot TEXT,
    description TEXT NOT NULL,
    items TEXT,
    quantity REAL,
    units TEXT,
    tags TEXT,
    notes TEXT,
    created_at REAL NOT NULL,
    person_id TEXT,
    source_system TEXT,
    external_id TEXT,
    device_id TEXT,
    provenance TEXT,
    provenance_detail TEXT,
    recorded_by TEXT,
    confidence TEXT,
    confirmed INTEGER NOT NULL DEFAULT 0,
    confirmed_at REAL
);
CREATE INDEX IF NOT EXISTS idx_nutrition_day ON nutrition_log(day);
CREATE TABLE IF NOT EXISTS health_observations (
    id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    last_seen REAL NOT NULL,
    day TEXT NOT NULL,
    kind TEXT NOT NULL,
    topic TEXT NOT NULL,
    statement TEXT NOT NULL,
    evidence TEXT,
    strength TEXT,
    window_days REAL,
    sample_size REAL,
    educational INTEGER NOT NULL DEFAULT 1,
    dismissed INTEGER NOT NULL DEFAULT 0,
    person_id TEXT,
    source_system TEXT,
    external_id TEXT,
    device_id TEXT,
    provenance TEXT,
    provenance_detail TEXT,
    recorded_by TEXT,
    confidence TEXT,
    confirmed INTEGER NOT NULL DEFAULT 0,
    confirmed_at REAL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_obs_topic ON health_observations(kind, topic);
CREATE TABLE IF NOT EXISTS backups (
    id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    path TEXT NOT NULL,
    filename TEXT NOT NULL,
    format TEXT NOT NULL DEFAULT 'jarvis-health-v1',
    encrypted INTEGER NOT NULL DEFAULT 1,
    size_bytes REAL,
    sha256 TEXT NOT NULL,
    record_counts TEXT,
    schema_version REAL,
    app_version TEXT,
    kind TEXT NOT NULL DEFAULT 'manual',
    verified_at REAL,
    verify_status TEXT,
    restored_at REAL,
    notes TEXT
);
CREATE TABLE IF NOT EXISTS restore_log (
    id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    backup_id TEXT,
    source_path TEXT,
    mode TEXT NOT NULL,
    confirmed INTEGER NOT NULL DEFAULT 0,
    safety_backup_id TEXT,
    tables_written TEXT,
    rows_written REAL,
    status TEXT NOT NULL,
    message TEXT
);
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

_COMPAT_COLUMNS = {
    "person_id": "TEXT",
    "source_system": "TEXT",
    "external_id": "TEXT",
    "device_id": "TEXT",
}
_PROVENANCE_COLUMNS = {
    "provenance": "TEXT",
    "provenance_detail": "TEXT",
    "recorded_by": "TEXT",
    "confidence": "TEXT",
    "confirmed": "INTEGER DEFAULT 0",
    "confirmed_at": "REAL",
}
_LEGACY_ADDITIONS: dict[str, dict[str, str]] = {
    "reminders": {"last_fired": "REAL"},
    "visits": {
        "reason": "TEXT",
        "summary": "TEXT",
        "instructions": "TEXT",
        "follow_up": "TEXT",
        "questions_asked": "TEXT",
        "questions_answered": "TEXT",
        "next_appointment": "TEXT",
        "document_ids": "TEXT",
    },
}
_METADATA_TABLES = (
    "medications",
    "supplements",
    "conditions",
    "allergies",
    "vitals",
    "labs",
    "symptoms",
    "vaccinations",
    "documents",
    "medical_notes",
    "visits",
    "procedures",
    "providers",
    "activities",
    "workouts",
    "goals",
    "health_journal",
    "dose_logs",
    "missed_doses",
    "recovery_events",
    "reminders",
    "milestones",
    "knowledge",
    "doctor_questions",
    "consultations",
    "family_history",
    "preventive_care",
    "nutrition_log",
    "health_observations",
)
_MIGRATED: dict[str, bool] = {}
SCHEMA_VERSION = "4"


def _today() -> str:
    return date.today().isoformat()


def _now() -> float:
    return time.time()


def _nid(prefix: str = "h") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def ensure_dirs() -> None:
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (HEALTH_DIR / "backups").mkdir(parents=True, exist_ok=True)


def _migrate(conn: sqlite3.Connection) -> None:
    key = str(Path(DB_PATH).resolve())
    if _MIGRATED.get(key):
        return
    for table, additions in _LEGACY_ADDITIONS.items():
        try:
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        except sqlite3.Error:
            continue
        for col, decl in additions.items():
            if col not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
    for table in _METADATA_TABLES:
        try:
            cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        except sqlite3.Error:
            continue
        if not cols:
            continue
        for col, decl in {**_COMPAT_COLUMNS, **_PROVENANCE_COLUMNS}.items():
            if col not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
    conn.execute(
        "INSERT INTO schema_meta(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        ("schema_version", SCHEMA_VERSION),
    )
    conn.commit()
    _MIGRATED[key] = True
    try:
        from jarvis.health_product.provenance import clear_column_cache

        clear_column_cache()
    except Exception:
        pass


def connect() -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    _migrate(conn)
    return conn


def reset_migration_cache() -> None:
    _MIGRATED.clear()
    try:
        from jarvis.health_product.provenance import clear_column_cache

        clear_column_cache()
    except Exception:
        pass


def _row(r: sqlite3.Row | None) -> dict[str, Any] | None:
    if r is None:
        return None
    return {k: r[k] for k in r.keys()}


def _rows(cur: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [{k: r[k] for k in r.keys()} for r in cur.fetchall()]


def log_event(verb: str, detail: str = "") -> None:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO events(id, ts, verb, detail) VALUES (?,?,?,?)",
                (_nid("evt"), _now(), verb, detail[:2000]),
            )
            conn.commit()
        finally:
            conn.close()


def get_profile() -> dict[str, Any]:
    with _lock:
        conn = connect()
        try:
            cur = conn.execute("SELECT key, value FROM profile")
            out: dict[str, Any] = {}
            for r in cur.fetchall():
                try:
                    out[r["key"]] = json.loads(r["value"])
                except Exception:
                    out[r["key"]] = r["value"]
            return out
        finally:
            conn.close()


def set_profile(updates: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    with _lock:
        conn = connect()
        try:
            for key, value in (updates or {}).items():
                conn.execute(
                    "INSERT INTO profile(key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (str(key), json.dumps(value)),
                )
            conn.commit()
        finally:
            conn.close()
    log_event("profile_update", ",".join((updates or {}).keys()))
    return get_profile()


def upsert_checkin(payload: dict[str, Any], day: str | None = None) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    from jarvis.production_guard import ProductionIsolationError, assert_owner_write_allowed

    try:
        blob = " ".join(str(payload.get(k) or "") for k in ("mood", "note", "notes", "source", "id"))
        assert_owner_write_allowed(blob, store="health")
    except ProductionIsolationError as exc:
        raise ValueError(str(exc)) from exc
    day = day or payload.get("day") or _today()
    payload = {**payload, "day": day}
    cid = payload.get("id") or _nid("chk")
    payload["id"] = cid
    with _lock:
        conn = connect()
        try:
            existing = conn.execute("SELECT id, payload FROM checkins WHERE day=?", (day,)).fetchone()
            if existing and not payload.get("force_new"):
                cid = existing["id"]
                prev = json.loads(existing["payload"])
                prev.update({k: v for k, v in payload.items() if v is not None and k != "force_new"})
                prev["id"] = cid
                prev["day"] = day
                conn.execute(
                    "UPDATE checkins SET recorded_at=?, payload=? WHERE id=?",
                    (_now(), json.dumps(prev), cid),
                )
                payload = prev
            else:
                conn.execute(
                    "INSERT INTO checkins(id, day, recorded_at, payload) VALUES (?,?,?,?)",
                    (cid, day, _now(), json.dumps(payload)),
                )
            conn.commit()
        finally:
            conn.close()
    log_event("checkin", day)
    return payload


def get_checkin(day: str | None = None) -> dict[str, Any] | None:
    day = day or _today()
    with _lock:
        conn = connect()
        try:
            r = conn.execute("SELECT payload FROM checkins WHERE day=?", (day,)).fetchone()
            return json.loads(r["payload"]) if r else None
        finally:
            conn.close()


def list_checkins(limit: int | None = 90, since: str | None = None) -> list[dict[str, Any]]:
    with _lock:
        conn = connect()
        try:
            if since and limit is not None:
                cur = conn.execute(
                    "SELECT payload FROM checkins WHERE day>=? ORDER BY day DESC LIMIT ?",
                    (since, limit),
                )
            elif since:
                cur = conn.execute(
                    "SELECT payload FROM checkins WHERE day>=? ORDER BY day DESC",
                    (since,),
                )
            elif limit is not None:
                cur = conn.execute("SELECT payload FROM checkins ORDER BY day DESC LIMIT ?", (limit,))
            else:
                cur = conn.execute("SELECT payload FROM checkins ORDER BY day DESC")
            return [json.loads(r["payload"]) for r in cur.fetchall()]
        finally:
            conn.close()


def _upsert_named(table: str, record: dict[str, Any], name_key: str = "name") -> dict[str, Any]:
    from jarvis.health_product.provenance import stamp
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    cols_now = table_columns_safe(table)
    rec = stamp(
        dict(record),
        table,
        source=str(record.get("provenance") or "manual"),
        confidence=str(record.get("confidence") or "user_entered"),
    )
    rec.setdefault("id", _nid(table[:3]))
    if "updated_at" in cols_now:
        rec["updated_at"] = _now()
    cols = [c for c in rec.keys() if c in cols_now]
    if "id" not in cols:
        cols.insert(0, "id")
    with _lock:
        conn = connect()
        try:
            placeholders = ",".join("?" for _ in cols)
            assignments = ",".join(f"{c}=excluded.{c}" for c in cols if c != "id")
            conn.execute(
                f"INSERT INTO {table}({','.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(id) DO UPDATE SET {assignments}",
                [rec.get(c) for c in cols],
            )
            conn.commit()
        finally:
            conn.close()
    log_event(f"{table}_upsert", str(rec.get(name_key) or rec.get("id")))
    return {k: rec.get(k) for k in cols}


def table_columns_safe(table: str) -> set[str]:
    with _lock:
        conn = connect()
        try:
            return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        finally:
            conn.close()


_ORDER_DEFAULTS = {
    "checkins": "day DESC",
    "vitals": "recorded_at DESC",
    "labs": "recorded_at DESC",
    "symptoms": "recorded_at DESC",
    "documents": "created_at DESC",
    "medical_notes": "created_at DESC",
    "events": "ts DESC",
    "doctor_questions": "created_at DESC",
    "pending_mutations": "created_at DESC",
    "consultations": "created_at DESC",
    "visits": "created_at DESC",
    "missed_doses": "created_at DESC",
    "dose_logs": "created_at DESC",
    "recovery_events": "created_at DESC",
    "milestones": "created_at DESC",
    "activities": "day DESC, created_at DESC",
    "workouts": "day DESC, created_at DESC",
    "workout_sets": "created_at DESC",
    "goals": "updated_at DESC",
    "health_journal": "created_at DESC",
    "knowledge": "created_at DESC",
    "providers": "updated_at DESC",
    "procedures": "day DESC, created_at DESC",
    "family_history": "updated_at DESC",
    "preventive_care": "CASE WHEN next_due IS NULL THEN 1 ELSE 0 END, next_due ASC",
    "nutrition_log": "day DESC, recorded_at DESC",
    "health_observations": "created_at DESC",
    "backups": "created_at DESC",
    "restore_log": "created_at DESC",
}


def list_table(table: str, where: str = "", args: tuple = (), order: str | None = None, limit: int | None = 200) -> list[dict[str, Any]]:
    """List rows. limit=None returns the full table (used by lifelong backup export)."""
    if order is None:
        order = _ORDER_DEFAULTS.get(table, "updated_at DESC")
    sql = f"SELECT * FROM {table}"
    if where:
        sql += f" WHERE {where}"
    if order:
        sql += f" ORDER BY {order}"
    params: tuple = args
    if limit is not None:
        sql += " LIMIT ?"
        params = (*args, int(limit))
    with _lock:
        conn = connect()
        try:
            cur = conn.execute(sql, params)
            return _rows(cur)
        finally:
            conn.close()


def get_by_id(table: str, item_id: str) -> dict[str, Any] | None:
    with _lock:
        conn = connect()
        try:
            return _row(conn.execute(f"SELECT * FROM {table} WHERE id=?", (item_id,)).fetchone())
        finally:
            conn.close()


def delete_by_id(table: str, item_id: str, *, force: bool = False, log: bool = True) -> bool:
    from jarvis.health_product.trust import assert_writable

    assert_writable(force=force)
    with _lock:
        conn = connect()
        try:
            cur = conn.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
            conn.commit()
            ok = cur.rowcount > 0
        finally:
            conn.close()
    if ok and log:
        log_event(f"{table}_delete", item_id)
    return ok


# Accidental smoke/probe rows previously written to the live PHR (confirmed=0, empty provenance).
_KNOWN_SMOKE_ROWS: tuple[tuple[str, str], ...] = (
    ("medications", "med_4fb5c51e93eb"),  # Metformin smoke insert
    ("supplements", "sup_ea51d50be3d8"),  # Vitamin D smoke insert
    ("vitals", "vit_010862cfa7b8"),  # blood_sugar 121 smoke
    ("checkins", "chk_d0784dcf3bb5"),
    ("events", "evt_c1c4930a4788"),
    ("events", "evt_72a22992f833"),
    ("events", "evt_c5c9c5cd90ee"),
    ("events", "evt_09aa3a0e12f8"),
    # Phase 1 contamination audit — unambiguous certification fixtures (2026-08-06)
    ("dose_logs", "dose_c56a12f7c65d"),  # P64TestMed
    ("dose_logs", "dose_b8a263128a02"),  # P64TestMed
    ("dose_logs", "dose_485bf519628d"),  # P64Verify
    ("events", "evt_1024900f073d"),  # taken:P64TestMed
    ("events", "evt_eb2b7df6ed7a"),
    ("events", "evt_549763ad97b6"),  # taken:P64Verify
    ("checkins", "chk_0a4c1c12b45a"),  # cert-mood / oc-direct
    ("vitals", "vit_599cf301f7bc"),  # blood_sugar attached to cert-mood
    ("vitals", "vit_f1b9db928816"),
)


def purge_known_smoke_records(*, force: bool = False) -> dict[str, Any]:
    """Remove only known QA/smoke rows from the PHR. Never deletes other rows."""
    from jarvis.health_product.trust import assert_writable

    assert_writable(force=force)
    removed: list[dict[str, str]] = []
    for table, item_id in _KNOWN_SMOKE_ROWS:
        if delete_by_id(table, item_id, force=force, log=False):
            removed.append({"table": table, "id": item_id})
    return {"ok": True, "removed": removed, "count": len(removed)}


def upsert_medication(rec: dict[str, Any]) -> dict[str, Any]:
    rec.setdefault("status", "current")
    return _upsert_named("medications", rec)


def upsert_supplement(rec: dict[str, Any]) -> dict[str, Any]:
    rec.setdefault("status", "current")
    return _upsert_named("supplements", rec)


def upsert_condition(rec: dict[str, Any]) -> dict[str, Any]:
    rec.setdefault("status", "active")
    rec.setdefault("kind", "condition")
    return _upsert_named("conditions", rec)


def upsert_allergy(rec: dict[str, Any]) -> dict[str, Any]:
    rec.setdefault("kind", "drug")
    return _upsert_named("allergies", rec)


def add_vital(kind: str, value: float | None, *, value2: float | None = None, units: str = "", notes: str = "", day: str | None = None) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    rec = {
        "id": _nid("vit"),
        "kind": kind,
        "day": day or _today(),
        "recorded_at": _now(),
        "value": value,
        "value2": value2,
        "units": units,
        "notes": notes,
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO vitals(id,kind,day,recorded_at,value,value2,units,notes) VALUES (?,?,?,?,?,?,?,?)",
                (rec["id"], rec["kind"], rec["day"], rec["recorded_at"], rec["value"], rec["value2"], rec["units"], rec["notes"]),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("vital", f"{kind}={value}")
    return rec


def list_vitals(kind: str | None = None, since: str | None = None, limit: int | None = 365) -> list[dict[str, Any]]:
    """List vitals. When capped without `since`, return the most recent rows (not the oldest)."""
    where = []
    args: list[Any] = []
    if kind:
        where.append("kind=?")
        args.append(kind)
    if since:
        where.append("day>=?")
        args.append(since)
        order = "day ASC, recorded_at ASC"
        return list_table("vitals", " AND ".join(where), tuple(args), order=order, limit=limit)
    # Capped lifelong reads must prefer recent history — ASC+LIMIT silently kept decade-old rows.
    if limit is None:
        return list_table("vitals", " AND ".join(where), tuple(args), order="day ASC, recorded_at ASC", limit=None)
    recent = list_table(
        "vitals",
        " AND ".join(where),
        tuple(args),
        order="day DESC, recorded_at DESC",
        limit=limit,
    )
    return list(reversed(recent))


def add_lab(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    rec = {
        "id": rec.get("id") or _nid("lab"),
        "name": rec["name"],
        "day": rec.get("day") or _today(),
        "recorded_at": rec.get("recorded_at") or _now(),
        "value": rec.get("value"),
        "value_text": rec.get("value_text") or "",
        "units": rec.get("units") or "",
        "ref_low": rec.get("ref_low"),
        "ref_high": rec.get("ref_high"),
        "physician": rec.get("physician") or "",
        "notes": rec.get("notes") or "",
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO labs(id,name,day,recorded_at,value,value_text,units,ref_low,ref_high,physician,notes) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    rec["id"],
                    rec["name"],
                    rec["day"],
                    rec["recorded_at"],
                    rec["value"],
                    rec["value_text"],
                    rec["units"],
                    rec["ref_low"],
                    rec["ref_high"],
                    rec["physician"],
                    rec["notes"],
                ),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("lab", f"{rec['name']}={rec.get('value') or rec.get('value_text')}")
    return rec


def list_labs(name: str | None = None, since: str | None = None, limit: int | None = 200) -> list[dict[str, Any]]:
    where = []
    args: list[Any] = []
    if name:
        where.append("lower(name)=?")
        args.append(name.lower())
    if since:
        where.append("day>=?")
        args.append(since)
        return list_table("labs", " AND ".join(where), tuple(args), order="day ASC, recorded_at ASC", limit=limit)
    if limit is None:
        return list_table("labs", " AND ".join(where), tuple(args), order="day ASC, recorded_at ASC", limit=None)
    recent = list_table(
        "labs",
        " AND ".join(where),
        tuple(args),
        order="day DESC, recorded_at DESC",
        limit=limit,
    )
    return list(reversed(recent))


def add_symptom(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    rec = {
        "id": rec.get("id") or _nid("sym"),
        "name": rec["name"],
        "day": rec.get("day") or _today(),
        "recorded_at": rec.get("recorded_at") or _now(),
        "severity": rec.get("severity"),
        "notes": rec.get("notes") or "",
        "duration": rec.get("duration") or "",
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO symptoms(id,name,day,recorded_at,severity,notes,duration) VALUES (?,?,?,?,?,?,?)",
                (rec["id"], rec["name"], rec["day"], rec["recorded_at"], rec["severity"], rec["notes"], rec["duration"]),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("symptom", rec["name"])
    return rec


def upsert_vaccination(rec: dict[str, Any]) -> dict[str, Any]:
    return _upsert_named("vaccinations", rec)


def add_document(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    rec = {
        "id": rec.get("id") or _nid("doc"),
        "title": rec.get("title") or Path(rec.get("path") or "document").name,
        "kind": rec.get("kind") or "document",
        "path": rec["path"],
        "day": rec.get("day") or _today(),
        "extracted_text": rec.get("extracted_text") or "",
        "notes": rec.get("notes") or "",
        "created_at": rec.get("created_at") or _now(),
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO documents(id,title,kind,path,day,extracted_text,notes,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (
                    rec["id"],
                    rec["title"],
                    rec["kind"],
                    rec["path"],
                    rec["day"],
                    rec["extracted_text"],
                    rec["notes"],
                    rec["created_at"],
                ),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("document", rec["title"])
    return rec


def upsert_reminder(rec: dict[str, Any]) -> dict[str, Any]:
    rec.setdefault("enabled", 1)
    return _upsert_named("reminders", rec, name_key="title")


def add_note(title: str, body: str, day: str | None = None) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    rec = {
        "id": _nid("note"),
        "day": day or _today(),
        "title": title or "",
        "body": body,
        "created_at": _now(),
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO medical_notes(id,day,title,body,created_at) VALUES (?,?,?,?,?)",
                (rec["id"], rec["day"], rec["title"], rec["body"], rec["created_at"]),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("note", rec["title"] or rec["id"])
    return rec


def search_all(query: str, limit: int = 40) -> list[dict[str, Any]]:
    q = f"%{(query or '').strip().lower()}%"
    if q == "%%":
        return []
    hits: list[dict[str, Any]] = []
    with _lock:
        conn = connect()
        try:
            for table, fields, title_field in (
                ("medications", "name,brand_name,generic_name,purpose,notes,physician", "name"),
                ("supplements", "name,purpose,notes", "name"),
                ("conditions", "name,notes,kind", "name"),
                ("allergies", "name,reaction,notes,kind", "name"),
                ("labs", "name,notes,physician,value_text", "name"),
                ("symptoms", "name,notes", "name"),
                ("vaccinations", "name,notes", "name"),
                ("documents", "title,kind,extracted_text,notes", "title"),
                ("medical_notes", "title,body", "title"),
                ("reminders", "title,kind,notes", "title"),
                ("doctor_questions", "text,notes,status", "text"),
                ("consultations", "question,response,provider,model", "question"),
                ("visits", "title,physician,notes,reason,summary,instructions,follow_up,questions_asked,questions_answered", "title"),
                ("dose_logs", "name,kind,status,notes", "name"),
                ("recovery_events", "title,kind,body_part,notes,mobility,status", "title"),
                ("milestones", "title,detail,key", "title"),
                ("activities", "kind,title,notes", "title"),
                ("workouts", "title,template,body_part,notes", "title"),
                ("workout_sets", "exercise,notes,body_part,band_color", "exercise"),
                ("goals", "title,kind,notes", "title"),
                ("health_journal", "body,mood", "body"),
                ("knowledge", "title,source,body,tags,url", "title"),
                ("providers", "name,specialty,notes,phone,email,address", "name"),
                ("procedures", "name,kind,location,provider,result,notes", "name"),
                ("family_history", "relation,relation_side,display_name,condition,condition_category,cause_of_death,notes", "condition"),
                ("preventive_care", "name,slug,category,physician,facility,result,notes,status", "name"),
                ("nutrition_log", "description,kind,meal_slot,notes,tags,items", "description"),
                ("health_observations", "topic,statement,kind,strength", "topic"),
            ):
                where = " OR ".join(f"lower(coalesce({f},'')) LIKE ?" for f in fields.split(","))
                args = tuple(q for _ in fields.split(","))
                cur = conn.execute(f"SELECT * FROM {table} WHERE {where} LIMIT ?", (*args, max(5, limit // 4)))
                for r in cur.fetchall():
                    row = {k: r[k] for k in r.keys()}
                    hits.append({"source": table, "title": row.get(title_field) or row.get("id"), "record": row})
            cur = conn.execute("SELECT day, payload FROM checkins ORDER BY day DESC LIMIT 120")
            needle = (query or "").strip().lower()
            for r in cur.fetchall():
                blob = (r["payload"] or "").lower()
                if needle in blob:
                    hits.append({"source": "checkins", "title": f"Check-in {r['day']}", "record": json.loads(r["payload"])})
        finally:
            conn.close()
    return hits[:limit]


def find_medication(name: str) -> dict[str, Any] | None:
    needle = (name or "").strip().lower()
    if not needle:
        return None
    with _lock:
        conn = connect()
        try:
            r = conn.execute(
                "SELECT * FROM medications WHERE lower(name)=? OR lower(coalesce(brand_name,''))=? "
                "OR lower(coalesce(generic_name,''))=? ORDER BY updated_at DESC LIMIT 1",
                (needle, needle, needle),
            ).fetchone()
            if r:
                return _row(r)
            r = conn.execute(
                "SELECT * FROM medications WHERE lower(name) LIKE ? OR lower(coalesce(brand_name,'')) LIKE ? "
                "OR lower(coalesce(generic_name,'')) LIKE ? ORDER BY updated_at DESC LIMIT 1",
                (f"%{needle}%", f"%{needle}%", f"%{needle}%"),
            ).fetchone()
            return _row(r)
        finally:
            conn.close()


def find_supplement(name: str) -> dict[str, Any] | None:
    needle = (name or "").strip().lower()
    if not needle:
        return None
    with _lock:
        conn = connect()
        try:
            r = conn.execute(
                "SELECT * FROM supplements WHERE lower(name)=? OR lower(name) LIKE ? ORDER BY updated_at DESC LIMIT 1",
                (needle, f"%{needle}%"),
            ).fetchone()
            return _row(r)
        finally:
            conn.close()


def add_doctor_question(text: str, notes: str = "") -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    rec = {"id": _nid("q"), "text": text.strip(), "status": "open", "created_at": _now(), "answered_at": None, "notes": notes}
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO doctor_questions(id,text,status,created_at,answered_at,notes) VALUES (?,?,?,?,?,?)",
                (rec["id"], rec["text"], rec["status"], rec["created_at"], rec["answered_at"], rec["notes"]),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("doctor_question", rec["text"][:200])
    return rec


def set_doctor_question_status(item_id: str, status: str, notes: str = "") -> dict[str, Any] | None:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    rec = get_by_id("doctor_questions", item_id)
    if not rec:
        return None
    rec["status"] = status
    rec["notes"] = notes or rec.get("notes") or ""
    rec["answered_at"] = _now() if status == "answered" else rec.get("answered_at")
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "UPDATE doctor_questions SET status=?, notes=?, answered_at=? WHERE id=?",
                (rec["status"], rec["notes"], rec["answered_at"], item_id),
            )
            conn.commit()
        finally:
            conn.close()
    return rec


def add_pending_mutation(kind: str, summary: str, payload: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    rec = {
        "id": _nid("pend"),
        "created_at": _now(),
        "kind": kind,
        "summary": summary,
        "payload": json.dumps(payload),
        "status": "pending",
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO pending_mutations(id,created_at,kind,summary,payload,status) VALUES (?,?,?,?,?,?)",
                (rec["id"], rec["created_at"], rec["kind"], rec["summary"], rec["payload"], rec["status"]),
            )
            conn.commit()
        finally:
            conn.close()
    return rec


def latest_pending() -> dict[str, Any] | None:
    rows = list_table("pending_mutations", "status=?", ("pending",), order="created_at DESC", limit=1)
    if not rows:
        return None
    row = rows[0]
    try:
        row["payload_obj"] = json.loads(row.get("payload") or "{}")
    except Exception:
        row["payload_obj"] = {}
    return row


def set_pending_status(item_id: str, status: str) -> dict[str, Any] | None:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    rec = get_by_id("pending_mutations", item_id)
    if not rec:
        return None
    with _lock:
        conn = connect()
        try:
            conn.execute("UPDATE pending_mutations SET status=? WHERE id=?", (status, item_id))
            conn.commit()
        finally:
            conn.close()
    rec["status"] = status
    try:
        rec["payload_obj"] = json.loads(rec.get("payload") or "{}")
    except Exception:
        rec["payload_obj"] = {}
    return rec


def add_consultation(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {
        "id": rec.get("id") or _nid("con"),
        "created_at": rec.get("created_at") or _now(),
        "level": rec.get("level") or "local_only",
        "provider": rec.get("provider") or "",
        "model": rec.get("model") or "",
        "question": rec.get("question") or "",
        "shared_json": rec.get("shared_json")
        if isinstance(rec.get("shared_json"), str)
        else json.dumps(rec.get("shared") or rec.get("shared_json") or {}),
        "response": rec.get("response") or "",
        "approved": 1 if rec.get("approved") else 0,
        "stored": 1 if rec.get("stored") else 0,
        "status": rec.get("status") or "preview",
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO consultations(id,created_at,level,provider,model,question,shared_json,response,approved,stored,status) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    row["id"],
                    row["created_at"],
                    row["level"],
                    row["provider"],
                    row["model"],
                    row["question"],
                    row["shared_json"],
                    row["response"],
                    row["approved"],
                    row["stored"],
                    row["status"],
                ),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("consultation", f"{row['level']}:{row['status']}")
    return row


def update_consultation(item_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    rec = get_by_id("consultations", item_id)
    if not rec:
        return None
    rec.update({k: v for k, v in updates.items() if v is not None})
    if "shared" in updates and "shared_json" not in updates:
        rec["shared_json"] = json.dumps(updates["shared"])
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "UPDATE consultations SET level=?, provider=?, model=?, question=?, shared_json=?, response=?, approved=?, stored=?, status=? WHERE id=?",
                (
                    rec.get("level"),
                    rec.get("provider") or "",
                    rec.get("model") or "",
                    rec.get("question") or "",
                    rec.get("shared_json") or "{}",
                    rec.get("response") or "",
                    int(rec.get("approved") or 0),
                    int(rec.get("stored") or 0),
                    rec.get("status") or "preview",
                    item_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    return rec


def add_visit(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {
        "id": rec.get("id") or _nid("vis"),
        "day": rec.get("day") or _today(),
        "title": rec.get("title") or rec.get("reason") or "Doctor visit",
        "physician": rec.get("physician") or rec.get("provider") or "",
        "reason": rec.get("reason") or "",
        "summary": rec.get("summary") or "",
        "instructions": rec.get("instructions") or "",
        "follow_up": rec.get("follow_up") or "",
        "questions_asked": rec.get("questions_asked") or "",
        "questions_answered": rec.get("questions_answered") or "",
        "next_appointment": rec.get("next_appointment") or "",
        "document_ids": rec.get("document_ids") or "",
        "notes": rec.get("notes") or "",
        "created_at": rec.get("created_at") or _now(),
    }
    with _lock:
        conn = connect()
        try:
            existing = None
            if rec.get("id"):
                existing = conn.execute("SELECT id FROM visits WHERE id=?", (row["id"],)).fetchone()
            if existing:
                conn.execute(
                    "UPDATE visits SET day=?, title=?, physician=?, reason=?, summary=?, instructions=?, follow_up=?, "
                    "questions_asked=?, questions_answered=?, next_appointment=?, document_ids=?, notes=? WHERE id=?",
                    (
                        row["day"], row["title"], row["physician"], row["reason"], row["summary"], row["instructions"],
                        row["follow_up"], row["questions_asked"], row["questions_answered"], row["next_appointment"],
                        row["document_ids"], row["notes"], row["id"],
                    ),
                )
            else:
                conn.execute(
                    "INSERT INTO visits(id,day,title,physician,reason,summary,instructions,follow_up,questions_asked,"
                    "questions_answered,next_appointment,document_ids,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        row["id"], row["day"], row["title"], row["physician"], row["reason"], row["summary"],
                        row["instructions"], row["follow_up"], row["questions_asked"], row["questions_answered"],
                        row["next_appointment"], row["document_ids"], row["notes"], row["created_at"],
                    ),
                )
            conn.commit()
        finally:
            conn.close()
    log_event("visit", row["title"])
    return row


def add_missed_dose(name: str, *, kind: str = "medication", notes: str = "", day: str | None = None) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {
        "id": _nid("miss"),
        "day": day or _today(),
        "name": name,
        "kind": kind,
        "notes": notes,
        "created_at": _now(),
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO missed_doses(id,day,name,kind,notes,created_at) VALUES (?,?,?,?,?,?)",
                (row["id"], row["day"], row["name"], row["kind"], row["notes"], row["created_at"]),
            )
            conn.execute(
                "INSERT INTO dose_logs(id,day,name,kind,status,notes,created_at) VALUES (?,?,?,?,?,?,?)",
                (_nid("dose"), row["day"], row["name"], row["kind"], "missed", notes, row["created_at"]),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("missed_dose", name)
    return row


def log_dose(name: str, *, status: str = "taken", kind: str = "medication", notes: str = "", day: str | None = None) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    from jarvis.production_guard import ProductionIsolationError, assert_owner_write_allowed

    try:
        assert_owner_write_allowed(name, notes, store="health")
    except ProductionIsolationError as exc:
        raise ValueError(str(exc)) from exc
    status = "missed" if str(status).lower() in ("missed", "skip", "skipped") else "taken"
    row = {
        "id": _nid("dose"),
        "day": day or _today(),
        "name": name,
        "kind": kind,
        "status": status,
        "notes": notes,
        "created_at": _now(),
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO dose_logs(id,day,name,kind,status,notes,created_at) VALUES (?,?,?,?,?,?,?)",
                (row["id"], row["day"], row["name"], row["kind"], row["status"], row["notes"], row["created_at"]),
            )
            if status == "missed":
                conn.execute(
                    "INSERT INTO missed_doses(id,day,name,kind,notes,created_at) VALUES (?,?,?,?,?,?)",
                    (_nid("miss"), row["day"], row["name"], row["kind"], notes, row["created_at"]),
                )
            conn.commit()
        finally:
            conn.close()
    log_event("dose_log", f"{status}:{name}")
    return row


def add_recovery(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {
        "id": rec.get("id") or _nid("rec"),
        "day": rec.get("day") or _today(),
        "kind": str(rec.get("kind") or "recovery").lower(),
        "title": rec.get("title") or rec.get("kind") or "Recovery",
        "body_part": rec.get("body_part") or "",
        "pain": rec.get("pain"),
        "mobility": rec.get("mobility") or "",
        "status": rec.get("status") or "active",
        "notes": rec.get("notes") or "",
        "created_at": _now(),
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO recovery_events(id,day,kind,title,body_part,pain,mobility,status,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    row["id"], row["day"], row["kind"], row["title"], row["body_part"], row["pain"],
                    row["mobility"], row["status"], row["notes"], row["created_at"],
                ),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("recovery", row["title"])
    return row


def remember_milestone(key: str, title: str, detail: str = "", day: str | None = None) -> dict[str, Any] | None:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    existing = list_table("milestones", "key=?", (key,), limit=1)
    if existing:
        return existing[0]
    row = {
        "id": _nid("ms"),
        "key": key,
        "title": title,
        "detail": detail,
        "day": day or _today(),
        "created_at": _now(),
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO milestones(id,key,title,detail,day,created_at) VALUES (?,?,?,?,?,?)",
                (row["id"], row["key"], row["title"], row["detail"], row["day"], row["created_at"]),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("milestone", title)
    return row


def add_activity(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {
        "id": rec.get("id") or _nid("act"),
        "day": rec.get("day") or _today(),
        "kind": str(rec.get("kind") or "custom").strip().lower(),
        "title": rec.get("title") or rec.get("kind") or "Activity",
        "start_time": rec.get("start_time") or "",
        "end_time": rec.get("end_time") or "",
        "duration_min": rec.get("duration_min"),
        "intensity": rec.get("intensity") or "",
        "calories": rec.get("calories"),
        "distance": rec.get("distance"),
        "distance_units": rec.get("distance_units") or "",
        "steps": rec.get("steps"),
        "heart_rate": rec.get("heart_rate"),
        "notes": rec.get("notes") or "",
        "created_at": _now(),
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO activities(id,day,kind,title,start_time,end_time,duration_min,intensity,calories,distance,distance_units,steps,heart_rate,notes,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    row["id"], row["day"], row["kind"], row["title"], row["start_time"], row["end_time"],
                    row["duration_min"], row["intensity"], row["calories"], row["distance"], row["distance_units"],
                    row["steps"], row["heart_rate"], row["notes"], row["created_at"],
                ),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("activity", f"{row['kind']} {row['day']}")
    return row


def add_workout(rec: dict[str, Any], sets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {
        "id": rec.get("id") or _nid("wo"),
        "day": rec.get("day") or _today(),
        "title": rec.get("title") or rec.get("template") or "Workout",
        "template": rec.get("template") or "",
        "body_part": rec.get("body_part") or "",
        "duration_min": rec.get("duration_min"),
        "difficulty": rec.get("difficulty") or "",
        "pain": rec.get("pain"),
        "notes": rec.get("notes") or "",
        "created_at": _now(),
    }
    saved_sets: list[dict[str, Any]] = []
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO workouts(id,day,title,template,body_part,duration_min,difficulty,pain,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    row["id"], row["day"], row["title"], row["template"], row["body_part"],
                    row["duration_min"], row["difficulty"], row["pain"], row["notes"], row["created_at"],
                ),
            )
            for s in sets or rec.get("sets") or []:
                srow = {
                    "id": _nid("wos"),
                    "workout_id": row["id"],
                    "exercise": s.get("exercise") or "exercise",
                    "sets": s.get("sets"),
                    "reps": s.get("reps"),
                    "weight": s.get("weight"),
                    "weight_units": s.get("weight_units") or "lb",
                    "band_color": s.get("band_color") or "",
                    "resistance": s.get("resistance") or "",
                    "time_sec": s.get("time_sec"),
                    "rest_sec": s.get("rest_sec"),
                    "difficulty": s.get("difficulty") or "",
                    "pain": s.get("pain"),
                    "notes": s.get("notes") or "",
                    "body_part": s.get("body_part") or row["body_part"],
                    "created_at": _now(),
                }
                conn.execute(
                    "INSERT INTO workout_sets(id,workout_id,exercise,sets,reps,weight,weight_units,band_color,resistance,time_sec,rest_sec,difficulty,pain,notes,body_part,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        srow["id"], srow["workout_id"], srow["exercise"], srow["sets"], srow["reps"], srow["weight"],
                        srow["weight_units"], srow["band_color"], srow["resistance"], srow["time_sec"], srow["rest_sec"],
                        srow["difficulty"], srow["pain"], srow["notes"], srow["body_part"], srow["created_at"],
                    ),
                )
                saved_sets.append(srow)
            conn.commit()
        finally:
            conn.close()
    row["sets"] = saved_sets
    log_event("workout", row["title"])
    return row


def list_workout_sets(workout_id: str) -> list[dict[str, Any]]:
    return list_table("workout_sets", "workout_id=?", (workout_id,), order="created_at ASC", limit=200)


def upsert_goal(rec: dict[str, Any]) -> dict[str, Any]:
    rec.setdefault("status", "active")
    return _upsert_named("goals", rec, name_key="title")


def add_health_journal(body: str, *, day: str | None = None, mood: str = "") -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {"id": _nid("hj"), "day": day or _today(), "body": body, "mood": mood, "created_at": _now()}
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO health_journal(id,day,body,mood,created_at) VALUES (?,?,?,?,?)",
                (row["id"], row["day"], row["body"], row["mood"], row["created_at"]),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("health_journal", row["body"][:80])
    return row


def add_knowledge(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {
        "id": rec.get("id") or _nid("kn"),
        "title": rec.get("title") or "Health note",
        "source": rec.get("source") or "personal",
        "url": rec.get("url") or "",
        "body": rec.get("body") or "",
        "tags": rec.get("tags") or "",
        "created_at": _now(),
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO knowledge(id,title,source,url,body,tags,created_at) VALUES (?,?,?,?,?,?,?)",
                (row["id"], row["title"], row["source"], row["url"], row["body"], row["tags"], row["created_at"]),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("knowledge", row["title"])
    return row


def upsert_provider(rec: dict[str, Any]) -> dict[str, Any]:
    return _upsert_named("providers", rec, name_key="name")


def add_procedure(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {
        "id": rec.get("id") or _nid("proc"),
        "name": rec.get("name") or "Procedure",
        "kind": rec.get("kind") or rec.get("name") or "",
        "day": rec.get("day") or _today(),
        "location": rec.get("location") or "",
        "provider": rec.get("provider") or "",
        "result": rec.get("result") or "",
        "follow_up": rec.get("follow_up") or "",
        "document_id": rec.get("document_id") or "",
        "notes": rec.get("notes") or "",
        "created_at": _now(),
    }
    with _lock:
        conn = connect()
        try:
            conn.execute(
                "INSERT INTO procedures(id,name,kind,day,location,provider,result,follow_up,document_id,notes,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    row["id"], row["name"], row["kind"], row["day"], row["location"], row["provider"],
                    row["result"], row["follow_up"], row["document_id"], row["notes"], row["created_at"],
                ),
            )
            conn.commit()
        finally:
            conn.close()
    log_event("procedure", row["name"])
    return row


# Tables exported/restored for lifelong PHR integrity (full history, no silent caps).
_EXPORT_TABLES: tuple[tuple[str, str | None], ...] = (
    ("medications", None),
    ("supplements", None),
    ("conditions", None),
    ("allergies", None),
    ("vitals", "day ASC, recorded_at ASC"),
    ("labs", "day ASC, recorded_at ASC"),
    ("symptoms", "recorded_at DESC"),
    ("vaccinations", None),
    ("documents", "created_at DESC"),
    ("medical_notes", "created_at DESC"),
    ("reminders", None),
    ("doctor_questions", "created_at DESC"),
    ("consultations", "created_at DESC"),
    ("visits", "day DESC"),
    ("missed_doses", "created_at DESC"),
    ("activities", "day DESC"),
    ("workouts", "day DESC"),
    ("workout_sets", "created_at DESC"),
    ("goals", None),
    ("health_journal", "created_at DESC"),
    ("knowledge", "created_at DESC"),
    ("providers", None),
    ("procedures", "created_at DESC"),
    ("dose_logs", "created_at DESC"),
    ("recovery_events", "created_at DESC"),
    ("milestones", "created_at DESC"),
    ("family_history", None),
    ("preventive_care", None),
    ("nutrition_log", "day DESC"),
    ("health_observations", "created_at DESC"),
    ("pending_mutations", "created_at DESC"),
    ("events", "ts DESC"),
    ("backups", "created_at DESC"),
    ("restore_log", "created_at DESC"),
)


def table_row_count(table: str) -> int:
    with _lock:
        conn = connect()
        try:
            return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        finally:
            conn.close()


def export_bundle() -> dict[str, Any]:
    """Full Personal Health Record export — every row, no silent truncation."""
    # Checkins keep id+day+payload shape for restore fidelity
    checkin_rows: list[dict[str, Any]] = []
    with _lock:
        conn = connect()
        try:
            cur = conn.execute("SELECT id, day, recorded_at, payload FROM checkins ORDER BY day DESC")
            for r in cur.fetchall():
                payload = json.loads(r["payload"]) if isinstance(r["payload"], str) else (r["payload"] or {})
                checkin_rows.append(
                    {
                        "id": r["id"],
                        "day": r["day"],
                        "recorded_at": r["recorded_at"],
                        "payload": payload,
                    }
                )
        finally:
            conn.close()

    bundle: dict[str, Any] = {
        "product": "Health",
        "exported_at": _now(),
        "schema_version": SCHEMA_VERSION,
        "profile": get_profile(),
        "checkins": checkin_rows,
        "notes": list_table("medical_notes", order="created_at DESC", limit=None),
    }
    for table, order in _EXPORT_TABLES:
        if table == "medical_notes":
            continue  # aliased as notes for older backups
        bundle[table] = list_table(table, order=order, limit=None)

    # Completeness stamp — restore/verify can assert nothing was dropped
    counts = {"checkins": len(checkin_rows), "medical_notes": len(bundle["notes"])}
    for table, _ in _EXPORT_TABLES:
        if table == "medical_notes":
            continue
        counts[table] = len(bundle.get(table) or [])
        live = table_row_count(table)
        if counts[table] != live:
            raise RuntimeError(f"Health export incomplete for {table}: exported {counts[table]} of {live}")
    if counts["checkins"] != table_row_count("checkins"):
        raise RuntimeError("Health export incomplete for checkins")
    bundle["record_counts"] = counts
    bundle["complete"] = True
    return bundle


def upsert_row(table: str, record: dict[str, Any]) -> dict[str, Any]:
    """Insert-or-replace a row by id — used by lifelong restore merge."""
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    if not isinstance(record, dict) or not record.get("id"):
        raise ValueError("upsert_row requires id")
    cols_now = table_columns_safe(table)
    rec = {k: v for k, v in record.items() if k in cols_now}
    if "payload" in rec and not isinstance(rec["payload"], str):
        rec["payload"] = json.dumps(rec["payload"])
    cols = list(rec.keys())
    with _lock:
        conn = connect()
        try:
            placeholders = ",".join("?" for _ in cols)
            assignments = ",".join(f"{c}=excluded.{c}" for c in cols if c != "id")
            conn.execute(
                f"INSERT INTO {table}({','.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(id) DO UPDATE SET {assignments}",
                [rec.get(c) for c in cols],
            )
            conn.commit()
        finally:
            conn.close()
    return rec


def upsert_family_history(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.provenance import stamp

    row = stamp(
        {
            "id": rec.get("id") or _nid("fam"),
            "relation": str(rec.get("relation") or "other").lower(),
            "relation_side": rec.get("relation_side") or "",
            "display_name": rec.get("display_name") or "",
            "condition": rec.get("condition") or "",
            "condition_category": rec.get("condition_category") or "",
            "hereditary": 1 if rec.get("hereditary", True) else 0,
            "age_at_diagnosis": rec.get("age_at_diagnosis") or "",
            "living": rec.get("living"),
            "age_now": rec.get("age_now") or "",
            "age_at_death": rec.get("age_at_death") or "",
            "cause_of_death": rec.get("cause_of_death") or "",
            "notes": rec.get("notes") or "",
            "created_at": rec.get("created_at") or _now(),
            "provenance": rec.get("provenance") or "manual",
            "confidence": rec.get("confidence") or "user_entered",
            "confirmed": rec.get("confirmed", 0),
        },
        "family_history",
        source=str(rec.get("provenance") or "manual"),
        confidence=str(rec.get("confidence") or "user_entered"),
        confirmed=bool(rec.get("confirmed")),
    )
    return _upsert_named("family_history", row, name_key="condition")


def upsert_preventive(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.provenance import stamp

    row = stamp(
        {
            "id": rec.get("id") or _nid("prv"),
            "name": rec.get("name") or "Preventive care",
            "slug": rec.get("slug") or "",
            "category": rec.get("category") or "screening",
            "interval_months": rec.get("interval_months"),
            "last_done": rec.get("last_done") or "",
            "next_due": rec.get("next_due") or "",
            "scheduled_for": rec.get("scheduled_for") or "",
            "physician": rec.get("physician") or "",
            "facility": rec.get("facility") or "",
            "result": rec.get("result") or "",
            "result_day": rec.get("result_day") or "",
            "status": rec.get("status") or "planned",
            "document_id": rec.get("document_id") or "",
            "reminder_id": rec.get("reminder_id") or "",
            "source_kind": rec.get("source_kind") or "user",
            "notes": rec.get("notes") or "",
            "created_at": rec.get("created_at") or _now(),
            "provenance": rec.get("provenance") or "manual",
            "confidence": rec.get("confidence") or "user_entered",
        },
        "preventive_care",
        source=str(rec.get("provenance") or "manual"),
        confidence=str(rec.get("confidence") or "user_entered"),
    )
    return _upsert_named("preventive_care", row, name_key="name")


def add_nutrition(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.provenance import stamp
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    items = rec.get("items")
    if isinstance(items, (list, dict)):
        items = json.dumps(items)
    tags = rec.get("tags")
    if isinstance(tags, (list, dict)):
        tags = json.dumps(tags)
    row = stamp(
        {
            "id": rec.get("id") or _nid("nut"),
            "day": rec.get("day") or _today(),
            "recorded_at": rec.get("recorded_at") or _now(),
            "kind": str(rec.get("kind") or "meal").lower(),
            "meal_slot": rec.get("meal_slot") or "",
            "description": rec.get("description") or rec.get("text") or "",
            "items": items or "",
            "quantity": rec.get("quantity"),
            "units": rec.get("units") or "",
            "tags": tags or "",
            "notes": rec.get("notes") or "",
            "created_at": _now(),
            "provenance": rec.get("provenance") or "manual",
            "confidence": rec.get("confidence") or "user_entered",
        },
        "nutrition_log",
        source=str(rec.get("provenance") or "manual"),
        confidence=str(rec.get("confidence") or "user_entered"),
    )
    cols = [c for c in row.keys() if c in table_columns_safe("nutrition_log")]
    with _lock:
        conn = connect()
        try:
            conn.execute(
                f"INSERT INTO nutrition_log({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
                [row.get(c) for c in cols],
            )
            conn.commit()
        finally:
            conn.close()
    log_event("nutrition", row.get("description") or row["id"])
    return {k: row.get(k) for k in cols}


def remember_observation(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.provenance import stamp
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    kind = str(rec.get("kind") or "correlation")
    topic = str(rec.get("topic") or "general")
    existing = list_table("health_observations", "kind=? AND topic=?", (kind, topic), limit=1)
    evidence = rec.get("evidence")
    if isinstance(evidence, (list, dict)):
        evidence = json.dumps(evidence)
    now = _now()
    row = stamp(
        {
            "id": (existing[0]["id"] if existing else None) or _nid("obs"),
            "created_at": (existing[0]["created_at"] if existing else now),
            "last_seen": now,
            "day": rec.get("day") or _today(),
            "kind": kind,
            "topic": topic,
            "statement": rec.get("statement") or "",
            "evidence": evidence or "",
            "strength": rec.get("strength") or "weak",
            "window_days": rec.get("window_days"),
            "sample_size": rec.get("sample_size"),
            "educational": 1 if rec.get("educational", True) else 0,
            "dismissed": int(rec.get("dismissed") or 0),
            "provenance": "system",
            "confidence": "derived",
        },
        "health_observations",
        source="system",
        confidence="derived",
    )
    cols = [c for c in row.keys() if c in table_columns_safe("health_observations")]
    with _lock:
        conn = connect()
        try:
            placeholders = ",".join("?" for _ in cols)
            assignments = ",".join(f"{c}=excluded.{c}" for c in cols if c != "id")
            conn.execute(
                f"INSERT INTO health_observations({','.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(id) DO UPDATE SET {assignments}",
                [row.get(c) for c in cols],
            )
            conn.commit()
        finally:
            conn.close()
    return {k: row.get(k) for k in cols}


def add_backup_record(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {
        "id": rec.get("id") or _nid("bak"),
        "created_at": rec.get("created_at") or _now(),
        "path": rec.get("path") or "",
        "filename": rec.get("filename") or "",
        "format": rec.get("format") or "jarvis-health-v1",
        "encrypted": 1 if rec.get("encrypted", True) else 0,
        "size_bytes": rec.get("size_bytes"),
        "sha256": rec.get("sha256") or "",
        "record_counts": json.dumps(rec.get("record_counts") or {}) if not isinstance(rec.get("record_counts"), str) else rec.get("record_counts"),
        "schema_version": rec.get("schema_version") or float(SCHEMA_VERSION),
        "app_version": rec.get("app_version") or "",
        "kind": rec.get("kind") or "manual",
        "verified_at": rec.get("verified_at"),
        "verify_status": rec.get("verify_status") or "",
        "restored_at": rec.get("restored_at"),
        "notes": rec.get("notes") or "",
    }
    with _lock:
        conn = connect()
        try:
            cols = list(row.keys())
            conn.execute(
                f"INSERT INTO backups({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
                [row[c] for c in cols],
            )
            conn.commit()
        finally:
            conn.close()
    log_event("backup", row["filename"] or row["id"])
    return row


def add_restore_log(rec: dict[str, Any]) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = {
        "id": rec.get("id") or _nid("rst"),
        "created_at": _now(),
        "backup_id": rec.get("backup_id") or "",
        "source_path": rec.get("source_path") or "",
        "mode": rec.get("mode") or "merge",
        "confirmed": 1 if rec.get("confirmed") else 0,
        "safety_backup_id": rec.get("safety_backup_id") or "",
        "tables_written": json.dumps(rec.get("tables_written") or []) if not isinstance(rec.get("tables_written"), str) else rec.get("tables_written"),
        "rows_written": rec.get("rows_written"),
        "status": rec.get("status") or "pending",
        "message": rec.get("message") or "",
    }
    with _lock:
        conn = connect()
        try:
            cols = list(row.keys())
            conn.execute(
                f"INSERT INTO restore_log({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
                [row[c] for c in cols],
            )
            conn.commit()
        finally:
            conn.close()
    return row


def schema_version() -> str:
    with _lock:
        conn = connect()
        try:
            row = conn.execute("SELECT value FROM schema_meta WHERE key=?", ("schema_version",)).fetchone()
            if row:
                return str(row["value"] or SCHEMA_VERSION)
        finally:
            conn.close()
    return SCHEMA_VERSION
