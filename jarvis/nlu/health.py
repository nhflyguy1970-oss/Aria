"""Classifier health — runtime metrics for Mission Control."""

from __future__ import annotations

import time
from typing import Any

_HEALTH: dict[str, Any] = {
    "loaded": False,
    "healthy": True,
    "responding": True,
    "latency_samples": [],
    "failures": 0,
    "restart_count": 0,
    "queue_depth": 0,
    "last_error": "",
    "last_classify_at": 0.0,
}


def record_classify_success(*, latency_ms: float, model: str, device: str) -> None:
    samples = list(_HEALTH.get("latency_samples") or [])
    samples.append(latency_ms)
    _HEALTH.update(
        {
            "loaded": True,
            "healthy": True,
            "responding": True,
            "model": model,
            "device": device,
            "latency_samples": samples[-50:],
            "last_classify_at": time.time(),
            "queue_depth": max(0, int(_HEALTH.get("queue_depth") or 0) - 1),
        }
    )


def record_classify_failure(error: str) -> None:
    _HEALTH["failures"] = int(_HEALTH.get("failures") or 0) + 1
    _HEALTH["healthy"] = int(_HEALTH.get("failures") or 0) < 5
    _HEALTH["last_error"] = (error or "")[:300]
    _HEALTH["queue_depth"] = max(0, int(_HEALTH.get("queue_depth") or 0) - 1)


def record_queue_enqueue() -> None:
    _HEALTH["queue_depth"] = int(_HEALTH.get("queue_depth") or 0) + 1


def record_restart() -> None:
    _HEALTH["restart_count"] = int(_HEALTH.get("restart_count") or 0) + 1


def classifier_health() -> dict[str, Any]:
    from jarvis.nlu.benchmark import should_rebenchmark
    from jarvis.nlu.placement import placement_config

    cfg = placement_config()
    samples = list(_HEALTH.get("latency_samples") or [])
    avg_lat = round(sum(samples) / len(samples), 1) if samples else None
    mem_mb = None
    try:
        import resource

        mem_mb = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
    except Exception:
        pass
    util = None
    try:
        from jarvis.gpu import detect_gpu

        gpu = detect_gpu()
        util = gpu.get("vram_used_mb")
    except Exception:
        pass
    return {
        "ok": True,
        "loaded": _HEALTH.get("loaded", False),
        "healthy": _HEALTH.get("healthy", True),
        "responding": _HEALTH.get("responding", True),
        "model": cfg.get("model"),
        "device": cfg.get("device"),
        "version": cfg.get("version", "1.0"),
        "benchmark_date": cfg.get("benchmark_date"),
        "selection_reason": cfg.get("selection_reason"),
        "average_latency_ms": avg_lat or cfg.get("average_latency_ms"),
        "memory_mb": mem_mb,
        "device_utilization": util,
        "queue_depth": _HEALTH.get("queue_depth", 0),
        "recent_failures": _HEALTH.get("failures", 0),
        "restart_count": _HEALTH.get("restart_count", 0),
        "last_error": _HEALTH.get("last_error", ""),
        "benchmark_stale": should_rebenchmark(),
        "benchmark_status": "stale" if should_rebenchmark() else "current",
    }
