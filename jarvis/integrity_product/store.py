"""Integrity findings + repair history store (never auto-deletes user data)."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

INTEGRITY_DIR = DATA_DIR / "integrity_product"
LAST_SCAN_FILE = INTEGRITY_DIR / "last_scan.json"
HISTORY_FILE = INTEGRITY_DIR / "history.jsonl"

_lock = threading.RLock()


def ensure_dirs() -> None:
    INTEGRITY_DIR.mkdir(parents=True, exist_ok=True)


def save_last_scan(payload: dict[str, Any]) -> None:
    ensure_dirs()
    with _lock:
        LAST_SCAN_FILE.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def load_last_scan() -> dict[str, Any] | None:
    if not LAST_SCAN_FILE.is_file():
        return None
    try:
        data = json.loads(LAST_SCAN_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def append_history(entry: dict[str, Any]) -> None:
    ensure_dirs()
    row = {"ts": time.time(), **entry}
    with _lock:
        with HISTORY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")


def list_history(*, limit: int = 40) -> list[dict[str, Any]]:
    if not HISTORY_FILE.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(rows) >= limit:
                break
    except OSError:
        return []
    return rows
