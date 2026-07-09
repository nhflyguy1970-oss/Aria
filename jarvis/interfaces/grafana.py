"""Grafana observability interface."""

from __future__ import annotations

import os
from typing import Any


def grafana_url() -> str:
    return os.getenv("JARVIS_GRAFANA_URL", "http://127.0.0.1:3001").rstrip("/")


def prometheus_url() -> str:
    return os.getenv("JARVIS_PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")


def status() -> dict[str, Any]:
    from jarvis.workstation.registry import component

    comp = component("grafana")
    prom = component("prometheus")
    return {
        "ok": True,
        "grafana": {
            "url": grafana_url(),
            "healthy": comp.healthy() if comp else False,
        },
        "prometheus": {
            "url": prometheus_url(),
            "healthy": prom.healthy() if prom else False,
            "aria_metrics": "/api/metrics/prometheus",
        },
    }
