"""Dashboard Home summary — Provider Health owns the data."""

from __future__ import annotations

from typing import Any

from jarvis.provider_health.engine import product_status


def dashboard_summary() -> dict[str, Any]:
    from jarvis.provider_health.engine import diagnostics

    st = product_status()
    wd = st.get("watchdog") or {}
    diag = diagnostics()
    return {
        "ok": True,
        "status": st.get("state"),
        "state": st.get("state"),
        "health_score": st.get("health_score"),
        "provider": st.get("provider"),
        "model": diag.get("model"),
        "models": (diag.get("models") or [])[:6],
        "alive": st.get("alive"),
        "cpu_percent": diag.get("cpu_percent"),
        "ram_percent": ((diag.get("memory") or {}) if isinstance(diag.get("memory"), dict) else {}).get("percent"),
        "last_error": wd.get("last_error") or diag.get("last_error"),
        "recoveries": wd.get("recoveries"),
        "recovery_active": st.get("state") == "recovering",
        "timeouts": wd.get("timeouts"),
        "deep_link": {"view": "workstation", "tab": "diagnostics"},
    }
