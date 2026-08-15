"""Mission Control status panel — operational view only."""

from __future__ import annotations

import time
from typing import Any

from jarvis.provider_health.engine import product_status
from jarvis.provider_health.history import load_history

_PANEL_CACHE: dict[str, object] = {"at": 0.0, "value": None}
_PANEL_TTL_S = 15.0


def list_models_safe() -> dict[str, Any]:
    try:
        from jarvis.provider_health.probe import list_models

        return list_models("ollama") or {}
    except Exception:
        return {}


def resource_snapshot_safe() -> dict[str, Any]:
    try:
        from jarvis.provider_health.probe import resource_snapshot

        return resource_snapshot() or {}
    except Exception:
        return {}


def mission_panel() -> dict[str, Any]:
    now = time.monotonic()
    cached = _PANEL_CACHE.get("value")
    if isinstance(cached, dict) and now - float(_PANEL_CACHE.get("at") or 0) < _PANEL_TTL_S:
        return dict(cached)

    # Never call diagnostics() here — it force-probes Ollama generate and was
    # measured at multi-second cost (and is the Provider Health "timeout" path).
    st = product_status()
    ping = st.get("ping") or {}
    models = list_models_safe()
    resources = resource_snapshot_safe()
    hist = load_history(limit=12)
    wd = st.get("watchdog") or {}
    value = {
        "ok": True,
        "product": "Provider Health",
        "state": st.get("state"),
        "health_score": st.get("health_score"),
        "provider": st.get("provider") or ping.get("provider") or "ollama",
        "model": models.get("current"),
        "endpoint": ping.get("host"),
        "connection": "up" if st.get("alive") else "down",
        "gpu": resources.get("gpu"),
        "cpu_percent": resources.get("cpu_percent"),
        "failure_rate": _failure_rate(wd),
        "recovery_attempts": wd.get("recoveries"),
        "recovery_success": wd.get("recovery_success"),
        "last_error": wd.get("last_error"),
        "recent": hist[:8],
        "note": "Mission Control displays Provider Health — it does not own recovery policy.",
    }
    _PANEL_CACHE["at"] = now
    _PANEL_CACHE["value"] = value
    return dict(value)


def _failure_rate(wd: dict[str, Any]) -> float:
    req = int(wd.get("requests") or 0)
    if req <= 0:
        return 0.0
    return round(int(wd.get("timeouts") or 0) / req, 3)
