"""Calendar timezone helpers — local-first, DST-safe day keys."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo


def local_tz() -> ZoneInfo | timezone:
    """Best-effort local timezone (falls back to system local)."""
    try:
        return datetime.now().astimezone().tzinfo or timezone.utc
    except Exception:
        return timezone.utc


def now_local() -> datetime:
    return datetime.now(local_tz())


def today_iso(*, when: datetime | None = None) -> str:
    """Local calendar date YYYY-MM-DD (never UTC midnight rollover)."""
    dt = when or now_local()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=local_tz())
    return dt.astimezone(local_tz()).date().isoformat()


def month_key(*, when: datetime | None = None) -> str:
    return today_iso(when=when)[:7]


def parse_day(day: str | date | None) -> date:
    if day is None:
        return date.fromisoformat(today_iso())
    if isinstance(day, date) and not isinstance(day, datetime):
        return day
    return date.fromisoformat(str(day)[:10])


def day_bounds(day: str | date) -> tuple[datetime, datetime]:
    """Local start/end of day as aware datetimes."""
    d = parse_day(day)
    tz = local_tz()
    start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
    end = start + timedelta(days=1)
    return start, end


def combine_local(day: str | date, time_str: str | None) -> datetime | None:
    """Combine YYYY-MM-DD + HH:MM into aware local datetime."""
    d = parse_day(day)
    if not time_str:
        return datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=local_tz())
    t = str(time_str).strip()
    try:
        if "T" in t:
            dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=local_tz())
            return dt.astimezone(local_tz())
        parts = t.replace(".", ":").split(":")
        hh = int(parts[0])
        mm = int(parts[1]) if len(parts) > 1 else 0
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            return None
        return datetime(d.year, d.month, d.day, hh, mm, 0, tzinfo=local_tz())
    except (TypeError, ValueError, IndexError):
        return None


def format_hm(dt: datetime | None) -> str:
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=local_tz())
    return dt.astimezone(local_tz()).strftime("%H:%M")


def validate_time_hm(time_str: str | None) -> str | None:
    """Return normalized HH:MM or None if empty; raise ValueError if invalid."""
    if time_str is None or str(time_str).strip() == "":
        return None
    t = str(time_str).strip().lower().replace(".", "")
    import re

    m = re.match(r"^(\d{1,2}):(\d{2})\s*(am|pm)?$", t)
    if not m:
        m2 = re.match(r"^(\d{1,2})\s*(am|pm)$", t)
        if not m2:
            raise ValueError(f"Invalid time: {time_str}")
        hh = int(m2.group(1))
        mm = 0
        ampm = m2.group(2)
    else:
        hh = int(m.group(1))
        mm = int(m.group(2))
        ampm = m.group(3)
    if ampm == "pm" and hh < 12:
        hh += 12
    if ampm == "am" and hh == 12:
        hh = 0
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise ValueError(f"Invalid time: {time_str}")
    return f"{hh:02d}:{mm:02d}"


def week_dates(anchor: str | date | None = None) -> list[str]:
    """Monday–Sunday ISO dates containing anchor (local)."""
    d = parse_day(anchor)
    monday = d - timedelta(days=d.weekday())
    return [(monday + timedelta(days=i)).isoformat() for i in range(7)]


def agenda_dates(days: int = 7, *, start: str | date | None = None) -> list[str]:
    d = parse_day(start)
    return [(d + timedelta(days=i)).isoformat() for i in range(max(1, days))]


def sort_key_item(item: dict[str, Any]) -> tuple:
    """Sort timed first by time, untimed last (stable)."""
    t = item.get("time") or item.get("start_hm") or ""
    if not t:
        return (1, "99:99", item.get("title") or item.get("content") or "")
    return (0, str(t)[:5], item.get("title") or item.get("content") or "")
