"""Persist Audio tab session (last path, transcript, summary)."""

from __future__ import annotations

import json

from jarvis.config import DATA_DIR

SESSION_FILE = DATA_DIR / "audio" / "session.json"


def load_session() -> dict:
    if not SESSION_FILE.exists():
        return {}
    try:
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_session(patch: dict) -> dict:
    data = load_session()
    data.update({k: v for k, v in patch.items() if v is not None})
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
