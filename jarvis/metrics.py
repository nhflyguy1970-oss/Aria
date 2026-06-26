# Source Generated with Decompyle++
# File: metrics.cpython-312.pyc (Python 3.12)

'''In-process metrics for /api/metrics and structured logs.'''
from __future__ import annotations
import os
import threading
import time
from typing import Any
_lock = threading.Lock()
_started_at = time.time()
_watchdog_restarts = 0
_comfyui_settings_jobs = {
    'completed': 0,
    'failed': 0 }
_request_count = 0
_slow_request_count = 0
_duration_buckets = {
    'lt_100ms': 0,
    'lt_500ms': 0,
    'lt_1s': 0,
    'lt_3s': 0,
    'gte_3s': 0 }

def note_watchdog_restart():
    global _watchdog_restarts
    _lock
    _watchdog_restarts += 1
    None(None, None)
    return None
    with None:
        if not None:
            pass


def note_comfyui_settings_job(*, ok):
    _lock
    key = 'completed' if ok else 'failed'
    _comfyui_settings_jobs[key] = _comfyui_settings_jobs.get(key, 0) + 1
    None(None, None)
    return None
    with None:
        if not None:
            pass


def note_request_duration(ms = None, *, path, status):
    global _request_count, _slow_request_count
    _lock
    _request_count += 1
    if ms >= 3000:
        _slow_request_count += 1
    if ms < 100:
        pass
    elif ms < 500:
        pass
    elif ms < 1000:
        pass
    elif ms < 3000:
        pass
    
    None(None, None)
    return None
    with None:
        if not None:
            pass


def snapshot():
    job_stats = job_stats
    import jarvis.media_jobs
    _lock
    wd = _watchdog_restarts
    comfy = dict(_comfyui_settings_jobs)
    req_count = _request_count
    slow_count = _slow_request_count
    buckets = dict(_duration_buckets)
    None(None, None)
    uptime = max(0, int(time.time() - _started_at))
    media = job_stats()
# WARNING: Decompyle incomplete

