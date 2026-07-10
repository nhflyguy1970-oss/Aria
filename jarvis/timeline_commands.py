"""Timeline chat commands — operational history without chain-of-thought."""

from __future__ import annotations

import time
from typing import Any


def is_timeline_command(message: str) -> str | None:
    lower = (message or "").strip().lower()
    if lower == "timeline":
        return "timeline_recent"
    if lower == "timeline today":
        return "timeline_today"
    if lower == "timeline startup":
        return "timeline_startup"
    if lower == "timeline failures":
        return "timeline_failures"
    if lower == "timeline services":
        return "timeline_services"
    if lower == "timeline models":
        return "timeline_models"
    if lower == "timeline repairs":
        return "timeline_repairs"
    if lower == "timeline backups":
        return "timeline_backups"
    return None


def _fetch_events(**kwargs: Any) -> list[dict[str, Any]]:
    try:
        from aiplatform.mission_control.timeline import list_timeline

        return list_timeline(limit=kwargs.pop("limit", 15), **kwargs)
    except Exception:
        return []


def format_timeline_events(events: list[dict[str, Any]], *, title: str) -> str:
    if not events:
        return f"**{title}**\n\nNo timeline events recorded yet."
    lines = [f"**{title}**", ""]
    for ev in events:
        lines.append(
            f"- `{ev.get('iso', '')}` **{ev.get('type', '')}** "
            f"({ev.get('application', '')}/{ev.get('component', '')}) "
            f"[{ev.get('severity', 'info')}] {ev.get('detail', '')[:160]}"
        )
    return "\n".join(lines)


def execute_timeline_command(action: str) -> dict[str, Any]:
    today_start = time.mktime(time.strptime(time.strftime("%Y-%m-%d"), "%Y-%m-%d"))
    if action == "timeline_today":
        events = _fetch_events(since_ts=today_start, limit=25)
        return {"ok": True, "message": format_timeline_events(events, title="Timeline — today")}
    if action == "timeline_startup":
        events = _fetch_events(query="start", limit=20)
        return {"ok": True, "message": format_timeline_events(events, title="Timeline — startup")}
    if action == "timeline_failures":
        events = _fetch_events(severity="error", limit=20) + _fetch_events(
            severity="critical", limit=20
        )
        events = events[:20]
        return {"ok": True, "message": format_timeline_events(events, title="Timeline — failures")}
    if action == "timeline_services":
        events = _fetch_events(category="services", limit=20) or _fetch_events(
            query="service", limit=20
        )
        return {"ok": True, "message": format_timeline_events(events, title="Timeline — services")}
    if action == "timeline_models":
        events = _fetch_events(query="model", limit=20)
        return {"ok": True, "message": format_timeline_events(events, title="Timeline — models")}
    if action == "timeline_repairs":
        events = _fetch_events(query="repair", limit=20)
        return {"ok": True, "message": format_timeline_events(events, title="Timeline — repairs")}
    if action == "timeline_backups":
        events = _fetch_events(query="backup", limit=20)
        return {"ok": True, "message": format_timeline_events(events, title="Timeline — backups")}
    events = _fetch_events(limit=15)
    return {"ok": True, "message": format_timeline_events(events, title="Timeline — recent")}
