"""Mission Control Latency panel payload."""

from __future__ import annotations

from typing import Any

from jarvis.latency_observability.metrics import diagnostics, stats_payload
from jarvis.latency_observability.trace import live_traces


def mission_panel() -> dict[str, Any]:
    stats = stats_payload()
    live = live_traces()[:8]
    current = live[0] if live else None
    return {
        "product": "Latency",
        "state": "live" if live else "idle",
        "live_count": len(live),
        "current": {
            "trace_id": (current or {}).get("trace_id"),
            "request_id": (current or {}).get("request_id"),
            "stage": (current or {}).get("current_stage"),
            "elapsed_ms": (current or {}).get("elapsed_ms"),
            "model": ((current or {}).get("provider") or {}).get("model")
            or ((current or {}).get("model") or {}).get("model"),
            "provider": ((current or {}).get("provider") or {}).get("provider") or "ollama",
            "first_token_ms": ((current or {}).get("stream") or {}).get("first_token_ms"),
            "slowest": (current or {}).get("slowest"),
            "action": (current or {}).get("action"),
        }
        if current
        else None,
        "first_token": stats.get("first_token"),
        "completion": stats.get("completion"),
        "cancellation_rate": stats.get("cancellation_rate"),
        "timeout_rate": stats.get("timeout_rate"),
        "model_load": stats.get("model_load"),
        "live": live,
        "recent": stats.get("recent") or [],
        "diagnostics": diagnostics(),
        "deep_link": {"view": "mission_control", "tab": "latency"},
    }
