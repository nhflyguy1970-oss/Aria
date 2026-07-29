"""Calendar tab — thin wrappers over Schedule Abstraction Layer."""

from __future__ import annotations

from typing import Any

from jarvis.calendar_schedule import (
    agenda_schedule,
    month_schedule,
    schedule_for_day,
    timeline_schedule,
    week_schedule,
)


def month_overview(journal, month: str | None = None) -> dict[str, Any]:
    return month_schedule(journal, month)


def day_detail(journal, day: str) -> dict[str, Any]:
    detail = schedule_for_day(journal, day)
    # Back-compat fields expected by older UI / tests
    items = detail.get("items") or []
    return {
        **detail,
        "holidays": [i for i in items if i.get("source") == "holiday"],
        "work_blocks": [
            {"start": i.get("time"), "end": i.get("end_hm"), "label": i.get("title")}
            for i in items
            if i.get("source") == "work"
        ],
        "ics_events": [
            {"summary": i.get("title"), "time": i.get("time"), "source": "ics", "id": i.get("id")}
            for i in items
            if i.get("source") == "ics"
        ],
        "journal_events": [
            {
                "id": (i.get("meta") or {}).get("bullet_id"),
                "content": i.get("title"),
                "time": i.get("time"),
                "all_day": i.get("all_day"),
                "item_id": i.get("id"),
            }
            for i in items
            if i.get("source") == "journal" and i.get("kind") == "event"
        ],
        "appointments": [
            {
                "id": (i.get("meta") or {}).get("bullet_id"),
                "content": i.get("title"),
                "time": i.get("time"),
                "type": "event",
                "item_id": i.get("id"),
            }
            for i in items
            if i.get("source") == "journal" and i.get("kind") == "event"
        ],
        "tasks": [
            {
                "id": (i.get("meta") or {}).get("bullet_id"),
                "content": i.get("title"),
                "status": (i.get("meta") or {}).get("status") or "open",
                "item_id": i.get("id"),
            }
            for i in items
            if i.get("source") == "journal" and i.get("kind") == "task"
        ],
        "planner_tasks": [
            {
                "id": (i.get("meta") or {}).get("task_id"),
                "content": i.get("title"),
                "type": "planner_task",
                "source": "planner",
                "item_id": i.get("id"),
            }
            for i in items
            if i.get("source") == "planner" and i.get("kind") == "task"
        ],
        "planner_events": [
            {
                "id": (i.get("meta") or {}).get("event_id"),
                "title": i.get("title"),
                "time": i.get("time"),
                "source": "planner",
                "item_id": i.get("id"),
            }
            for i in items
            if i.get("source") == "planner" and i.get("kind") == "event"
        ],
        "ics_url": (detail.get("ics_status") or {}).get("url") or "",
    }


def week_overview(journal, anchor: str | None = None) -> dict[str, Any]:
    return week_schedule(journal, anchor)


def agenda_overview(journal, *, days: int = 7, start: str | None = None) -> dict[str, Any]:
    return agenda_schedule(journal, days=days, start=start)


def timeline_overview(journal, day: str | None = None) -> dict[str, Any]:
    return timeline_schedule(journal, day)
