"""Dashboard Home summary — Provider Health owns the data."""

from __future__ import annotations

from typing import Any

from jarvis.provider_health.engine import product_status


def dashboard_summary() -> dict[str, Any]:
    from jarvis.provider_health.probe import list_models, resource_snapshot

    st = product_status()
    wd = st.get("watchdog") or {}
    models = list_models("ollama") or {}
    resources = resource_snapshot() or {}
    mem = resources.get("ram") if isinstance(resources.get("ram"), dict) else {}
    return {
        "ok": True,
        "status": st.get("state"),
        "state": st.get("state"),
        "health_score": st.get("health_score"),
        "provider": st.get("provider"),
        "model": models.get("current"),
        "models": (models.get("models") or [])[:6],
        "alive": st.get("alive"),
        "cpu_percent": resources.get("cpu_percent"),
        "ram_percent": mem.get("percent"),
        "last_error": wd.get("last_error"),
        "recoveries": wd.get("recoveries"),
        "recovery_active": st.get("state") == "recovering",
        "timeouts": wd.get("timeouts"),
        "deep_link": {"view": "workstation", "tab": "diagnostics"},
    }
