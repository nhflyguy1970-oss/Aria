"""Searchable proposal history archive (separate from pending proposals)."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "coding_proposal_history.json"
_MAX_ENTRIES = 500


def _load() -> list[dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list[dict[str, Any]]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(entries[:_MAX_ENTRIES], indent=2, default=str), encoding="utf-8")


def _files_list(proposal: dict[str, Any]) -> list[str]:
    files = proposal.get("files") or []
    if not files and proposal.get("path"):
        return [str(proposal["path"])]
    out = []
    for f in files:
        p = f.get("path") if isinstance(f, dict) else None
        if p:
            out.append(str(p))
    return out


def _coding_model() -> str:
    """Read coding role from settings file only — never ping Ollama."""
    try:
        from jarvis.config import is_uncensored
        from jarvis.model_store import _load_raw

        data = _load_raw() or {}
        mode = "uncensored" if is_uncensored() else "standard"
        bank = data.get(mode) or data.get("standard") or {}
        return str(bank.get("coding") or bank.get("coder") or "")
    except Exception:
        try:
            from jarvis.model_store import SETTINGS_FILE
            import json

            if SETTINGS_FILE.exists():
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                bank = data.get("standard") or {}
                return str(bank.get("coding") or bank.get("coder") or "")
        except Exception:
            pass
        return ""


def record_proposal(
    proposal_id: str,
    proposal: dict[str, Any],
    *,
    status: str = "pending",
    model: str | None = None,
    verification_status: str = "unknown",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Upsert a history row for a proposal."""
    entries = _load()
    now = time.time()
    files = _files_list(proposal)
    summary = (proposal.get("explanation") or proposal.get("summary") or "")[:400]
    existing = next((e for e in entries if e.get("id") == proposal_id), None)
    row = {
        "id": proposal_id,
        "timestamp": (existing or {}).get("timestamp") or now,
        "updated_at": now,
        "files": files,
        "summary": summary,
        "status": status,
        "mode": proposal.get("mode") or "propose",
        "model": model if model is not None else (_coding_model() or (existing or {}).get("model") or ""),
        "verification_status": verification_status,
        "syntax_ok": proposal.get("syntax_ok"),
        "bookmarked": bool((existing or {}).get("bookmarked")),
        "patch": _build_patch_snapshot(proposal) if status in ("pending", "applied", "rejected") else (existing or {}).get("patch"),
        "files_payload": proposal.get("files") or (
            [{"path": proposal["path"], "code": proposal.get("code", "")}]
            if proposal.get("path")
            else (existing or {}).get("files_payload")
        ),
    }
    if extra:
        row.update(extra)
    entries = [e for e in entries if e.get("id") != proposal_id]
    entries.insert(0, row)
    _save(entries)
    return row


def _build_patch_snapshot(proposal: dict[str, Any]) -> str:
    """Best-effort unified patch text without requiring disk reads."""
    parts: list[str] = []
    files = proposal.get("files") or []
    if not files and proposal.get("path"):
        files = [{"path": proposal["path"], "code": proposal.get("code", "")}]
    for f in files:
        path = f.get("path") or ""
        code = f.get("code") or ""
        if f.get("delete"):
            parts.append(f"--- a/{path}\n+++ /dev/null\n@@ DELETE @@\n")
            continue
        # Store proposed content as a create-style hunk when no original available
        lines = code.splitlines()
        parts.append(f"--- a/{path}\n+++ b/{path}\n@@ proposed {len(lines)} lines @@\n")
        for ln in lines[:400]:
            parts.append(f"+{ln}")
        if len(lines) > 400:
            parts.append(f"+… ({len(lines) - 400} more lines)")
    return "\n".join(parts)[:120_000]


def update_status(
    proposal_id: str,
    status: str,
    *,
    verification_status: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    entries = _load()
    for e in entries:
        if e.get("id") == proposal_id:
            e["status"] = status
            e["updated_at"] = time.time()
            if verification_status is not None:
                e["verification_status"] = verification_status
            if extra:
                e.update(extra)
            _save(entries)
            return e
    return None


def set_bookmark(proposal_id: str, bookmarked: bool = True) -> dict[str, Any] | None:
    entries = _load()
    for e in entries:
        if e.get("id") == proposal_id:
            e["bookmarked"] = bool(bookmarked)
            e["updated_at"] = time.time()
            _save(entries)
            return e
    return None


def get_proposal(proposal_id: str) -> dict[str, Any] | None:
    for e in _load():
        if e.get("id") == proposal_id:
            return e
    return None


def list_history(
    *,
    query: str = "",
    status: str = "",
    bookmarked_only: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    q = (query or "").strip().lower()
    st = (status or "").strip().lower()
    rows = _load()
    filtered: list[dict[str, Any]] = []
    for e in rows:
        if st and str(e.get("status") or "").lower() != st:
            continue
        if bookmarked_only and not e.get("bookmarked"):
            continue
        if q:
            blob = " ".join(
                [
                    str(e.get("id") or ""),
                    str(e.get("summary") or ""),
                    str(e.get("status") or ""),
                    str(e.get("model") or ""),
                    " ".join(e.get("files") or []),
                ]
            ).lower()
            if q not in blob:
                continue
        filtered.append(e)
    total = len(filtered)
    page = filtered[offset : offset + max(1, min(limit, 200))]
    # Strip heavy payloads from list view
    light = []
    for e in page:
        light.append(
            {
                "id": e.get("id"),
                "timestamp": e.get("timestamp"),
                "updated_at": e.get("updated_at"),
                "files": e.get("files") or [],
                "summary": e.get("summary") or "",
                "status": e.get("status"),
                "mode": e.get("mode"),
                "model": e.get("model") or "",
                "verification_status": e.get("verification_status"),
                "syntax_ok": e.get("syntax_ok"),
                "bookmarked": bool(e.get("bookmarked")),
                "has_patch": bool(e.get("patch") or e.get("files_payload")),
            }
        )
    return {"ok": True, "total": total, "offset": offset, "limit": limit, "items": light}


def export_patch(proposal_id: str) -> dict[str, Any]:
    e = get_proposal(proposal_id)
    if not e:
        return {"ok": False, "error": "Proposal not found in history"}
    patch = e.get("patch") or ""
    if not patch and e.get("files_payload"):
        patch = _build_patch_snapshot({"files": e["files_payload"], "explanation": e.get("summary")})
    name = f"aria-proposal-{proposal_id}.patch"
    return {
        "ok": True,
        "proposal_id": proposal_id,
        "filename": name,
        "patch": patch,
        "content_type": "text/x-diff",
    }


def restore_to_pending(assistant: Any, proposal_id: str) -> dict[str, Any]:
    """Re-queue a historical proposal into pending_proposals for Apply."""
    e = get_proposal(proposal_id)
    if not e:
        return {"ok": False, "error": "Proposal not found in history"}
    files = e.get("files_payload")
    if not files:
        return {"ok": False, "error": "No file payload to restore"}
    new_id = str(uuid.uuid4())[:8]
    payload = {
        "mode": e.get("mode") or "restore",
        "files": files,
        "explanation": e.get("summary") or f"Restored from history {proposal_id}",
        "diagnostics": [],
        "syntax_ok": e.get("syntax_ok", True),
        "restored_from": proposal_id,
    }
    if len(files) == 1:
        payload["path"] = files[0].get("path")
        payload["code"] = files[0].get("code", "")
    assistant.pending_proposals[new_id] = payload
    assistant._persist_proposals()
    assistant.session.note_proposal(new_id)
    record_proposal(new_id, payload, status="pending", model=e.get("model") or "")
    update_status(proposal_id, e.get("status") or "applied", extra={"restored_as": new_id})
    return {"ok": True, "proposal_id": new_id, "restored_from": proposal_id, "message": f"Restored as proposal `{new_id}`."}
