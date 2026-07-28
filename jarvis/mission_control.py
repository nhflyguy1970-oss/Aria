"""Mission Control — delegates to AI Platform (source of truth), enriched for Aria operators."""

from __future__ import annotations

from typing import Any


def collect_mission_control(*, record_metrics: bool = True) -> dict[str, Any]:
    from aiplatform.mission_control.aggregator import collect_mission_control as platform_mc

    from jarvis.mission_control_ops.enrich import enrich_snapshot

    raw = platform_mc(record_metrics=record_metrics)
    return enrich_snapshot(raw)


def get_tab(tab: str) -> dict[str, Any]:
    key = (tab or "").strip().lower()
    # Aria-local surface (not an AI-Platform MC tab name).
    if key == "connection":
        from jarvis.platform_runtime import runtime_connection_status

        return {"ok": True, "tab": "connection", "data": runtime_connection_status()}

    from aiplatform.mission_control.aggregator import get_tab as platform_tab

    return platform_tab(tab)


def format_overview_markdown() -> str:
    from aiplatform.mission_control.aggregator import format_overview_markdown as platform_md

    return platform_md()


def export_activity_csv(*, limit: int = 200) -> str:
    from aiplatform.mission_control.activity import export_csv

    return export_csv(limit=limit)


def health_summary() -> dict[str, Any]:
    """Compact health for Automation / voice / status bar."""
    from jarvis.mission_control_ops.automation_gate import get_infrastructure_health

    return get_infrastructure_health(force=True)
