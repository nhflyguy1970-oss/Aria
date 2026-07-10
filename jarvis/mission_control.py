"""Mission Control — delegates to AI Platform (source of truth)."""

from __future__ import annotations

from typing import Any


def collect_mission_control(*, record_metrics: bool = True) -> dict[str, Any]:
    from aiplatform.mission_control.aggregator import collect_mission_control as platform_mc

    return platform_mc(record_metrics=record_metrics)


def get_tab(tab: str) -> dict[str, Any]:
    from aiplatform.mission_control.aggregator import get_tab as platform_tab

    return platform_tab(tab)


def format_overview_markdown() -> str:
    from aiplatform.mission_control.aggregator import format_overview_markdown as platform_md

    return platform_md()


def export_activity_csv(*, limit: int = 200) -> str:
    from aiplatform.mission_control.activity import export_csv

    return export_csv(limit=limit)
