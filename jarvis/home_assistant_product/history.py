"""Smart Home history — control / scene / status events (shared censored/uncensored storage)."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from jarvis.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "home_assistant_product" / "history.jsonl"
MAX_ENTRIES = 500


def add_entry(entry: dict[str, Any]) -> dict[str, Any]:
    row = {
        "id": entry.get("id") or uuid.uuid4().hex[:16],
        "ts": entry.get("ts") or time.time(),
        "kind": entry.get("kind") or "event",  # control | scene | status | vision | voice | note
        "entity_id": entry.get("entity_id") or "",
        "entity_name": entry.get("entity_name") or "",
        "scene": entry.get("scene") or "",
        "action": entry.get("action") or "",
        "summary": (entry.get("summary") or "")[:2000],
        "detail": (entry.get("detail") or "")[:8000],
        "path": entry.get("path") or "",
        "source": entry.get("source") or "api",
        "uncensored_origin": bool(entry.get("uncensored_origin")),
        "meta": entry.get("meta") or {},
    }
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    _trim()
    return row


def _trim() -> None:
    if not HISTORY_FILE.is_file():
        return
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > MAX_ENTRIES:
            HISTORY_FILE.write_text("\n".join(lines[-MAX_ENTRIES:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def list_history(*, limit: int = 50, q: str = "", kind: str = "") -> list[dict[str, Any]]:
    if not HISTORY_FILE.is_file():
        return []
    q = (q or "").strip().lower()
    kind = (kind or "").strip().lower()
    rows: list[dict[str, Any]] = []
    try:
        for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if kind and str(row.get("kind") or "").lower() != kind:
                continue
            if q:
                blob = " ".join(
                    str(row.get(k) or "")
                    for k in (
                        "summary",
                        "detail",
                        "entity_id",
                        "entity_name",
                        "scene",
                        "action",
                        "kind",
                        "source",
                    )
                ).lower()
                if q not in blob:
                    continue
            rows.append(row)
    except OSError:
        return []
    rows.reverse()
    return rows[: max(1, min(limit, 200))]


def get_entry(entry_id: str) -> dict[str, Any] | None:
    for row in list_history(limit=500):
        if row.get("id") == entry_id:
            return row
    return None


def presentation_for_profile(
    entry: dict[str, Any],
    *,
    censored: bool,
    reveal: bool = False,
) -> dict[str, Any]:
    """
    Censored vs uncensored share storage. Presentation-only redaction.
    Never regenerate or delete original Smart Home events.
    """
    out = dict(entry)
    if not censored or reveal or not entry.get("uncensored_origin"):
        out["redacted"] = False
        return out
    out["detail"] = "[Restricted — reveal to view detail]"
    out["summary"] = out.get("summary") or "[Restricted]"
    out["redacted"] = True
    out["has_original"] = True
    return out
