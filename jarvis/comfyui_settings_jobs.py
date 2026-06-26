"""Background ComfyUI settings changes (mode/checkpoint restart can take ~2 min)."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Callable

from jarvis.metrics import note_comfyui_settings_job

_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}


def _run_job(job_id: str, fn: Callable[[], dict]) -> None:
    try:
        result = fn()
        ok = bool(result.get("ok", True))
        note_comfyui_settings_job(ok=ok)
    except Exception as exc:
        result = {"ok": False, "message": str(exc)}
        note_comfyui_settings_job(ok=False)
    with _lock:
        job = _jobs.get(job_id)
        if job:
            job["done"] = True
            job["result"] = result
            job["message"] = result.get("message") or ("Complete" if result.get("ok") else "Failed")
            job["pct"] = 100


def submit(label: str, fn: Callable[[], dict]) -> str:
    job_id = uuid.uuid4().hex[:12]
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "label": label,
            "pct": 0,
            "message": "Queued…",
            "done": False,
            "result": None,
            "started": time.time(),
        }
    threading.Thread(
        target=_run_job,
        args=(job_id, fn),
        daemon=True,
        name=f"comfyui-settings-{job_id[:6]}",
    ).start()
    with _lock:
        job = _jobs.get(job_id)
        if job:
            job["message"] = "Applying settings…"
            job["pct"] = 10
    return job_id


def get_job(job_id: str) -> dict | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None
