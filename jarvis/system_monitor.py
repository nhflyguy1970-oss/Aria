"""Live CPU/RAM/GPU and Ollama model stats for the GUI.

Primary cpu_percent / ram fields are the Aria serve process so the UI
does not present host-wide load as if it were Aria itself.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.request
from typing import Any

_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, Any] | None = None
_CACHE_AT: float = 0
_CACHE_TTL_SEC = float(os.getenv("JARVIS_MONITOR_CACHE_SEC", "7"))
_CPU_PRIMED = False


def _ollama_running_models() -> list[dict[str, Any]]:
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/ps", headers={"User-Agent": "Jarvis/monitor"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return list(data.get("models") or [])
    except Exception:
        return []


def _sample_cpu_and_ram() -> tuple[float, float, dict[str, Any], dict[str, Any]]:
    """Return (process_cpu, system_cpu, process_ram, system_ram). Non-blocking."""
    global _CPU_PRIMED
    process_cpu = 0.0
    system_cpu = 0.0
    process_ram = {"percent": 0.0, "used_mb": 0, "total_mb": 0, "rss_mb": 0}
    system_ram = {"percent": 0.0, "used_mb": 0, "total_mb": 0, "available_mb": 0}
    try:
        import psutil

        proc = psutil.Process(os.getpid())
        if not _CPU_PRIMED:
            # First call after process start returns 0.0; prime without sleeping.
            psutil.cpu_percent(interval=None)
            proc.cpu_percent(interval=None)
            _CPU_PRIMED = True
            time.sleep(0.05)
        system_cpu = float(psutil.cpu_percent(interval=None))
        process_cpu = float(proc.cpu_percent(interval=None))
        mem = psutil.virtual_memory()
        rss_mb = int(proc.memory_info().rss // (1024 * 1024))
        total_mb = int(mem.total // (1024 * 1024)) or 1
        process_ram = {
            "percent": round(100.0 * rss_mb / total_mb, 1),
            "used_mb": rss_mb,
            "total_mb": total_mb,
            "rss_mb": rss_mb,
        }
        system_ram = {
            "percent": float(mem.percent),
            "used_mb": int(mem.used // (1024 * 1024)),
            "total_mb": total_mb,
            "available_mb": int(mem.available // (1024 * 1024)),
        }
    except Exception:
        pass
    return process_cpu, system_cpu, process_ram, system_ram


def collect_stats() -> dict[str, Any]:
    global _CACHE, _CACHE_AT
    now = time.time()
    with _CACHE_LOCK:
        if _CACHE is not None and now - _CACHE_AT < _CACHE_TTL_SEC:
            return dict(_CACHE)

    process_cpu, system_cpu, process_ram, system_ram = _sample_cpu_and_ram()
    gpu: dict[str, Any] = {}
    try:
        from jarvis.gpu import detect_gpu

        gpu = detect_gpu()
    except Exception:
        pass
    payload = {
        # Primary fields = Aria process (what operators mean by "Aria CPU/RAM").
        "cpu_percent": process_cpu,
        "ram": process_ram,
        "gpu": gpu,
        "ollama_models": _ollama_running_models(),
        "process": {
            "pid": os.getpid(),
            "cpu_percent": process_cpu,
            "rss_mb": process_ram.get("rss_mb") or process_ram.get("used_mb") or 0,
        },
        "system": {
            "cpu_percent": system_cpu,
            "ram": system_ram,
        },
    }
    with _CACHE_LOCK:
        _CACHE = dict(payload)
        _CACHE_AT = now
    return payload
