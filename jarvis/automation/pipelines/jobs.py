"""Lightweight Job Center bridge for pipeline runs (live execution tracking)."""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections import deque
from typing import Any

from jarvis.automation.paths import AUTOMATION_ROOT, ensure_dirs

_STATE_FILE = AUTOMATION_ROOT / "pipeline_jobs.json"
_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}
_history: deque[str] = deque(maxlen=40)
_loaded = False


def _persist() -> None:
    ensure_dirs()
    try:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(_STATE_FILE)
    except Exception:
        pass
    with _lock:
        payload = {
            "jobs": [dict(_jobs[i]) for i in list(_history) if i in _jobs][-40:],
            "updated_at": time.time(),
        }
    try:
        _STATE_FILE.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    except OSError:
        pass


def _load() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    if not _STATE_FILE.is_file():
        return
    try:
        data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return
    with _lock:
        for item in data.get("jobs") or []:
            jid = item.get("id")
            if jid:
                _jobs[jid] = item
                _history.append(jid)


def start_job(
    *,
    run_id: str,
    pipeline_id: str,
    name: str,
    dry_run: bool = False,
    correlation_id: str = "",
) -> str:
    _load()
    jid = f"pipe_{uuid.uuid4().hex[:10]}"
    job = {
        "id": jid,
        "queue": "automation",
        "kind": "pipeline",
        "label": name,
        "run_id": run_id,
        "pipeline_id": pipeline_id,
        "correlation_id": correlation_id,
        "pct": 0,
        "message": "queued",
        "status": "queued",
        "done": False,
        "error": "",
        "started": time.time(),
        "cancelled": False,
        "dry_run": dry_run,
    }
    with _lock:
        _jobs[jid] = job
        _history.append(jid)
    _persist()
    return jid


def update_job(job_id: str, **fields: Any) -> None:
    _load()
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        if "status" in fields:
            job["status"] = fields["status"]
        if "pct" in fields:
            job["pct"] = fields["pct"]
        if "message" in fields:
            job["message"] = fields["message"]
        if "current_step" in fields:
            job["current_step"] = fields["current_step"]
        if fields.get("done"):
            job["done"] = True
        if fields.get("error"):
            job["error"] = str(fields["error"])
    _persist()


def finish_job(job_id: str, *, status: str, result: dict[str, Any] | None = None) -> None:
    _load()
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job["status"] = status
        job["done"] = True
        job["pct"] = 100
        job["message"] = status
        if status == "failed":
            job["error"] = (result or {}).get("failure_summary") or "failed"
        if status == "cancelled":
            job["cancelled"] = True
        if result:
            job["result_ok"] = bool(result.get("ok"))
            job["result_message"] = (
                result.get("success_summary") or result.get("failure_summary") or ""
            )[:200]
    _persist()


def list_jobs(*, limit: int = 20) -> list[dict[str, Any]]:
    _load()
    with _lock:
        ids = list(_history)[-limit:]
        out = [dict(_jobs[i]) for i in reversed(ids) if i in _jobs]
    return out[:limit]


def get_job(job_id: str) -> dict[str, Any] | None:
    _load()
    with _lock:
        j = _jobs.get(job_id)
        return dict(j) if j else None


def busy() -> bool:
    _load()
    with _lock:
        return any(not j.get("done") for j in _jobs.values())
