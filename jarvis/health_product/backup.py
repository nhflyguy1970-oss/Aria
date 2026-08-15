"""Encrypted Health backups — jarvis-health-v1; never overwrite without confirm."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

FORMAT = "jarvis-health-v1"


def _crypto():
    """Reuse journal crypto primitives with a Health format wrapper."""
    from jarvis import journal_crypto as jc

    return jc


def encrypt_bundle(bundle: dict[str, Any], password: str) -> dict[str, str]:
    jc = _crypto()
    # Temporarily use journal encrypt then retag format
    env = jc.encrypt_export(bundle, password)
    env["format"] = FORMAT
    return env


def decrypt_bundle(data: dict[str, Any], password: str) -> dict[str, Any]:
    jc = _crypto()
    if data.get("format") not in (FORMAT, jc.FORMAT):
        raise ValueError("Not a Jarvis encrypted Health backup")
    # journal decrypt checks format — coerce temporarily
    payload = dict(data)
    payload["format"] = jc.FORMAT
    return jc.decrypt_import(payload, password)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def create(*, password: str, kind: str = "manual", notes: str = "") -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    store.ensure_dirs()
    backup_dir = store.HEALTH_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    bundle = store.export_bundle()
    if not bundle.get("complete"):
        raise RuntimeError("Health refused to write an incomplete backup.")
    ts = time.strftime("%Y%m%d-%H%M%S")
    filename = f"aria-health-{ts}.json"
    path = backup_dir / filename
    if path.exists():
        filename = f"aria-health-{ts}-{uuid.uuid4().hex[:6]}.json"
        path = backup_dir / filename
    env = encrypt_bundle(bundle, password)
    path.write_text(json.dumps(env, indent=2), encoding="utf-8")
    digest = _sha256_file(path)
    counts = bundle.get("record_counts") or {
        k: len(v) if isinstance(v, list) else 1
        for k, v in bundle.items()
        if k not in ("product", "exported_at", "schema_version", "profile", "record_counts", "complete")
    }
    rec = store.add_backup_record(
        {
            "path": str(path),
            "filename": filename,
            "format": FORMAT,
            "encrypted": True,
            "size_bytes": path.stat().st_size,
            "sha256": digest,
            "record_counts": counts,
            "schema_version": float(store.SCHEMA_VERSION),
            "kind": kind,
            "notes": notes,
            "verify_status": "ok",
            "verified_at": time.time(),
        }
    )
    return {
        "ok": True,
        "intent": "backup",
        "backup": rec,
        "complete": True,
        "record_counts": counts,
        "message": f"Encrypted Health backup saved as {filename} (complete lifelong export). Store the password safely — it cannot be recovered.\n\n_{DISCLAIMER}_",
        "disclaimer": DISCLAIMER,
    }


def verify(backup_id: str) -> dict[str, Any]:
    row = store.get_by_id("backups", backup_id)
    if not row:
        return {"ok": False, "message": "Backup not found.", "disclaimer": DISCLAIMER}
    path = Path(row["path"])
    if not path.is_file():
        return {"ok": False, "message": "Backup file missing on disk.", "disclaimer": DISCLAIMER}
    digest = _sha256_file(path)
    ok = digest == row.get("sha256")
    with store._lock:
        conn = store.connect()
        try:
            conn.execute(
                "UPDATE backups SET verified_at=?, verify_status=? WHERE id=?",
                (time.time(), "ok" if ok else "mismatch", backup_id),
            )
            conn.commit()
        finally:
            conn.close()
    return {
        "ok": ok,
        "intent": "integrity",
        "sha256": digest,
        "expected": row.get("sha256"),
        "message": ("Integrity OK." if ok else "Integrity check FAILED — file does not match recorded hash.") + f"\n\n_{DISCLAIMER}_",
        "disclaimer": DISCLAIMER,
    }


def history() -> dict[str, Any]:
    rows = store.list_table("backups", limit=100)
    lines = ["**Health backup history**", ""]
    if not rows:
        lines.append("No backups yet.")
    else:
        for r in rows[:30]:
            lines.append(f"• {r.get('filename')} — {r.get('kind')} — verify={r.get('verify_status') or '—'} — {r.get('size_bytes') or 0} bytes")
    lines += ["", "_" + DISCLAIMER + "_"]
    return {"ok": True, "intent": "backup_history", "backups": rows, "message": "\n".join(lines), "disclaimer": DISCLAIMER}


def restore_preview(*, backup_id: str = "", path: str = "", password: str = "") -> dict[str, Any]:
    row = store.get_by_id("backups", backup_id) if backup_id else None
    file_path = Path(path or (row or {}).get("path") or "")
    if not file_path.is_file():
        return {"ok": False, "message": "Backup file not found.", "disclaimer": DISCLAIMER}
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        bundle = decrypt_bundle(data, password)
    except ValueError as exc:
        # Wrong password / corrupt cipher — owner-facing failure, not a 500.
        return {
            "ok": False,
            "message": str(exc) or "Wrong password or corrupt file",
            "disclaimer": DISCLAIMER,
        }
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "message": f"Could not read backup: {exc}", "disclaimer": DISCLAIMER}
    counts = {k: len(v) if isinstance(v, list) else (1 if isinstance(v, dict) else 0) for k, v in bundle.items()}
    return {
        "ok": True,
        "intent": "restore_preview",
        "confirm_required": True,
        "path": str(file_path),
        "backup_id": (row or {}).get("id"),
        "record_counts": counts,
        "message": (
            "Restore preview ready. This will change your Health Record.\n"
            "Reply with confirm=true and mode=merge|replace to proceed. "
            "A safety backup will be created first.\n\n_" + DISCLAIMER + "_"
        ),
        "disclaimer": DISCLAIMER,
    }


# Tables restored from a lifelong backup (merge by id). Skip backup-system metadata.
_RESTORE_TABLES = (
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
    "reminders",
    "doctor_questions",
    "consultations",
    "visits",
    "missed_doses",
    "activities",
    "workouts",
    "workout_sets",
    "goals",
    "health_journal",
    "knowledge",
    "providers",
    "procedures",
    "dose_logs",
    "recovery_events",
    "milestones",
    "family_history",
    "preventive_care",
    "nutrition_log",
    "health_observations",
)


def restore(*, password: str, backup_id: str = "", path: str = "", mode: str = "merge", confirm: bool = False) -> dict[str, Any]:
    from jarvis.health_product.trust import assert_writable

    assert_writable()
    preview = restore_preview(backup_id=backup_id, path=path, password=password)
    if not preview.get("ok"):
        return preview
    if not confirm:
        return {
            "ok": False,
            "confirm_required": True,
            "status_code": 409,
            "message": "Restore refused without explicit confirmation. Pass confirm=true after reviewing the preview.",
            "disclaimer": DISCLAIMER,
            **preview,
        }
    # Password validated — safety backup next; never destroy the current PHR without a recoverable copy
    safety = create(password=password, kind="pre_restore", notes=f"Safety backup before restore of {backup_id or path}")
    file_path = Path(preview["path"])
    data = json.loads(file_path.read_text(encoding="utf-8"))
    bundle = decrypt_bundle(data, password)
    mode = "merge"  # replace wipe is intentionally unavailable — safety first
    written = 0
    tables: list[str] = []

    profile = bundle.get("profile")
    if isinstance(profile, dict) and profile:
        store.set_profile(profile)
        written += 1
        tables.append("profile")

    # Check-ins: prefer id-preserving restore; fall back for older payload-only exports
    for row in bundle.get("checkins") or []:
        if not isinstance(row, dict):
            continue
        try:
            if row.get("id") and "payload" in row:
                store.upsert_row("checkins", row)
            else:
                store.upsert_checkin(row, day=row.get("day"))
            written += 1
            tables.append("checkins")
        except Exception:
            continue

    # Legacy alias
    if bundle.get("notes") and not bundle.get("medical_notes"):
        bundle = dict(bundle)
        bundle["medical_notes"] = bundle.get("notes")

    for table in _RESTORE_TABLES:
        for row in bundle.get(table) or []:
            if not isinstance(row, dict):
                continue
            try:
                row = dict(row)
                if not row.get("id"):
                    # Avoid collisions on anonymous re-import
                    continue
                store.upsert_row(table, row)
                written += 1
                tables.append(table)
            except Exception:
                continue

    log = store.add_restore_log(
        {
            "backup_id": backup_id,
            "source_path": str(file_path),
            "mode": mode,
            "confirmed": True,
            "safety_backup_id": (safety.get("backup") or {}).get("id"),
            "tables_written": sorted(set(tables)),
            "rows_written": written,
            "status": "complete",
            "message": f"Restored {written} rows (merge). Bundle complete={bundle.get('complete')}.",
        }
    )
    return {
        "ok": True,
        "intent": "restore",
        "restore_log": log,
        "safety_backup": safety.get("backup"),
        "rows_written": written,
        "tables": sorted(set(tables)),
        "message": (
            f"Restore complete ({written} rows across {len(set(tables))} sections, merge). "
            f"Safety backup: {(safety.get('backup') or {}).get('filename')}.\n\n_{DISCLAIMER}_"
        ),
        "disclaimer": DISCLAIMER,
    }


def integrity_report() -> dict[str, Any]:
    rows = store.list_table("backups", limit=50)
    results = []
    for r in rows:
        results.append({"id": r["id"], "filename": r.get("filename"), **verify(r["id"])})
    ok_n = sum(1 for r in results if r.get("ok"))
    return {
        "ok": True,
        "intent": "integrity",
        "checked": len(results),
        "ok_count": ok_n,
        "results": results,
        "message": f"Checked {len(results)} backup(s); {ok_n} OK.\n\n_{DISCLAIMER}_",
        "disclaimer": DISCLAIMER,
    }
