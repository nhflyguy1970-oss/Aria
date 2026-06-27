"""In-process metrics for /api/metrics and structured logs."""

from __future__ import annotations

import os
import threading
import time
from typing import Any

_lock = threading.Lock()
_started_at = time.time()
_watchdog_restarts = 0
_comfyui_settings_jobs = {"completed": 0, "failed": 0}


def note_watchdog_restart() -> None:
    global _watchdog_restarts
    with _lock:
        _watchdog_restarts += 1


def note_comfyui_settings_job(*, ok: bool) -> None:
    with _lock:
        key = "completed" if ok else "failed"
        _comfyui_settings_jobs[key] = _comfyui_settings_jobs.get(key, 0) + 1


def snapshot() -> dict[str, Any]:
    from jarvis.media_jobs import job_stats

    with _lock:
        wd = _watchdog_restarts
        comfy = dict(_comfyui_settings_jobs)
    uptime = max(0, int(time.time() - _started_at))
    media = job_stats()
    try:
        from jarvis.coding_jobs import job_stats as coding_stats

        coding = coding_stats()
    except Exception:
        coding = {}
    try:
        from jarvis.audio_progress import job_stats as audio_stats

        audio = audio_stats()
    except Exception:
        audio = {}
    return {
        "ok": True,
        "uptime_sec": uptime,
        "version_env": os.getenv("JARVIS_APP_VERSION", ""),
        "watchdog_restarts": wd,
        "comfyui_settings_jobs": comfy,
        "media": media,
        "coding": coding,
        "audio": audio,
    }
