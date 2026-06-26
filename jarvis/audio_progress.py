"""In-memory progress for long audio jobs (music, song studio)."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any

_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}


class JobCancelled(Exception):
    """Raised when user cancels a long audio job."""


def start_job(label: str) -> str:
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "label": label,
            "pct": 0,
            "message": "Starting…",
            "done": False,
            "cancelled": False,
            "error": "",
            "result": None,
            "started": time.time(),
        }
    return job_id


def cancel_job(job_id: str) -> bool:
    with _lock:
        job = _jobs.get(job_id)
        if not job or job.get("done"):
            return False
        job["cancelled"] = True
        job["message"] = "Cancelling…"
        return True


def is_cancelled(job_id: str | None) -> bool:
    if not job_id:
        return False
    with _lock:
        job = _jobs.get(job_id)
        return bool(job and job.get("cancelled"))


def check_cancelled(job_id: str | None) -> None:
    if is_cancelled(job_id):
        raise JobCancelled("Cancelled by user")


def update_job(job_id: str, pct: int, message: str = "") -> None:
    check_cancelled(job_id)
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job["pct"] = max(0, min(100, int(pct)))
        if message:
            job["message"] = message


def finish_job(job_id: str, result: Any = None, error: str = "") -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        job["done"] = True
        if job.get("cancelled") and not error:
            error = "Cancelled by user"
        job["pct"] = 100 if not error else job["pct"]
        job["result"] = result
        job["error"] = error
        job["message"] = error or "Complete"


def get_job(job_id: str) -> dict | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def job_stats() -> dict[str, Any]:
    with _lock:
        active = [j for j in _jobs.values() if not j.get("done")]
        return {
            "busy": bool(active),
            "pending": 0,
            "active_count": len(active),
            "active_id": active[0]["id"] if active else None,
            "tracked_jobs": len(_jobs),
        }


def list_recent(limit: int = 10) -> list[dict]:
    with _lock:
        items = sorted(
            (_jobs[jid] for jid in _jobs),
            key=lambda j: j.get("started") or 0,
            reverse=True,
        )
        return [dict(j) for j in items[:limit]]
