"""Append-only notification history (server-side; Activity Center remains durable inbox)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.notifications_product.schema import normalize_event

ROOT = Path(DATA_DIR) / "notifications_product"
HISTORY_FILE = ROOT / "history.jsonl"
MAX_LINES = 2000


def _ensure() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)


def append_history(evt: dict[str, Any]) -> None:
    try:
        from jarvis.notifications_product.preferences import load_preferences

        if not load_preferences().get("history_enabled", True):
            return
    except Exception:
        pass
    _ensure()
    row = normalize_event(evt)
    row["recorded_at"] = time.time()
    try:
        with HISTORY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")
    except OSError:
        return
    # Trim occasionally
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) > MAX_LINES:
            HISTORY_FILE.write_text("\n".join(lines[-MAX_LINES:]) + "\n", encoding="utf-8")
    except OSError:
        pass


def load_history(*, limit: int = 100, unread_only: bool = False, severity: str = "") -> list[dict[str, Any]]:
    if not HISTORY_FILE.is_file():
        return []
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if unread_only and item.get("read"):
            continue
        if severity and str(item.get("severity") or "") != severity:
            continue
        out.append(item)
        if len(out) >= limit:
            break
    return out


def export_history(*, limit: int = 500) -> dict[str, Any]:
    items = load_history(limit=limit)
    return {
        "format": "aria_notifications_history",
        "count": len(items),
        "events": items,
    }


def retention_prune(*, days: int | None = None) -> int:
    from jarvis.notifications_product.preferences import load_preferences

    prefs = load_preferences()
    days = int(days if days is not None else prefs.get("retention_days") or 30)
    cutoff = time.time() - max(1, days) * 86400
    if not HISTORY_FILE.is_file():
        return 0
    try:
        lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 0
    kept = []
    removed = 0
    for line in lines:
        try:
            item = json.loads(line)
            ts = float(item.get("timestamp") or item.get("recorded_at") or 0)
            if ts and ts < cutoff:
                removed += 1
                continue
        except Exception:
            pass
        kept.append(line)
    try:
        HISTORY_FILE.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
    except OSError:
        return 0
    return removed
