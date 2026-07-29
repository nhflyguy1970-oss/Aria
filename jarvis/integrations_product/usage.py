"""Redacted usage / activity log for Integrations."""

from __future__ import annotations

import json
import time
from typing import Any

from jarvis.config import DATA_DIR

USAGE_FILE = DATA_DIR / "integrations_product" / "usage.json"
MAX_EVENTS = 300


def _load() -> list[dict[str, Any]]:
    if not USAGE_FILE.is_file():
        return []
    try:
        raw = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [e for e in raw if isinstance(e, dict)]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save(events: list[dict[str, Any]]) -> None:
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(events[-MAX_EVENTS:], indent=2), encoding="utf-8")


def record_usage(
    provider_id: str,
    *,
    action: str,
    ok: bool,
    latency_ms: int | None = None,
    status: str = "",
    message: str = "",
) -> dict[str, Any]:
    # Never accept or store secret material
    msg = (message or "")[:400]
    for needle in ("sk-", "AIza", "hf_", "Bearer ", "token="):
        if needle.lower() in msg.lower():
            msg = "[redacted]"
            break
    event = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provider_id": provider_id,
        "action": action,
        "ok": bool(ok),
        "latency_ms": latency_ms,
        "status": status,
        "message": msg,
    }
    events = _load()
    events.append(event)
    _save(events)
    return event


def list_usage(limit: int = 50, *, provider_id: str = "") -> list[dict[str, Any]]:
    events = _load()
    if provider_id:
        events = [e for e in events if e.get("provider_id") == provider_id]
    return list(reversed(events[-max(1, limit) :]))


def clear_usage() -> None:
    _save([])
