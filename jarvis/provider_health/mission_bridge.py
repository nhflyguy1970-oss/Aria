"""Mission Control status panel — operational view only."""

from __future__ import annotations

from typing import Any

from jarvis.provider_health.engine import diagnostics, product_status
from jarvis.provider_health.history import load_history


def mission_panel() -> dict[str, Any]:
    st = product_status()
    diag = diagnostics()
    hist = load_history(limit=12)
    return {
        "ok": True,
        "product": "Provider Health",
        "state": st.get("state"),
        "health_score": st.get("health_score"),
        "provider": diag.get("provider"),
        "model": diag.get("model"),
        "endpoint": diag.get("endpoint"),
        "connection": diag.get("connection"),
        "gpu": diag.get("gpu"),
        "cpu_percent": diag.get("cpu_percent"),
        "failure_rate": _failure_rate(st.get("watchdog") or {}),
        "recovery_attempts": diag.get("recovery_attempts"),
        "recovery_success": diag.get("recovery_success"),
        "last_error": diag.get("last_error"),
        "recent": hist[:8],
        "note": "Mission Control displays Provider Health — it does not own recovery policy.",
    }


def _failure_rate(wd: dict[str, Any]) -> float:
    req = int(wd.get("requests") or 0)
    if req <= 0:
        return 0.0
    return round(int(wd.get("timeouts") or 0) / req, 3)
