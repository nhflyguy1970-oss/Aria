"""Calendar bridges — Home/Dashboard/Search/Mission Control consume; Calendar owns data."""

from __future__ import annotations

import re
from typing import Any

from jarvis.calendar_time import today_iso


def dashboard_summary(journal: Any | None = None) -> dict[str, Any]:
    """Upcoming commitments for Dashboard Home widget."""
    from jarvis.calendar_schedule import schedule_for_day
    from jarvis.calendar_ics import sync_status

    if journal is None:
        try:
            from jarvis.modules.journal import BulletJournal

            journal = BulletJournal()
        except Exception as exc:
            return {"ok": False, "error": str(exc), "items": [], "count": 0}

    day = today_iso()
    detail = schedule_for_day(journal, day)
    items = [
        {
            "title": i.get("title"),
            "time": i.get("time") or "",
            "source": i.get("source"),
            "id": i.get("id"),
            "all_day": i.get("all_day"),
        }
        for i in (detail.get("items") or [])
        if i.get("kind") in ("event", "holiday", "block")
    ][:8]
    return {
        "ok": True,
        "day": day,
        "count": len(items),
        "items": items,
        "ics_status": sync_status(),
        "deep_link": {"view": "calendar"},
    }


def search_hits(query: str, limit: int = 12, journal: Any | None = None) -> list[dict[str, Any]]:
    """Keyword hits over work schedule + today's unified schedule (Calendar-owned)."""
    from jarvis.calendar_store import WEEKDAYS, load_work_schedule
    from jarvis.calendar_schedule import schedule_for_day

    q = (query or "").lower().strip()
    out: list[dict[str, Any]] = []
    tokens = re.findall(r"\w{2,}", q) or ([q] if q else [])
    # Browsing the Calendar corpus by name should show today's commitments,
    # not require the word "calendar" to appear inside every event title.
    browse_all = (not q) or q in {
        "calendar",
        "schedule",
        "schedules",
        "agenda",
        "appointments",
        "meetings",
        "events",
    }

    sched = load_work_schedule()
    for day in WEEKDAYS:
        for block in sched.get("days", {}).get(day, []) or []:
            label = str(block.get("label") or "Work")
            blob = f"{day} {label} {block.get('start')} {block.get('end')}".lower()
            if not browse_all and q and q not in blob and not any(t in blob for t in tokens):
                continue
            out.append(
                {
                    "title": f"{day.title()}: {label}",
                    "summary": f"{block.get('start')}–{block.get('end')}",
                    "day": day,
                    "kind": "work_block",
                    "score": 0.78 if browse_all else 0.68,
                }
            )
            if len(out) >= limit:
                return out

    if journal is None:
        try:
            from jarvis.modules.journal import BulletJournal

            journal = BulletJournal()
        except Exception:
            return out

    try:
        detail = schedule_for_day(journal, today_iso())
        for i in detail.get("items") or []:
            # Calendar search owns commitments only — journal notes stay in Journal.
            if i.get("kind") not in ("event", "holiday", "block"):
                continue
            blob = f"{i.get('title')} {i.get('time')} {i.get('source')}".lower()
            if not browse_all and q and q not in blob and not any(t in blob for t in tokens):
                continue
            out.append(
                {
                    "title": i.get("title") or "Commitment",
                    "summary": f"{i.get('time') or 'all-day'} · {i.get('source_label') or i.get('source')}",
                    "day": i.get("day") or today_iso(),
                    "kind": i.get("kind"),
                    "id": i.get("id"),
                    "score": 0.82 if browse_all else 0.72,
                }
            )
            if len(out) >= limit:
                break
    except Exception:
        pass
    return out[:limit]


def mission_status() -> dict[str, Any]:
    """Mission Control status panel — health only, no ops ownership."""
    from jarvis.calendar_ics import sync_status
    from jarvis.calendar_store import load_work_schedule
    from jarvis.calendar_terminology import TERMINOLOGY

    st = sync_status()
    work = load_work_schedule()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "ics": st,
        "work_schedule_enabled": bool(work.get("enabled")),
        "healthy": bool(st.get("ok", True)) or not st.get("configured"),
        "note": "Calendar status only — Mission Control does not own schedule data.",
    }


def product_status() -> dict[str, Any]:
    from jarvis.calendar_ics import sync_status
    from jarvis.calendar_terminology import BOUNDARIES, MENTAL_MODEL, TERMINOLOGY

    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "ics": sync_status(),
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "terminology": TERMINOLOGY,
    }
