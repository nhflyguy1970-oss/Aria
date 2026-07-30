"""Provider health event history (JSONL) — diagnostics / Search index source."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "provider_health" / "history.jsonl"
_MAX_LINES = 2000


def append_event(event: dict[str, Any]) -> dict[str, Any]:
    row = {
        **event,
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")
    _trim()
    return row


def load_history(*, limit: int = 80) -> list[dict[str, Any]]:
    if not HISTORY_FILE.is_file():
        return []
    lines = HISTORY_FILE.read_text(encoding="utf-8").strip().splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(out))


def search_history(query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    q = (query or "").lower().strip()
    if not q:
        return load_history(limit=limit)
    hits = []
    for row in load_history(limit=400):
        blob = json.dumps(row, default=str).lower()
        if q in blob:
            hits.append(row)
        if len(hits) >= limit:
            break
    return hits


def _trim() -> None:
    if not HISTORY_FILE.is_file():
        return
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > _MAX_LINES:
            HISTORY_FILE.write_text("\n".join(lines[-_MAX_LINES:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def history_path() -> Path:
    return HISTORY_FILE
