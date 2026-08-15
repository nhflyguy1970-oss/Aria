"""Record provenance and confidence — stamp every Health write; never auto-edit confirmed rows."""

from __future__ import annotations

import time
from typing import Any

PROVENANCE_SOURCES = (
    "manual",
    "voice",
    "chat_nl",
    "ocr",
    "imported_pdf",
    "doctor_visit",
    "lab_report",
    "ai_consultation",
    "wearable_import",  # reserved — not implemented yet
    "catalog_suggestion",
    "system",
)

CONFIDENCE_LEVELS = (
    "user_confirmed",
    "ocr_verified",
    "imported_physician",
    "ocr_low",
    "awaiting_confirmation",
    "derived",
    "user_entered",
)

# Columns that may be stamped onto records (must exist on the target table).
METADATA_KEYS = (
    "person_id",
    "source_system",
    "external_id",
    "device_id",
    "provenance",
    "provenance_detail",
    "recorded_by",
    "confidence",
    "confirmed",
    "confirmed_at",
)

_COLUMN_CACHE: dict[str, frozenset[str]] = {}


class ConfirmedRecordGuard(PermissionError):
    """Raised when an automatic path would overwrite a user-confirmed record."""


def table_columns(table: str) -> frozenset[str]:
    cached = _COLUMN_CACHE.get(table)
    if cached is not None:
        return cached
    from jarvis.health_product import store

    with store._lock:
        conn = store.connect()
        try:
            cols = frozenset(r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall())
        finally:
            conn.close()
    _COLUMN_CACHE[table] = cols
    return cols


def clear_column_cache() -> None:
    _COLUMN_CACHE.clear()


def stamp(
    record: dict[str, Any],
    table: str,
    *,
    source: str = "manual",
    confidence: str = "user_entered",
    detail: str = "",
    recorded_by: str = "user",
    confirmed: bool | None = None,
    person_id: str | None = None,
    source_system: str | None = None,
    external_id: str | None = None,
    device_id: str | None = None,
) -> dict[str, Any]:
    """Return a copy of record with provenance fields that exist on `table`."""
    out = dict(record)
    cols = table_columns(table)
    desired: dict[str, Any] = {
        "provenance": source if source in PROVENANCE_SOURCES else "manual",
        "provenance_detail": (detail or "")[:2000],
        "recorded_by": recorded_by or "user",
        "confidence": confidence if confidence in CONFIDENCE_LEVELS else "user_entered",
    }
    if person_id is not None:
        desired["person_id"] = person_id
    if source_system is not None:
        desired["source_system"] = source_system
    if external_id is not None:
        desired["external_id"] = external_id
    if device_id is not None:
        desired["device_id"] = device_id
    if confirmed is True:
        desired["confirmed"] = 1
        desired["confirmed_at"] = time.time()
    elif confirmed is False:
        desired["confirmed"] = 0
        desired["confirmed_at"] = None
    elif "confirmed" not in out and "confirmed" in cols:
        desired.setdefault("confirmed", 0)

    for key, val in desired.items():
        if key in cols and (key not in out or out.get(key) in (None, "")):
            out[key] = val
        elif key in cols and key in ("provenance", "confidence", "provenance_detail", "recorded_by") and key not in record:
            out[key] = val
    # Drop unknown keys that would break _upsert_named SQL
    return {k: v for k, v in out.items() if k == "id" or k in cols or k not in METADATA_KEYS}


def describe(row: dict[str, Any] | None) -> dict[str, Any]:
    row = row or {}
    conf = str(row.get("confidence") or "")
    confirmed = bool(row.get("confirmed"))
    badge = "✓ User confirmed" if confirmed or conf == "user_confirmed" else None
    if not badge and conf == "ocr_verified":
        badge = "✓ OCR verified"
    elif not badge and conf == "imported_physician":
        badge = "✓ Imported from physician report"
    elif not badge and conf == "ocr_low":
        badge = "⚠ OCR low confidence"
    elif not badge and conf == "awaiting_confirmation":
        badge = "⚠ Awaiting user confirmation"
    elif not badge and conf == "derived":
        badge = "Educational / derived"
    elif not badge:
        badge = f"Source: {row.get('provenance') or 'manual'}"
    return {
        "provenance": row.get("provenance") or "manual",
        "provenance_detail": row.get("provenance_detail") or "",
        "confidence": conf or "user_entered",
        "confirmed": confirmed,
        "badge": badge,
        "person_id": row.get("person_id"),
        "source_system": row.get("source_system"),
        "external_id": row.get("external_id"),
        "device_id": row.get("device_id"),
    }


def guard_update(existing: dict[str, Any] | None, incoming: dict[str, Any], *, allow_confirmed: bool = False) -> dict[str, Any]:
    """Refuse automatic modification of confirmed records unless explicitly allowed."""
    if not existing:
        return incoming
    if allow_confirmed:
        return incoming
    if int(existing.get("confirmed") or 0) == 1:
        raise ConfirmedRecordGuard(
            "This Health record is user-confirmed and will not be changed automatically. "
            "Confirm explicitly in Health if you want to update it."
        )
    return incoming


def mark_confirmed(table: str, item_id: str) -> dict[str, Any] | None:
    from jarvis.health_product import store
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    row = store.get_by_id(table, item_id)
    if not row:
        return None
    cols = table_columns(table)
    if "confirmed" not in cols:
        return row
    with store._lock:
        conn = store.connect()
        try:
            if "confirmed_at" in cols:
                conn.execute(
                    f"UPDATE {table} SET confirmed=1, confirmed_at=? WHERE id=?",
                    (time.time(), item_id),
                )
            else:
                conn.execute(f"UPDATE {table} SET confirmed=1 WHERE id=?", (item_id,))
            conn.commit()
        finally:
            conn.close()
    store.log_event("confirm_record", f"{table}:{item_id}")
    return store.get_by_id(table, item_id)
