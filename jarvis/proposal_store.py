"""Persist pending code proposals across restarts."""

from __future__ import annotations

import json

from jarvis.config import DATA_DIR

PROPOSALS_FILE = DATA_DIR / "pending_proposals.json"


def load() -> dict[str, dict]:
    if not PROPOSALS_FILE.exists():
        return {}
    try:
        data = json.loads(PROPOSALS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save(proposals: dict[str, dict]) -> None:
    PROPOSALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Strip non-serializable internal keys
    clean = {}
    for pid, p in proposals.items():
        clean[pid] = {k: v for k, v in p.items() if not k.startswith("_")}
    PROPOSALS_FILE.write_text(json.dumps(clean, indent=2), encoding="utf-8")


def sync(proposals: dict[str, dict]) -> None:
    save(proposals)
