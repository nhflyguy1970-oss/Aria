"""Job Center bridge for Specialist Team runs."""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections import deque
from typing import Any

from jarvis.config import DATA_DIR

_STATE_FILE = DATA_DIR / "specialists" / "jobs.json"
_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}
_history: deque[str] = deque(maxlen=50)
_cancel: set[str] = set()
_loaded = False


def _persist() -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        payload = {"jobs": [dict(_jobs[i]) for i in list(_history) if i in _jobs][-40:]}
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


def start_team_job(*, run_id: str, goal: str, team: list[str], correlation_id: str = "") -> str:
    _load()
    jid = f"team_{uuid.uuid4().hex[:10]}"
    job = {
        "id": jid,
        "queue": "specialists",
        "kind": "specialist_team",
        "label": f"Team: {goal[:60]}",
        "run_id": run_id,
        "team": team,
        "correlation_id": correlation_id,
        "pct": 0,
        "message": "queued",
        "status": "queued",
        "done": False,
        "error": "",
        "started": time.time(),
        "cancelled": False,
        "goal": goal,
    }
    with _lock:
        _jobs[jid] = job
        _history.append(jid)
        _cancel.discard(jid)
    _persist()
    return jid


def update_team_job(job_id: str, **fields: Any) -> None:
    _load()
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        for k in ("status", "pct", "message", "current"):
            if k in fields:
                job[k if k != "current" else "current_specialist"] = fields[k]
        if fields.get("done"):
            job["done"] = True
    _persist()


def finish_team_job(job_id: str, *, status: str, result: dict[str, Any] | None = None) -> None:
    _load()
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job["status"] = status
        job["done"] = True
        job["pct"] = 100
        job["message"] = status
        if status == "cancelled":
            job["cancelled"] = True
        if status == "failed":
            job["error"] = (result or {}).get("error") or "failed"
        if result:
            job["result_ok"] = bool(result.get("ok"))
            job["run_id"] = result.get("run_id") or job.get("run_id")
    _persist()


def request_cancel(job_id: str) -> dict[str, Any]:
    _load()
    with _lock:
        if job_id not in _jobs:
            return {"ok": False, "error": "not_found"}
        _cancel.add(job_id)
        _jobs[job_id]["message"] = "cancel requested"
    return {"ok": True, "cancelled": True, "id": job_id}


def is_cancelled(job_id: str) -> bool:
    with _lock:
        return job_id in _cancel


def list_jobs(*, limit: int = 20) -> list[dict[str, Any]]:
    _load()
    with _lock:
        ids = list(_history)[-limit:]
        return [dict(_jobs[i]) for i in reversed(ids) if i in _jobs][:limit]


def get_job(job_id: str) -> dict[str, Any] | None:
    _load()
    with _lock:
        j = _jobs.get(job_id)
        return dict(j) if j else None


def busy() -> bool:
    _load()
    with _lock:
        return any(not j.get("done") for j in _jobs.values())
