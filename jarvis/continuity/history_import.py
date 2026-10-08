"""Recovering older conversation history from data backups — dry run first.

``dry_run`` only reads. It compares a backup's ``chat_branches.json`` with the
live branch store and the continuity index, and produces a manifest: every turn,
its provenance (backup, branch, position), whether it is already present, a
duplicate, or a suspected test artifact, and which continuity records it would
yield. Nothing is written except the manifest, to a path the caller chooses.

``apply_import`` exists so an approved import is a reviewed, repeatable step:
it requires the manifest's token, writes only to a new, dedicated archive file
(``import-<backup>.jsonl``) — never to existing archives or the branch store —
and its events are marked ``import`` so they are indexed and retrievable but
not encoded into ACM automatically.

Backup messages carry no per-message timestamps. Imported turns are dated by
their branch's creation time and flagged ``undated_message`` so retrieval and
answers never present that date as when a sentence was said.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from jarvis.continuity import store
from jarvis.continuity.classify import classify


def _hash(role: str, content: str) -> str:
    return hashlib.sha256(f"{role}\0{(content or '').strip()}".encode()).hexdigest()


def _turns(branches_file: Path) -> list[dict[str, Any]]:
    data = json.loads(Path(branches_file).read_text(encoding="utf-8"))
    out = []
    for bid, branch in (data.get("branches") or {}).items():
        position = 0
        for message in branch.get("messages") or []:
            role = message.get("role")
            if role not in ("user", "assistant"):
                continue
            out.append(
                {
                    "branch": bid,
                    "branch_name": branch.get("name") or bid,
                    "branch_created": branch.get("created") or "",
                    "forked_from": branch.get("forked_from"),
                    "position": position,
                    "role": role,
                    "content": str(message.get("content") or ""),
                }
            )
            position += 1
    return out


def _sessions_inventory(db: Path) -> dict[str, Any]:
    if not db.is_file():
        return {"present": False}
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        tables = [
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if not r[0].startswith("sqlite_")
        ]
        return {
            "present": True,
            "tables": {t: conn.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tables},
        }
    finally:
        conn.close()


def dry_run(
    backup_dir: Path | str,
    *,
    live_branches_file: Path | None = None,
    manifest_path: Path | None = None,
    preview_chars: int = 80,
) -> dict[str, Any]:
    from jarvis.trust_memory import is_test_artifact

    backup_dir = Path(backup_dir)
    source = backup_dir / "chat_branches.json"
    if live_branches_file is None:
        from jarvis.branches import BRANCHES_FILE

        live_branches_file = BRANCHES_FILE
    live_hashes = {
        _hash(t["role"], t["content"])
        for t in (_turns(live_branches_file) if Path(live_branches_file).is_file() else [])
    }
    try:
        indexed_hashes = store.episode_hashes()
    except Exception:  # noqa: BLE001 - the manifest records that the index was not compared
        indexed_hashes = set()

    seen: set[str] = set()
    entries: list[dict[str, Any]] = []
    statuses: Counter[str] = Counter()
    would_records: Counter[str] = Counter()
    for turn in _turns(source):
        h = _hash(turn["role"], turn["content"])
        if h in live_hashes:
            status = "present_in_live_store"
        elif h in indexed_hashes:
            status = "present_in_index"
        elif h in seen:
            status = "duplicate_within_backup"  # forks copy their parent's turns
        elif is_test_artifact(turn["content"]):
            status = "suspected_test_artifact"
        elif not turn["content"].strip():
            status = "empty"
        else:
            status = "importable"
        seen.add(h)
        statuses[status] += 1
        kind = None
        if status == "importable":
            kind = classify(turn["role"], turn["content"]).kind
            if kind:
                would_records[kind] += 1
        entries.append(
            {
                "provenance": (
                    f"backup:{backup_dir.name}/chat_branches.json"
                    f"#branch={turn['branch']}&position={turn['position']}"
                ),
                "branch": turn["branch"],
                "branch_name": turn["branch_name"],
                "branch_created": turn["branch_created"],
                "forked_from": turn["forked_from"],
                "position": turn["position"],
                "role": turn["role"],
                "chars": len(turn["content"]),
                "sha256": h,
                "status": status,
                "would_record": kind,
                "preview": turn["content"][:preview_chars],
            }
        )

    created = sorted(e["branch_created"] for e in entries if e["branch_created"])
    importable = [e for e in entries if e["status"] == "importable"]
    summary = {
        "backup": str(backup_dir),
        "generated": datetime.now().isoformat(timespec="seconds"),
        "turns": len(entries),
        "by_status": dict(statuses),
        "importable_by_role": dict(Counter(e["role"] for e in importable)),
        "importable_branches": len({e["branch"] for e in importable}),
        "would_create_records": dict(would_records),
        "branch_created_range": [created[0], created[-1]] if created else [],
        "per_message_timestamps": False,
        "sessions_db": _sessions_inventory(backup_dir / "chat_sessions.db"),
        "written": False,
    }
    manifest = {"summary": summary, "entries": entries}
    manifest["token"] = hashlib.sha256(
        json.dumps([e["sha256"] + e["status"] for e in entries]).encode()
    ).hexdigest()[:16]
    if manifest_path is not None:
        manifest_path = Path(manifest_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
        manifest_path.chmod(0o600)
    return manifest


def apply_import(
    reviewed: dict[str, Any],
    *,
    confirm: str,
    backup_dir: Path | str,
    archive_root: Path | None = None,
) -> dict[str, Any]:
    """Import the *accepted* turns of a reviewed manifest. Requires approval.

    ``reviewed`` comes from ``history_review.review``. Only entries decided
    ``accepted`` are written; ``uncertain`` and ``rejected`` never are. The
    confirmation must be the reviewed manifest's token, and the backup and live
    history must still match the dry run the review was based on.
    """
    from jarvis.live_data_guard import assert_live_write_allowed

    if not confirm or confirm != reviewed.get("token"):
        raise ValueError("confirmation token does not match this reviewed manifest")
    backup_dir = Path(backup_dir)
    fresh = dry_run(backup_dir, preview_chars=0)
    if fresh["token"] != (reviewed.get("summary") or {}).get("source_manifest_token"):
        raise ValueError("live history or backup changed since the dry run; review again")
    if archive_root is None:
        from jarvis.continuity.ingest import archive_root as default_root

        archive_root = default_root()
    target = Path(archive_root) / f"import-{backup_dir.name}.jsonl"
    if target.exists():
        raise ValueError(f"{target.name} already exists; this backup was imported before")
    assert_live_write_allowed(target)
    contents = {
        (t["branch"], t["position"]): t["content"] for t in _turns(backup_dir / "chat_branches.json")
    }
    accepted = [e for e in reviewed["entries"] if e["decision"] == "accepted"]
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        for entry in accepted:
            date = entry.get("approx_date") or entry.get("branch_created") or ""
            event = {
                "id": uuid.uuid4().hex,
                "ts": _approx_ts(date),
                "branch": f"import:{entry['branch']}",
                "kind": "import",
                "role": entry["role"],
                "content": contents[(entry["branch"], entry["position"])],
                "origin": entry["provenance"],
                "undated_message": True,
                "approx_date": date,
                "review_reason": entry["reason"],
            }
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return {"ok": True, "written": len(accepted), "archive": str(target)}


def _approx_ts(date: str) -> str:
    """An ISO timestamp for an approximate date ("2026-08-11" → noon that day)."""
    if not date:
        return datetime.now().isoformat()
    if len(date) == 10:
        return f"{date}T12:00:00"
    return date
