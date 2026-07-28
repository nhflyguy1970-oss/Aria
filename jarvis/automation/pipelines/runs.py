"""Durable pipeline run history — survives restart."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

from jarvis.automation.paths import AUTOMATION_ROOT, ensure_dirs

RUNS_FILE = AUTOMATION_ROOT / "pipeline_runs.json"
_MAX = 200
_lock = threading.Lock()


def _load() -> list[dict[str, Any]]:
    ensure_dirs()
    if not RUNS_FILE.is_file():
        return []
    try:
        data = json.loads(RUNS_FILE.read_text(encoding="utf-8"))
        return list(data.get("runs") or [])
    except Exception:
        return []


def _save(runs: list[dict[str, Any]]) -> None:
    ensure_dirs()
    try:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(RUNS_FILE)
    except Exception:
        pass
    RUNS_FILE.write_text(
        json.dumps({"runs": runs[-_MAX:], "updated_at": time.time()}, indent=2, default=str),
        encoding="utf-8",
    )


def record_pipeline_run(payload: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "id": payload.get("run_id"),
        "correlation_id": payload.get("correlation_id"),
        "pipeline_id": payload.get("pipeline_id") or payload.get("workflow_id"),
        "name": payload.get("name"),
        "version": payload.get("version"),
        "status": payload.get("status"),
        "dry_run": bool(payload.get("dry_run")),
        "trigger": payload.get("trigger") or "manual",
        "elapsed_ms": payload.get("elapsed_ms"),
        "job_id": payload.get("job_id"),
        "variables": payload.get("variables") or {},
        "log": payload.get("log") or [],
        "success_summary": payload.get("success_summary") or "",
        "failure_summary": payload.get("failure_summary") or "",
        "from_step": payload.get("from_step"),
        "created_at": time.time(),
        "user": "local",
    }
    with _lock:
        runs = _load()
        runs.append(entry)
        _save(runs)
    return entry


def list_pipeline_runs(
    *,
    limit: int = 50,
    pipeline_id: str | None = None,
    status: str | None = None,
    q: str = "",
) -> list[dict[str, Any]]:
    with _lock:
        runs = list(reversed(_load()))
    if pipeline_id:
        runs = [r for r in runs if r.get("pipeline_id") == pipeline_id]
    if status:
        runs = [r for r in runs if r.get("status") == status]
    ql = (q or "").strip().lower()
    if ql:
        runs = [
            r
            for r in runs
            if ql in (r.get("name") or "").lower()
            or ql in (r.get("id") or "").lower()
            or ql in (r.get("status") or "").lower()
            or ql in (r.get("failure_summary") or "").lower()
        ]
    return runs[:limit]


def get_pipeline_run(run_id: str) -> dict[str, Any] | None:
    with _lock:
        for r in reversed(_load()):
            if r.get("id") == run_id:
                return r
    return None


def last_run(pipeline_id: str) -> dict[str, Any] | None:
    for r in list_pipeline_runs(limit=50, pipeline_id=pipeline_id):
        if not r.get("dry_run"):
            return r
    runs = list_pipeline_runs(limit=1, pipeline_id=pipeline_id)
    return runs[0] if runs else None


def last_failure(pipeline_id: str | None = None) -> dict[str, Any] | None:
    for r in list_pipeline_runs(limit=100, pipeline_id=pipeline_id, status="failed"):
        return r
    return None


def clear_pipeline_runs() -> dict[str, Any]:
    with _lock:
        _save([])
    return {"ok": True}
