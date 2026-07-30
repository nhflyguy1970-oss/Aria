"""In-memory stream watchdog / request timing (negligible overhead)."""

from __future__ import annotations

import threading
import time
from typing import Any

_lock = threading.Lock()
_ACTIVE: dict[str, dict[str, Any]] = {}
_LAST_COMPLETED: dict[str, Any] | None = None
_STATS = {
    "requests": 0,
    "timeouts": 0,
    "recoveries": 0,
    "recovery_success": 0,
    "last_error": None,
    "last_success_at": None,
}


def begin_request(
    request_id: str,
    *,
    provider: str = "ollama",
    model: str = "",
    prompt_chars: int = 0,
) -> dict[str, Any]:
    rid = (request_id or f"anon-{time.time_ns()}").strip()
    row = {
        "request_id": rid,
        "provider": provider,
        "model": model,
        "prompt_chars": prompt_chars,
        "started_at": time.time(),
        "first_token_at": None,
        "last_token_at": None,
        "token_count": 0,
        "heartbeat_count": 0,
        "last_heartbeat_at": None,
        "state": "loading",
        "exit_reason": None,
        "completion_reason": None,
        "cancelled": False,
        "timeout": False,
        "classified": None,
    }
    with _lock:
        _ACTIVE[rid] = row
        _STATS["requests"] += 1
    return dict(row)


def note_heartbeat(request_id: str) -> None:
    with _lock:
        row = _ACTIVE.get(request_id)
        if not row:
            return
        row["heartbeat_count"] = int(row.get("heartbeat_count") or 0) + 1
        row["last_heartbeat_at"] = time.time()
        if row.get("state") == "loading":
            row["state"] = "busy"


def note_token(request_id: str, *, n: int = 1) -> None:
    now = time.time()
    with _lock:
        row = _ACTIVE.get(request_id)
        if not row:
            return
        if row.get("first_token_at") is None:
            row["first_token_at"] = now
        row["last_token_at"] = now
        row["token_count"] = int(row.get("token_count") or 0) + max(1, n)
        row["state"] = "generating"


def complete_request(
    request_id: str,
    *,
    reason: str = "done",
    timeout: bool = False,
    cancelled: bool = False,
    classified: dict[str, Any] | None = None,
    error: str = "",
) -> dict[str, Any] | None:
    global _LAST_COMPLETED
    with _lock:
        row = _ACTIVE.pop(request_id, None)
        if not row:
            return None
        row["ended_at"] = time.time()
        row["exit_reason"] = reason
        row["completion_reason"] = reason
        row["timeout"] = timeout
        row["cancelled"] = cancelled
        row["classified"] = classified
        row["error"] = error
        row["duration_ms"] = int((row["ended_at"] - row["started_at"]) * 1000)
        if row.get("first_token_at") and row.get("last_token_at") and row.get("token_count"):
            span = max(0.001, row["last_token_at"] - row["first_token_at"])
            row["tokens_per_sec"] = round(row["token_count"] / span, 2)
        else:
            row["tokens_per_sec"] = None
        if timeout:
            _STATS["timeouts"] += 1
            _STATS["last_error"] = error or reason
            row["state"] = "crashed" if classified and classified.get("class") == "model_crashed" else "degraded"
        elif cancelled:
            row["state"] = "unknown"
        else:
            row["state"] = "healthy"
            _STATS["last_success_at"] = row["ended_at"]
        _LAST_COMPLETED = dict(row)
        return dict(row)


def active_requests() -> list[dict[str, Any]]:
    with _lock:
        return [dict(v) for v in _ACTIVE.values()]


def stats() -> dict[str, Any]:
    with _lock:
        return {
            **dict(_STATS),
            "active": len(_ACTIVE),
            "last_completed": dict(_LAST_COMPLETED) if _LAST_COMPLETED else None,
        }


def note_recovery(*, success: bool) -> None:
    with _lock:
        _STATS["recoveries"] += 1
        if success:
            _STATS["recovery_success"] += 1
