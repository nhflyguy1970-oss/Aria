"""Health reminders — Notifications owns delivery; Health owns the schedule."""

from __future__ import annotations

import re
import time
from datetime import date, datetime
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

_MEDICAL_CAL_RE = re.compile(
    r"\b(doctor|dr\.|physician|clinic|lab|hospital|dentist|specialist|appointment|physical|follow-?up)\b",
    re.I,
)


def due_reminders() -> list[dict[str, Any]]:
    today = date.today().isoformat()
    checkin = store.get_checkin(today)
    due = []
    for rem in store.list_table("reminders", "enabled=?", (1,), limit=50):
        kind = str(rem.get("kind") or "")
        last = rem.get("last_fired")
        fired_today = False
        if last:
            try:
                fired_today = datetime.fromtimestamp(float(last)).date().isoformat() == today
            except Exception:
                fired_today = False
        if fired_today:
            continue
        if kind == "checkin" and checkin:
            continue
        due.append(rem)
    return due


def mark_fired(reminder_id: str) -> None:
    rec = store.get_by_id("reminders", reminder_id)
    if not rec:
        return
    rec["last_fired"] = time.time()
    store.upsert_reminder(rec)


def fire_due_reminders() -> dict[str, Any]:
    due = due_reminders()
    published = []
    for rem in due:
        try:
            from jarvis.notifications_product.pipeline import publish

            out = publish(
                {
                    "title": rem.get("title") or "Health reminder",
                    "summary": rem.get("notes") or rem.get("title") or "Health reminder",
                    "severity": "info",
                    "source": "health",
                    "category": "health",
                    "type": "health_reminder",
                    "deepLink": "health",
                    "product": "health",
                    "toast": True,
                }
            )
            mark_fired(str(rem.get("id")))
            published.append({"id": rem.get("id"), "ok": out.get("ok"), "title": rem.get("title")})
        except Exception as exc:
            published.append({"id": rem.get("id"), "ok": False, "error": str(exc)[:200]})
    return {"ok": True, "due": due, "published": published, "disclaimer": DISCLAIMER}


def related_calendar_appointments(*, days: int = 14) -> list[dict[str, Any]]:
    try:
        from jarvis.calendar_schedule import agenda_schedule
        from jarvis.modules.journal import Journal

        agenda = agenda_schedule(Journal(), days=days)
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    days_map = agenda.get("days") or agenda.get("items") or {}
    if isinstance(days_map, list):
        for item in days_map:
            title = str(item.get("title") or item.get("summary") or "")
            if title and _MEDICAL_CAL_RE.search(title):
                out.append(
                    {
                        "day": item.get("day") or item.get("date") or "",
                        "time": item.get("time") or "",
                        "title": title,
                    }
                )
        return out[:20]
    if isinstance(days_map, dict):
        for day, payload in days_map.items():
            items = payload.get("items") if isinstance(payload, dict) else payload
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title") or item.get("summary") or "")
                if title and _MEDICAL_CAL_RE.search(title):
                    out.append({"day": str(day)[:10], "time": item.get("time") or "", "title": title})
    return out[:20]


def maybe_sync_appointment_to_calendar(rem: dict[str, Any]) -> dict[str, Any] | None:
    kind = str(rem.get("kind") or "")
    if kind not in ("appointment", "appointments", "doctor", "refill"):
        return None
    schedule = str(rem.get("schedule") or "").strip()
    day = None
    time_hm = None
    if m := re.search(r"(20\d{2}-\d{2}-\d{2})", schedule):
        day = m.group(1)
    if m := re.search(r"\b(\d{1,2}:\d{2})\b", schedule):
        time_hm = m.group(1)
    if not day:
        return None
    try:
        from jarvis.calendar_schedule import create_commitment
        from jarvis.modules.journal import Journal

        return create_commitment(Journal(), title=str(rem.get("title") or "Health appointment"), day=day, time=time_hm, target="planner")
    except Exception:
        return None


def reminder_message() -> dict[str, Any]:
    due = due_reminders()
    rows = store.list_table("reminders", limit=40)
    appts = related_calendar_appointments()
    lines = ["**Health reminders**"]
    if not rows:
        lines.append(
            "None configured. You can add check-in, medication, supplement, BP, sugar, weight, refill, appointment, exercise, or hydration reminders in Health."
        )
    else:
        for r in rows:
            flag = "due" if r.get("enabled") and any(d.get("id") == r.get("id") for d in due) else ("on" if r.get("enabled") else "off")
            lines.append(f"• [{flag}] {r.get('kind')}: {r.get('title')} ({r.get('schedule') or 'unscheduled'})")
    if appts:
        lines += ["", "**Related calendar appointments**"]
        lines.extend(f"• {a.get('day')} {a.get('time') or ''} — {a.get('title')}".strip() for a in appts[:8])
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "reminders",
        "reminders": rows,
        "due": due,
        "calendar": appts,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
    }
