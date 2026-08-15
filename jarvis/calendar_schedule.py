"""Schedule Abstraction Layer — unified read model over Planner, Journal, ICS, work, holidays."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from jarvis.calendar_time import (
    agenda_dates,
    combine_local,
    format_hm,
    now_local,
    parse_day,
    sort_key_item,
    today_iso,
    validate_time_hm,
    week_dates,
)

log = logging.getLogger("jarvis.calendar.schedule")

SOURCE_META = {
    "journal": {"label": "Journal", "color": "journal", "editable": True},
    "planner": {"label": "Planner", "color": "planner", "editable": True},
    "ics": {"label": "External", "color": "ics", "editable": False},
    "work": {"label": "Work", "color": "work", "editable": False},
    "holiday": {"label": "Holiday", "color": "holiday", "editable": False},
    "memory": {"label": "Memory", "color": "memory", "editable": False},
    "timer": {"label": "Timer", "color": "timer", "editable": False},
    "alarm": {"label": "Alarm", "color": "alarm", "editable": False},
}


def _item(
    *,
    id: str,
    title: str,
    day: str,
    source: str,
    time: str | None = None,
    end_hm: str | None = None,
    duration_min: int | None = None,
    kind: str = "event",
    all_day: bool = False,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    src = SOURCE_META.get(source, {"label": source, "color": source, "editable": False})
    return {
        "id": id,
        "title": title,
        "content": title,
        "day": day,
        "time": time or "",
        "start_hm": time or "",
        "end_hm": end_hm or "",
        "duration_min": duration_min,
        "all_day": bool(all_day or not time),
        "source": source,
        "source_label": src["label"],
        "color": src["color"],
        "editable": src["editable"],
        "kind": kind,
        "meta": meta or {},
    }


def _journal_items(journal, day: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        page = journal.daily_get(day, enrich=False)
    except Exception as exc:
        log.warning("journal day load failed: %s", exc)
        return items

    def walk(bullets: list) -> None:
        for b in bullets:
            btype = b.get("type")
            if btype == "event":
                items.append(
                    _item(
                        id=f"journal:{b.get('id')}",
                        title=b.get("content") or "",
                        day=day,
                        source="journal",
                        time=b.get("time") or "",
                        duration_min=b.get("duration_min"),
                        kind="event",
                        all_day=not b.get("time"),
                        meta={"bullet_id": b.get("id"), "status": b.get("status")},
                    )
                )
            elif btype == "task" and b.get("status") != "done":
                items.append(
                    _item(
                        id=f"journal-task:{b.get('id')}",
                        title=b.get("content") or "",
                        day=day,
                        source="journal",
                        time=b.get("time") or "",
                        kind="task",
                        all_day=not b.get("time"),
                        meta={"bullet_id": b.get("id"), "status": b.get("status")},
                    )
                )
            elif btype in ("note", "fact", "explore", "reflection") or (
                btype and btype not in ("event", "task") and (b.get("content") or "").strip()
            ):
                # Notes and other journal bullets must appear on Calendar day —
                # otherwise Journal and Calendar disagree about the same day.
                items.append(
                    _item(
                        id=f"journal-note:{b.get('id')}",
                        title=b.get("content") or "",
                        day=day,
                        source="journal",
                        time=b.get("time") or "",
                        kind="note",
                        all_day=not b.get("time"),
                        meta={"bullet_id": b.get("id"), "status": b.get("status"), "bullet_type": btype},
                    )
                )
            walk(b.get("children") or [])

    walk(page.get("bullets") or [])
    return items


def _planner_events(day: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        from jarvis.planner_store import events_for_day, planner_enabled

        if not planner_enabled():
            return items
        for e in events_for_day(day):
            start = e.get("start_time") or ""
            end = e.get("end_time") or ""
            hm = start[11:16] if len(start) >= 16 else ""
            end_hm = end[11:16] if len(end) >= 16 else ""
            items.append(
                _item(
                    id=f"planner:{e.get('id')}",
                    title=e.get("title") or "",
                    day=day,
                    source="planner",
                    time=hm,
                    end_hm=end_hm,
                    kind="event",
                    all_day=not hm,
                    meta={"event_id": e.get("id"), "description": e.get("description")},
                )
            )
    except Exception as exc:
        log.debug("planner events: %s", exc)
    return items


def _planner_tasks_today(day: str) -> list[dict[str, Any]]:
    if day != today_iso():
        return []
    items: list[dict[str, Any]] = []
    try:
        from jarvis.planner_store import list_tasks, planner_enabled

        if not planner_enabled():
            return items
        for t in list_tasks(include_completed=False):
            due = (t.get("due_date") or "")[:10]
            if due and due != day:
                continue
            items.append(
                _item(
                    id=f"planner-task:{t.get('id')}",
                    title=t.get("text") or "",
                    day=day,
                    source="planner",
                    kind="task",
                    all_day=True,
                    meta={"task_id": t.get("id"), "priority": t.get("priority")},
                )
            )
    except Exception as exc:
        log.debug("planner tasks: %s", exc)
    return items


def _ics_items(day: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from jarvis.calendar_ics import fetch_events_for_range, sync_status

    d = parse_day(day)
    result = fetch_events_for_range(d, d + timedelta(days=1))
    items = []
    for e in (result.get("events") or {}).get(day, []):
        items.append(
            _item(
                id=e.get("id") or f"ics:{day}:{e.get('summary')}",
                title=e.get("summary") or e.get("title") or "",
                day=day,
                source="ics",
                time=e.get("time") or "",
                duration_min=e.get("duration_min"),
                kind="event",
                all_day=bool(e.get("all_day") or not e.get("time")),
                meta={"location": e.get("location"), "recurring": e.get("recurring")},
            )
        )
    return items, result.get("status") or sync_status()


def _work_items(day: str) -> list[dict[str, Any]]:
    from jarvis.calendar_store import work_blocks_for_day

    items = []
    for i, b in enumerate(work_blocks_for_day(day)):
        items.append(
            _item(
                id=f"work:{day}:{i}",
                title=b.get("label") or "Work",
                day=day,
                source="work",
                time=b.get("start") or "",
                end_hm=b.get("end") or "",
                kind="block",
                meta={"block": b},
            )
        )
    return items


def _holiday_items(day: str) -> list[dict[str, Any]]:
    items = []
    try:
        from jarvis.journal_holidays import holidays_for_month

        hol = holidays_for_month(day[:7]) or {}
        for h in hol.get(day) or []:
            name = h.get("name") if isinstance(h, dict) else str(h)
            items.append(
                _item(
                    id=f"holiday:{day}:{name}",
                    title=str(name),
                    day=day,
                    source="holiday",
                    kind="holiday",
                    all_day=True,
                )
            )
    except Exception as exc:
        log.debug("holidays: %s", exc)
    return items


def _timers_alarms(day: str) -> list[dict[str, Any]]:
    if day != today_iso():
        return []
    items = []
    try:
        from jarvis.planner_store import active_timers, list_alarms, planner_enabled

        if not planner_enabled():
            return items
        for t in active_timers():
            items.append(
                _item(
                    id=f"timer:{t.get('id')}",
                    title=t.get("label") or "Timer",
                    day=day,
                    source="timer",
                    kind="timer",
                    meta={"remaining_seconds": t.get("remaining_seconds"), "paused": t.get("paused")},
                )
            )
        for a in list_alarms():
            fire = a.get("fire_at") or ""
            if fire[:10] != day:
                continue
            items.append(
                _item(
                    id=f"alarm:{a.get('id')}",
                    title=a.get("label") or "Alarm",
                    day=day,
                    source="alarm",
                    time=fire[11:16] if len(fire) >= 16 else "",
                    kind="alarm",
                    meta={"fire_at": fire},
                )
            )
    except Exception as exc:
        log.debug("timers/alarms: %s", exc)
    return items


def schedule_for_day(journal, day: str | None = None) -> dict[str, Any]:
    """Unified schedule for one local day."""
    d = (day or today_iso())[:10]
    note = ""
    try:
        monthly = journal.monthly_calendar(d[:7])
        note = (monthly.get("calendar_notes") or {}).get(str(int(d[8:10])), "") or ""
    except Exception:
        note = ""

    ics_items, ics_status = _ics_items(d)
    items = (
        _holiday_items(d)
        + _work_items(d)
        + ics_items
        + _journal_items(journal, d)
        + _planner_events(d)
        + _planner_tasks_today(d)
        + _timers_alarms(d)
    )
    items.sort(key=sort_key_item)
    return {
        "ok": True,
        "day": d,
        "title": parse_day(d).strftime("%A, %B ") + str(parse_day(d).day) + ", " + str(parse_day(d).year),
        "calendar_note": note,
        "items": items,
        "ics_status": ics_status,
        "counts": {
            "total": len(items),
            "journal": sum(1 for i in items if i["source"] == "journal"),
            "planner": sum(1 for i in items if i["source"] == "planner"),
            "ics": sum(1 for i in items if i["source"] == "ics"),
        },
    }


def schedule_for_days(journal, days: list[str]) -> dict[str, Any]:
    by_day = {}
    ics_status = None
    for d in days:
        detail = schedule_for_day(journal, d)
        by_day[d] = detail
        ics_status = detail.get("ics_status") or ics_status
    return {"ok": True, "days": by_day, "ics_status": ics_status}


def month_schedule(journal, month: str | None = None) -> dict[str, Any]:
    from jarvis.calendar_ics import ics_url
    from jarvis.calendar_store import load_work_schedule
    from jarvis.modules.journal import _month_key

    mk = month or _month_key()
    cal = journal.monthly_calendar(mk)
    # Expand journal day_events to include untimed via schedule layer for each day that has bullets
    y, m = map(int, mk.split("-"))
    if m == 12:
        last = date(y + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(y, m + 1, 1) - timedelta(days=1)
    merged: dict[str, list] = {}
    for day_n in range(1, last.day + 1):
        day = f"{mk}-{day_n:02d}"
        detail = schedule_for_day(journal, day)
        chips = []
        for it in detail.get("items") or []:
            if it["source"] in ("work", "timer", "alarm") and it["kind"] != "event":
                if it["source"] == "work":
                    chips.append(
                        {
                            "time": it.get("time") or "",
                            "content": it.get("title"),
                            "source": "work",
                            "color": "work",
                            "id": it.get("id"),
                        }
                    )
                continue
            if it["kind"] in ("event", "holiday") or (
                it["kind"] == "task" and it["source"] == "planner" and not it.get("time")
            ):
                chips.append(
                    {
                        "time": it.get("time") or "",
                        "content": it.get("title"),
                        "source": it.get("source"),
                        "color": it.get("color"),
                        "id": it.get("id"),
                        "all_day": it.get("all_day"),
                    }
                )
        if chips:
            merged[day] = chips[:6]
        # work indicator flag
        if any(i["source"] == "work" for i in detail.get("items") or []):
            cal.setdefault("work_days", {})[str(day_n)] = True

    cal["events"] = merged
    cal["ics_url"] = ics_url()
    cal["work_schedule"] = load_work_schedule()
    from jarvis.calendar_ics import sync_status

    cal["ics_status"] = sync_status()
    cal["ok"] = True
    return cal


def week_schedule(journal, anchor: str | None = None) -> dict[str, Any]:
    days = week_dates(anchor)
    payload = schedule_for_days(journal, days)
    return {
        "ok": True,
        "view": "week",
        "anchor": anchor or today_iso(),
        "dates": days,
        "days": payload.get("days"),
        "ics_status": payload.get("ics_status"),
    }


def agenda_schedule(journal, *, days: int = 7, start: str | None = None) -> dict[str, Any]:
    dates = agenda_dates(days, start=start)
    payload = schedule_for_days(journal, dates)
    flat = []
    for d in dates:
        detail = (payload.get("days") or {}).get(d) or {}
        for it in detail.get("items") or []:
            if it["source"] == "work" and it["kind"] == "block":
                continue
            flat.append(it)
    # Free-time heuristic for today
    free = _free_windows(payload.get("days") or {}, dates[0] if dates else today_iso())
    return {
        "ok": True,
        "view": "agenda",
        "dates": dates,
        "items": flat,
        "days": payload.get("days"),
        "free_windows": free,
        "ics_status": payload.get("ics_status"),
    }


def timeline_schedule(journal, day: str | None = None) -> dict[str, Any]:
    d = (day or today_iso())[:10]
    detail = schedule_for_day(journal, d)
    now = now_local()
    now_hm = format_hm(now) if d == today_iso() else None
    items = [i for i in detail.get("items") or [] if i["kind"] in ("event", "block", "alarm", "timer", "holiday", "task")]
    # Next meeting
    next_item = None
    if now_hm:
        for it in items:
            t = it.get("time") or ""
            if t and t >= now_hm and it["kind"] in ("event", "alarm"):
                next_item = it
                break
    free = _free_windows({d: detail}, d)
    countdown_min = None
    if next_item and next_item.get("time") and now_hm:
        try:
            nh, nm = map(int, now_hm.split(":"))
            th, tm = map(int, next_item["time"].split(":"))
            countdown_min = (th * 60 + tm) - (nh * 60 + nm)
        except Exception:
            countdown_min = None
    return {
        "ok": True,
        "view": "timeline",
        "day": d,
        "now_hm": now_hm,
        "items": items,
        "next": next_item,
        "countdown_min": countdown_min,
        "free_windows": free,
        "focus_windows": [w for w in free if w.get("minutes", 0) >= 45],
        "calendar_note": detail.get("calendar_note"),
        "ics_status": detail.get("ics_status"),
        "counts": detail.get("counts"),
    }


def _free_windows(days: dict, day: str) -> list[dict[str, Any]]:
    detail = days.get(day) or {}
    busy = []
    for it in detail.get("items") or []:
        t = it.get("time") or ""
        if not t or it["kind"] not in ("event", "block"):
            continue
        start_m = int(t[:2]) * 60 + int(t[3:5])
        dur = int(it.get("duration_min") or 45)
        if it.get("end_hm"):
            try:
                eh, em = map(int, it["end_hm"].split(":"))
                dur = max(15, eh * 60 + em - start_m)
            except Exception:
                pass
        busy.append((start_m, start_m + dur))
    busy.sort()
    windows = []
    cursor = 8 * 60  # 08:00
    end_day = 21 * 60
    for b0, b1 in busy:
        if b0 > cursor + 20:
            windows.append(
                {
                    "start_hm": f"{cursor // 60:02d}:{cursor % 60:02d}",
                    "end_hm": f"{b0 // 60:02d}:{b0 % 60:02d}",
                    "minutes": b0 - cursor,
                }
            )
        cursor = max(cursor, b1)
    if end_day > cursor + 20:
        windows.append(
            {
                "start_hm": f"{cursor // 60:02d}:{cursor % 60:02d}",
                "end_hm": f"{end_day // 60:02d}:{end_day % 60:02d}",
                "minutes": end_day - cursor,
            }
        )
    return windows


# --- Mutations (route to owning store) ---


def create_commitment(
    journal,
    *,
    title: str,
    day: str | None = None,
    time: str | None = None,
    target: str = "planner",
    duration_min: int = 30,
) -> dict[str, Any]:
    """Create a scheduled user event in the Planner event store.

    Calendar is a read model over several sources, but Planner owns durable user
    event writes. Journal bullets may still project into Calendar for historical
    notes/events, never as the target for new Calendar event creation.
    """
    title = (title or "").strip()
    if not title:
        raise ValueError("Title required")
    d = (day or today_iso())[:10]
    hm = validate_time_hm(time) if time else None
    target = (target or "journal").lower().strip()
    if target not in ("planner", "journal", "calendar", "event", ""):
        raise ValueError("target must be planner/calendar/journal")
    from jarvis.planner_store import add_event

    ev = add_event(title, when=d, time_str=hm or "09:00", duration_min=duration_min)
    return {"ok": True, "target": "planner", "event": ev, "item_id": f"planner:{ev.get('id')}"}


def update_commitment(
    journal,
    item_id: str,
    *,
    title: str | None = None,
    time: str | None = None,
    day: str | None = None,
    duration_min: int | None = None,
) -> dict[str, Any]:
    if item_id.startswith("journal:") or item_id.startswith("journal-task:"):
        bid = item_id.split(":", 1)[1]
        found = journal.bullet_resolve(bid)
        if not found:
            raise ValueError("Journal item not found")
        if title is not None:
            journal.bullet_update(bid, content=title)
        if time is not None:
            hm = validate_time_hm(time) if time else None
            journal.bullet_set_time(bid, hm, duration_min)
        if day:
            # Move: recreate on target day, delete original (works for events + tasks)
            src = journal.bullet_resolve(bid) or found
            new_b = journal.daily_add(
                src.get("content") or title or "",
                src.get("type") or "event",
                src.get("signifiers"),
                day=day,
                time=src.get("time"),
            )
            journal.bullet_delete(bid)
            return {"ok": True, "bullet": new_b, "moved": True}
        return {"ok": True, "bullet": journal.bullet_resolve(bid)}
    if item_id.startswith("planner:"):
        from jarvis.planner_store import update_event

        eid = item_id.split(":", 1)[1]
        ev = update_event(
            eid,
            title=title,
            time_str=validate_time_hm(time) if time is not None and time != "" else (None if time is None else None),
            when=day,
            duration_min=duration_min,
        )
        # Clear time if blank string requested
        if time == "":
            # update_event may not clear — leave as-is if unsupported
            pass
        return {"ok": True, "event": ev}
    if item_id.startswith("planner-task:"):
        from jarvis.planner_store import update_task

        tid = item_id.split(":", 1)[1]
        task = update_task(tid, text=title, due_date=day)
        return {"ok": True, "task": task}
    raise ValueError(f"Item not editable: {item_id}")


def delete_commitment(journal, item_id: str) -> dict[str, Any]:
    if item_id.startswith("journal:") or item_id.startswith("journal-task:"):
        bid = item_id.split(":", 1)[1]
        ok = journal.bullet_delete(bid)
        return {"ok": bool(ok)}
    if item_id.startswith("planner:"):
        from jarvis.planner_store import delete_event

        return delete_event(item_id.split(":", 1)[1])
    if item_id.startswith("planner-task:"):
        from jarvis.planner_store import delete_task

        return delete_task(item_id.split(":", 1)[1])
    raise ValueError(f"Item not deletable: {item_id}")


def duplicate_commitment(journal, item_id: str, *, day: str | None = None) -> dict[str, Any]:
    detail_day = day or today_iso()
    if item_id.startswith("journal:") or item_id.startswith("journal-task:"):
        bid = item_id.split(":", 1)[1]
        b = journal.bullet_duplicate_to_daily(bid, detail_day)
        return {"ok": True, "bullet": b}
    if item_id.startswith("planner:"):
        from jarvis.planner_store import add_event, events_for_day

        # find original
        eid = item_id.split(":", 1)[1]
        src = None
        for e in events_for_day(detail_day):
            if e.get("id") == eid:
                src = e
                break
        if not src:
            # search nearby days
            for offset in range(-7, 8):
                d = (parse_day(detail_day) + timedelta(days=offset)).isoformat()
                for e in events_for_day(d):
                    if e.get("id") == eid:
                        src = e
                        break
                if src:
                    break
        if not src:
            raise ValueError("Planner event not found")
        start = src.get("start_time") or ""
        hm = start[11:16] if len(start) >= 16 else "09:00"
        ev = add_event(f"{src.get('title')} (copy)", when=detail_day, time_str=hm)
        return {"ok": True, "event": ev}
    raise ValueError(f"Cannot duplicate: {item_id}")


def complete_commitment(journal, item_id: str) -> dict[str, Any]:
    if item_id.startswith("journal:") or item_id.startswith("journal-task:"):
        bid = item_id.split(":", 1)[1]
        b = journal.bullet_complete(bid)
        return {"ok": True, "bullet": b}
    if item_id.startswith("planner-task:"):
        from jarvis.planner_store import complete_task

        ok = complete_task(item_id.split(":", 1)[1])
        return {"ok": bool(ok)}
    raise ValueError("Only tasks can be completed")
