"""Calendar tab — merge journal, holidays, ICS, and work schedule."""

from __future__ import annotations

from datetime import date
from typing import Any

from jarvis.calendar_ics import fetch_events_for_day, fetch_events_for_month, ics_url
from jarvis.calendar_store import load_work_schedule, work_blocks_for_day


def month_overview(journal, month: str | None = None) -> dict[str, Any]:
    from jarvis.modules.journal import _month_key

    mk = month or _month_key()
    cal = journal.monthly_calendar(mk)
    ics_by_day = fetch_events_for_month(mk)
    if ics_by_day:
        merged = dict(cal.get("events") or {})
        for day_str, items in ics_by_day.items():
            for item in items:
                merged.setdefault(day_str, []).append(
                    {
                        "time": item.get("time", ""),
                        "content": item.get("summary", ""),
                        "source": "ics",
                    }
                )
        cal["events"] = merged
        cal["ics_events"] = ics_by_day
    cal["ics_url"] = ics_url()
    cal["work_schedule"] = load_work_schedule()
    return cal


def day_detail(journal, day: str) -> dict[str, Any]:
    d = date.fromisoformat(day)
    mk = day[:7]
    monthly = journal.monthly_calendar(mk)
    day_num = str(d.day)
    note = (monthly.get("calendar_notes") or {}).get(day_num, "")
    holidays = (monthly.get("holidays") or {}).get(day, [])
    page = journal.daily_get(day, enrich=False)
    timeline = journal.daily_timeline(day)
    ics = fetch_events_for_day(d)
    work = work_blocks_for_day(d)
    bullets = page.get("bullets") or []
    appointments: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    for b in bullets:
        item = {
            "id": b.get("id"),
            "type": b.get("type"),
            "content": b.get("content", ""),
            "time": b.get("time"),
            "status": b.get("status"),
        }
        if b.get("type") == "event":
            appointments.append(item)
        elif b.get("type") == "task":
            tasks.append(item)
    journal_events = timeline.get("events") or []
    planner_tasks: list[dict[str, Any]] = []
    if day == date.today().isoformat():
        try:
            from jarvis.planner_store import list_tasks

            for t in list_tasks(include_completed=False):
                planner_tasks.append(
                    {
                        "id": t.get("id"),
                        "type": "planner_task",
                        "content": t.get("text") or "",
                        "time": None,
                        "status": "open",
                        "source": "planner",
                    }
                )
        except Exception:
            planner_tasks = []
    return {
        "ok": True,
        "day": day,
        "title": page.get("title", day),
        "holidays": holidays,
        "calendar_note": note,
        "work_blocks": work,
        "ics_events": ics,
        "journal_events": journal_events,
        "appointments": appointments,
        "tasks": tasks,
        "planner_tasks": planner_tasks,
        "ics_url": ics_url(),
    }
