"""Vision batch queue — progress, cancel, retry."""

from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}
_cancel: set[str] = set()


def list_jobs() -> list[dict[str, Any]]:
    with _lock:
        return [dict(j) for j in sorted(_jobs.values(), key=lambda x: x.get("started") or 0, reverse=True)]


def get_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        j = _jobs.get(job_id)
        return dict(j) if j else None


def cancel_job(job_id: str) -> dict[str, Any]:
    _cancel.add(job_id)
    with _lock:
        job = _jobs.get(job_id)
        if job and job.get("status") in ("queued", "running"):
            job["status"] = "cancelling"
    return {"ok": True, "job_id": job_id}


def start_batch(
    paths: list[str],
    *,
    action: str = "describe",
    source: str = "batch",
    assistant=None,
) -> dict[str, Any]:
    job_id = uuid.uuid4().hex[:12]
    files = [p for p in paths if Path(p).is_file()][:30]
    job = {
        "id": job_id,
        "status": "queued",
        "action": action,
        "total": len(files),
        "done": 0,
        "failed": 0,
        "results": [],
        "started": time.time(),
        "source": source,
    }
    with _lock:
        _jobs[job_id] = job

    def _run() -> None:
        from jarvis.vision_product.engine import analyze
        from jarvis.vision_product.status_bus import set_vision_state

        with _lock:
            _jobs[job_id]["status"] = "running"
        set_vision_state("batch", detail=job_id, task=action, progress=0)
        for i, path in enumerate(files):
            if job_id in _cancel:
                with _lock:
                    _jobs[job_id]["status"] = "cancelled"
                set_vision_state("idle", detail="batch-cancelled")
                return
            out = analyze(path=path, action=action, source=source, assistant=assistant, force=True)
            with _lock:
                row = _jobs[job_id]
                row["done"] = i + 1
                if out.get("ok"):
                    row["results"].append({"path": path, "ok": True, "preview": str(out.get("message") or "")[:200]})
                else:
                    row["failed"] = int(row.get("failed") or 0) + 1
                    row["results"].append({"path": path, "ok": False, "error": out.get("error")})
                row["progress"] = (i + 1) / max(1, len(files))
            set_vision_state("batch", detail=job_id, progress=(i + 1) / max(1, len(files)))
        with _lock:
            _jobs[job_id]["status"] = "done"
            _jobs[job_id]["finished"] = time.time()
        set_vision_state("idle", detail="batch-done", progress=1)

    threading.Thread(target=_run, daemon=True, name=f"vision-batch-{job_id}").start()
    return {"ok": True, "job": get_job(job_id)}


def retry_job(job_id: str, *, assistant=None) -> dict[str, Any]:
    job = get_job(job_id)
    if not job:
        return {"ok": False, "error": "job_not_found"}
    failed = [r["path"] for r in (job.get("results") or []) if not r.get("ok") and r.get("path")]
    if not failed:
        return {"ok": False, "error": "nothing_to_retry"}
    return start_batch(failed, action=job.get("action") or "describe", source="batch-retry", assistant=assistant)
