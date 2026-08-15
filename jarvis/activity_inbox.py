"""Server-authoritative Activity inbox (Batch C).

Browser is a client. localStorage is cache only — not source of truth.
"""

from __future__ import annotations

import json
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

INBOX_DIR = DATA_DIR / "activity"
INBOX_FILE = INBOX_DIR / "inbox.jsonl"
ENGINEERING_FILE = INBOX_DIR / "engineering.jsonl"
_lock = threading.Lock()
_MAX = 500

_CANCEL_RE = re.compile(
    r"aria-room-leave|signal is aborted|request cancelled|"
    r"the operation was aborted|aborterror|\bcancelled\b.*\broom\b|"
    r"stream aborted|cancel api",
    re.I,
)
_ENGINEERING_RE = re.compile(
    r"could not load |failed to load |load failed|checklist failed|"
    r"home unavailable|settings unavailable|status unavailable|"
    r"work schedule unavailable|browser agent unavailable|"
    r"comfyui settings unavailable|cloud live unavailable|"
    r"key legend unavailable|journal stats unavailable|cad status: undefined|"
    r"mission control.*health|system audit — failures|system audit - failures|"
    r"vision settings|could not load voice|could not load chat sessions|"
    r"could not load audio|could not load connections|could not load profile|"
    r"aria started|activity center is listening|"
    r"^notification$|^not found\b|select an image|select images|"
    r"enter a prompt first|enter an image description|task text required|"
    r"enter a (search query|natural language|backing|song topic)|"
    r"enter event text first|enter one path per line|enter 4|"
    r"need (top text|source path)|preview needs|nothing to redo|"
    r"empty request|pick a song file|"
    r"calendar day failed|could not speak reply|could not refresh audio|"
    r"journal search failed|comfyui switch failed|"
    r"could not save memory setting|export failed|voice bench failed|"
    r"save failed|toggle failed|settings update failed|model switch failed|"
    r"could not clear conversation|another request is still finishing",
    re.I,
)


def _ensure() -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)


def _read_all() -> list[dict[str, Any]]:
    _ensure()
    if not INBOX_FILE.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in INBOX_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict) and row.get("id"):
                rows.append(row)
        except json.JSONDecodeError:
            continue
    return rows


def _write_all(rows: list[dict[str, Any]]) -> None:
    _ensure()
    tmp = INBOX_FILE.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for row in rows[-_MAX:]:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    tmp.replace(INBOX_FILE)


def _is_noise(row: dict[str, Any] | None) -> bool:
    """Empty / non-actionable rows must not inflate the durable inbox (BUG-003)."""
    if not isinstance(row, dict):
        return True
    title = str(row.get("title") or "").strip()
    body = str(row.get("body") or row.get("message") or "").strip()
    if title or body:
        return False
    return True


def is_cancellation_event(title: str = "", body: str = "") -> bool:
    blob = f"{title} {body}".strip()
    if not blob:
        return False
    return bool(_CANCEL_RE.search(blob))


def classify_channel(title: str = "", body: str = "", source: str = "") -> str:
    """Owner inbox vs engineering diagnostics vs development vs cancelled."""
    blob = f"{title} {body} {source}".strip()
    if is_cancellation_event(title, body):
        return "cancelled"
    if str(title or "").strip().lower() in {"notification", "notice"}:
        return "engineering"
    try:
        from jarvis.integrity_product.tags import looks_like_dev_label

        if looks_like_dev_label(blob):
            return "development"
    except Exception:
        pass
    src = str(source or "").lower()
    if src in {"toast", "system", "mission", "client"} and _ENGINEERING_RE.search(blob):
        return "engineering"
    if _ENGINEERING_RE.search(f"{title} {body}"):
        return "engineering"
    return "owner"


def _read_engineering() -> list[dict[str, Any]]:
    _ensure()
    if not ENGINEERING_FILE.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in ENGINEERING_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except json.JSONDecodeError:
            continue
    return rows


def _append_engineering(item: dict[str, Any]) -> None:
    _ensure()
    with ENGINEERING_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")


def publish(
    *,
    kind: str = "info",
    title: str = "",
    body: str = "",
    source: str = "system",
    meta: dict | None = None,
    event_id: str | None = None,
    channel: str | None = None,
) -> dict[str, Any]:
    """Append an activity item. Idempotent if event_id matches an existing id."""
    title_s = str(title or "").strip()[:200]
    body_s = str(body or "").strip()[:2000]
    # BUG-003: never persist empty-title/empty-body events as durable unread.
    if not title_s and not body_s:
        return {"ok": True, "rejected": True, "reason": "empty_event"}
    if not title_s:
        title_s = body_s[:120]
    ch = (channel or classify_channel(title_s, body_s, source)).strip().lower() or "owner"
    if ch == "cancelled":
        return {"ok": True, "rejected": True, "reason": "cancelled", "channel": ch}
    item = {
        "id": (event_id or "").strip() or f"act-{uuid.uuid4().hex[:12]}",
        "ts": time.time(),
        "kind": kind or "info",
        "title": title_s,
        "body": body_s,
        "source": source or "system",
        "meta": meta or {},
        "channel": ch,
        "dismissed": False,
        "read": ch != "owner",
    }
    if ch in {"engineering", "development", "audit"}:
        with _lock:
            _append_engineering(item)
        return {"ok": True, "item": item, "channel": ch, "owner_visible": False}
    with _lock:
        rows = _read_all()
        eid = item["id"]
        for r in rows:
            if r.get("id") == eid:
                return {"ok": True, "item": r, "deduped": True}
        rows.append(item)
        rows = [r for r in rows if not _is_noise(r)]
        _write_all(rows)
        return {"ok": True, "item": item, "deduped": False, "channel": "owner"}


def list_items(
    *,
    include_dismissed: bool = False,
    limit: int = 100,
    channel: str = "owner",
) -> dict[str, Any]:
    with _lock:
        rows = _read_all()
        noise = [r for r in rows if _is_noise(r)]
        if noise:
            rows = [r for r in rows if not _is_noise(r)]
            _write_all(rows)
    if not include_dismissed:
        rows = [r for r in rows if not r.get("dismissed")]
    wanted = (channel or "owner").strip().lower()
    if wanted in {"engineering", "development", "audit"}:
        rows = _read_engineering()
        rows = [r for r in rows if str(r.get("channel") or wanted) == wanted or wanted == "engineering"]
        if wanted != "engineering":
            rows = [r for r in rows if str(r.get("channel") or "") == wanted]
    elif wanted and wanted != "all":
        filtered: list[dict[str, Any]] = []
        for r in rows:
            ch = str(r.get("channel") or classify_channel(
                str(r.get("title") or ""),
                str(r.get("body") or ""),
                str(r.get("source") or ""),
            ))
            if ch == "cancelled":
                continue
            if ch == wanted:
                filtered.append(r)
        rows = filtered
    rows = sorted(rows, key=lambda r: float(r.get("ts") or 0), reverse=True)
    limit = max(1, min(int(limit or 100), _MAX))
    unread = sum(1 for r in rows if not r.get("read") and not r.get("dismissed"))
    return {"ok": True, "items": rows[:limit], "count": len(rows), "unread": unread, "channel": wanted}


def reclassify_inbox() -> dict[str, Any]:
    """Move engineering/test/cancellation rows out of the owner inbox. Does not invent owner events."""
    moved = 0
    cancelled = 0
    kept = 0
    with _lock:
        rows = _read_all()
        owner_rows: list[dict[str, Any]] = []
        for r in rows:
            title = str(r.get("title") or "")
            body = str(r.get("body") or "")
            source = str(r.get("source") or "")
            ch = classify_channel(title, body, source)
            r["channel"] = ch
            if ch == "cancelled":
                cancelled += 1
                continue
            if ch in {"engineering", "development", "audit"}:
                r["read"] = True
                _append_engineering(r)
                moved += 1
                continue
            owner_rows.append(r)
            kept += 1
        _write_all(owner_rows)
    return {"ok": True, "kept_owner": kept, "moved_engineering": moved, "dropped_cancelled": cancelled}


def dismiss(item_id: str) -> dict[str, Any]:
    iid = (item_id or "").strip()
    if not iid:
        return {"ok": False, "message": "id required"}
    with _lock:
        rows = _read_all()
        found = False
        for r in rows:
            if r.get("id") == iid:
                r["dismissed"] = True
                r["dismissed_at"] = time.time()
                found = True
                break
        if not found:
            return {"ok": False, "message": "not found"}
        _write_all(rows)
    return {"ok": True, "id": iid}


def mark_read(item_id: str) -> dict[str, Any]:
    iid = (item_id or "").strip()
    if not iid:
        return {"ok": False, "message": "id required"}
    with _lock:
        rows = _read_all()
        found = False
        for r in rows:
            if r.get("id") == iid:
                r["read"] = True
                found = True
                break
        if not found:
            return {"ok": False, "message": "not found"}
        _write_all(rows)
    return {"ok": True, "id": iid}


def mark_all_read() -> dict[str, Any]:
    now = time.time()
    with _lock:
        rows = _read_all()
        changed = 0
        for r in rows:
            if not r.get("dismissed") and not r.get("read"):
                r["read"] = True
                r["read_at"] = now
                changed += 1
        _write_all(rows)
    return {"ok": True, "updated": changed}


def clear_read() -> dict[str, Any]:
    with _lock:
        rows = _read_all()
        kept = [r for r in rows if not r.get("read")]
        removed = len(rows) - len(kept)
        _write_all(kept)
    return {"ok": True, "removed": removed, "remaining": len(kept)}


def clear_all() -> dict[str, Any]:
    with _lock:
        rows = _read_all()
        removed = len(rows)
        _write_all([])
    return {"ok": True, "removed": removed, "remaining": 0}


def clear_dismissed() -> dict[str, Any]:
    with _lock:
        rows = [r for r in _read_all() if not r.get("dismissed")]
        _write_all(rows)
    return {"ok": True, "remaining": len(rows)}
