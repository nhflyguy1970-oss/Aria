"""Grafana dashboard provisioning helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DASHBOARD_DIR = Path(__file__).resolve().parent / "grafana" / "dashboards"


def list_dashboards() -> list[dict[str, Any]]:
    dashboards: list[dict[str, Any]] = []
    if not _DASHBOARD_DIR.is_dir():
        return dashboards
    for path in sorted(_DASHBOARD_DIR.glob("*.json")):
        try:
            dashboards.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return dashboards


def provisioning_manifest() -> dict[str, Any]:
    """Grafana file provisioning manifest for docker-compose sidecar."""
    return {
        "apiVersion": 1,
        "providers": [
            {
                "name": "Aria",
                "orgId": 1,
                "folder": "Aria",
                "type": "file",
                "disableDeletion": False,
                "updateIntervalSeconds": 30,
                "options": {"path": "/etc/grafana/provisioning/dashboards/aria"},
            }
        ],
    }
