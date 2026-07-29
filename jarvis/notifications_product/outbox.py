"""Drain product activity outboxes into the Notifications pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.notifications_product.pipeline import publish

OUTBOXES: list[tuple[str, Path]] = [
    ("gallery", DATA_DIR / "gallery_product" / "activity_outbox.jsonl"),
    ("browser", DATA_DIR / "browser_product" / "activity_outbox.jsonl"),
    ("models", DATA_DIR / "models_product" / "activity_outbox.jsonl"),
    ("automation", DATA_DIR / "automation" / "activity_outbox.jsonl"),
    ("coding", DATA_DIR / "coding_product" / "activity_outbox.jsonl"),
    ("vision", DATA_DIR / "vision_product" / "activity_outbox.jsonl"),
    ("voice", DATA_DIR / "voice_product" / "activity_outbox.jsonl"),
    ("planner", DATA_DIR / "planner" / "activity_outbox.jsonl"),
]


def _read_and_clear(path: Path, *, limit: int = 80) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").strip().splitlines()
    except OSError:
        return []
    events: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    try:
        path.write_text("", encoding="utf-8")
    except OSError:
        pass
    return events


def drain_all(*, limit_per: int = 50) -> dict[str, Any]:
    published: list[dict[str, Any]] = []
    by_source: dict[str, int] = {}
    activity_batch: list[dict[str, Any]] = []
    for source, path in OUTBOXES:
        events = _read_and_clear(path, limit=limit_per)
        # Models may also expose drain_outbox
        if source == "models" and not events:
            try:
                from jarvis.models_product.activity_bridge import drain_outbox

                events = drain_outbox(limit=limit_per)
            except Exception:
                events = []
        for raw in events:
            raw = dict(raw)
            raw.setdefault("source", source)
            raw.setdefault("product", source)
            raw.setdefault("category", source)
            result = publish(raw)
            by_source[source] = by_source.get(source, 0) + 1
            if result.get("ok") and not result.get("suppressed"):
                published.append(result.get("event") or {})
                if result.get("activity"):
                    activity_batch.append(result["activity"])
    return {
        "ok": True,
        "drained": sum(by_source.values()),
        "by_source": by_source,
        "events": published[:40],
        "activity_batch": activity_batch[:80],
    }


def outbox_status() -> list[dict[str, Any]]:
    rows = []
    for source, path in OUTBOXES:
        pending = 0
        if path.is_file():
            try:
                pending = len([ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()])
            except OSError:
                pending = -1
        rows.append({"source": source, "path": str(path), "pending": pending})
    return rows
