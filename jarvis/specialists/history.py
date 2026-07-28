"""Durable Specialist Team run history."""

from __future__ import annotations

import json
import threading
import time
from typing import Any

from jarvis.config import DATA_DIR

RUNS_FILE = DATA_DIR / "specialists" / "runs.json"
_MAX = 200
_lock = threading.Lock()


def _load() -> list[dict[str, Any]]:
    RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not RUNS_FILE.is_file():
        return []
    try:
        return list(json.loads(RUNS_FILE.read_text(encoding="utf-8")).get("runs") or [])
    except Exception:
        return []


def _save(runs: list[dict[str, Any]]) -> None:
    RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(RUNS_FILE)
    except Exception:
        pass
    RUNS_FILE.write_text(
        json.dumps({"runs": runs[-_MAX:], "updated_at": time.time()}, indent=2, default=str),
        encoding="utf-8",
    )


def record_run(payload: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "id": payload.get("run_id"),
        "goal": payload.get("goal"),
        "status": payload.get("status"),
        "team": payload.get("team") or payload.get("specialists") or [],
        "steps": payload.get("steps") or [],
        "scratchpad": payload.get("scratchpad") or {},
        "synthesis": payload.get("synthesis") or "",
        "elapsed_ms": payload.get("elapsed_ms"),
        "job_id": payload.get("job_id"),
        "correlation_id": payload.get("correlation_id"),
        "budget": payload.get("budget") or {},
        "trigger": payload.get("trigger") or "manual",
        "permissions": payload.get("permissions") or [],
        "created_at": time.time(),
        "ok": payload.get("ok"),
        "partial": payload.get("status") == "partial_success",
    }
    with _lock:
        runs = _load()
        runs.append(entry)
        _save(runs)
    return entry


def list_runs(*, limit: int = 40, status: str | None = None, q: str = "") -> list[dict[str, Any]]:
    with _lock:
        runs = list(reversed(_load()))
    if status:
        runs = [r for r in runs if r.get("status") == status]
    ql = (q or "").strip().lower()
    if ql:
        runs = [
            r
            for r in runs
            if ql in (r.get("goal") or "").lower()
            or ql in (r.get("id") or "").lower()
            or ql in " ".join(r.get("team") or []).lower()
            or ql in (r.get("synthesis") or "").lower()
        ]
    return runs[:limit]


def get_run(run_id: str) -> dict[str, Any] | None:
    with _lock:
        for r in reversed(_load()):
            if r.get("id") == run_id:
                return r
    return None


def search_runs(q: str, *, limit: int = 40) -> list[dict[str, Any]]:
    return list_runs(limit=limit, q=q)
