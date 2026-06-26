"""Action history for Jarvis."""

import json
from datetime import datetime, timezone

from jarvis.config import DATA_DIR

LOG_FILE = DATA_DIR / "action_log.json"
MAX_ENTRIES = 200


def _load() -> list:
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _save(entries: list) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(entries[-MAX_ENTRIES:], indent=2), encoding="utf-8")


def log_action(action: str, module: str = "", detail: str = "", ok: bool = True) -> None:
    log_event("action", action=action, module=module, detail=detail[:500], ok=ok)


def log_event(event: str, **fields) -> None:
    """Structured append-only event log (JSON lines in action_log.json list)."""
    entries = _load()
    row = {
        "time": datetime.now(timezone.utc).isoformat(),
        "event": event,
    }
    for key, val in fields.items():
        if val is not None:
            row[key] = val
    entries.append(row)
    _save(entries)


def list_actions(limit: int = 50, module: str = "") -> list:
    rows = _load()[-limit * 3:][::-1]
    mod = (module or "").strip().lower()
    if mod:
        rows = [r for r in rows if (r.get("module") or "").lower() == mod or (r.get("action") or "").lower().startswith(mod)]
    return rows[:limit]


def clear_log() -> None:
    _save([])
