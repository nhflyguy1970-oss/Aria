"""Live CPU/RAM/GPU and Ollama model stats for the GUI."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from typing import Any

_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, Any] | None = None
_CACHE_AT: float = 0
_CACHE_TTL_SEC = float(__import__("os").getenv("JARVIS_MONITOR_CACHE_SEC", "7"))


def _ollama_running_models() -> list[dict[str, Any]]:
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/ps", headers={"User-Agent": "Jarvis/monitor"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return list(data.get("models") or [])
    except Exception:
        return []


def collect_stats() -> dict[str, Any]:
    global _CACHE, _CACHE_AT
    now = time.time()
    with _CACHE_LOCK:
        if _CACHE is not None and now - _CACHE_AT < _CACHE_TTL_SEC:
            return dict(_CACHE)
    cpu_percent = 0.0
    ram = {"percent": 0, "used_mb": 0, "total_mb": 0}
    try:
        import psutil

        cpu_percent = float(psutil.cpu_percent(interval=0.1))
        mem = psutil.virtual_memory()
        ram = {
            "percent": float(mem.percent),
            "used_mb": int(mem.used // (1024 * 1024)),
            "total_mb": int(mem.total // (1024 * 1024)),
        }
    except Exception:
        pass
    gpu: dict[str, Any] = {}
    try:
        from jarvis.gpu import detect_gpu

        gpu = detect_gpu()
    except Exception:
        pass
    payload = {
        "cpu_percent": cpu_percent,
        "ram": ram,
        "gpu": gpu,
        "ollama_models": _ollama_running_models(),
    }
    with _CACHE_LOCK:
        _CACHE = dict(payload)
        _CACHE_AT = now
    return payload
