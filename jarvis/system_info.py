"""Unified system snapshot for voice and dashboard."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from jarvis.feature_flags import all_flags, planner_enabled


def build_system_info(*, assistant) -> dict[str, Any]:
    now = datetime.now()
    greeting = "Hello"
    try:
        from jarvis.morning_briefing import personalized_greeting

        greeting = personalized_greeting(when=now, assistant=assistant)
    except Exception:
        pass
    env: dict[str, Any] = {}
    try:
        from jarvis.environment import snapshot as env_snapshot

        env = env_snapshot()
    except Exception:
        pass
    planner: dict[str, Any] = {"enabled": planner_enabled()}
    if planner_enabled():
        try:
            from jarvis.planner_store import planner_snapshot

            planner = planner_snapshot()
        except Exception:
            pass
    ha: dict[str, Any] = {}
    try:
        from jarvis.home_assistant import ha_summary_markdown

        summary = ha_summary_markdown()
        if summary:
            ha = {"summary": summary}
    except Exception:
        pass
    return {
        "greeting": greeting,
        "date": now.strftime("%A, %B %d"),
        "date_label": now.strftime("%A, %B %d"),
        "time": now.strftime("%I:%M %p").lstrip("0"),
        "time_display": now.strftime("%I:%M %p").lstrip("0"),
        "planner": planner,
        "environment": env,
        "home_assistant": ha,
        "feature_flags": all_flags(),
    }


def format_system_info_markdown(*, assistant) -> str:
    info = build_system_info(assistant=assistant)
    parts = [
        f"## {info.get('greeting', 'Status')}",
        f"**{info.get('date', '')}** · {info.get('time', '')}",
    ]
    planner = info.get("planner") or {}
    if planner.get("enabled"):
        try:
            from jarvis.planner_store import format_planner_lines

            block = format_planner_lines()
            if block:
                parts.append(block)
        except Exception:
            pass
    ha = info.get("home_assistant") or {}
    if ha.get("summary"):
        parts.append(ha["summary"])
    return "\n".join(parts)
