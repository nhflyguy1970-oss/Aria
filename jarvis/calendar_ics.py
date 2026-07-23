"""Optional external calendar (ICS URL) for morning briefing."""

from __future__ import annotations

import logging
import os
import re
import urllib.request
from datetime import date, datetime
from typing import Any

log = logging.getLogger("jarvis")


def ics_url() -> str:
    return (os.getenv("JARVIS_ICS_URL") or os.getenv("JARVIS_CALENDAR_ICS_URL") or "").strip()


def _parse_dt(value: str, *, day: date) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+0000"
    for fmt in (
        "%Y%m%dT%H%M%S%z",
        "%Y%m%dT%H%M%S",
        "%Y%m%d",
    ):
        try:
            dt = datetime.strptime(
                raw[:15] if "T" in raw else raw[:8], fmt.split("T")[0] if "T" not in raw else fmt
            )
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            if "T" not in value and len(value.strip()) == 8:
                return dt.replace(hour=0, minute=0)
            return dt
        except ValueError:
            continue
    if len(raw) >= 8 and raw[:8].isdigit():
        try:
            d = datetime.strptime(raw[:8], "%Y%m%d")
            if d.date() != day:
                return None
            if "T" in raw and len(raw) >= 13:
                hh = int(raw[9:11])
                mm = int(raw[11:13])
                return d.replace(hour=hh, minute=mm)
            return d
        except ValueError:
            pass
    return None


def _parse_ics_events(text: str, day: date) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    blocks = re.split(r"BEGIN:VEVENT", text, flags=re.I)
    for block in blocks[1:]:
        chunk = block.split("END:VEVENT", 1)[0]
        summary = ""
        dtstart = ""
        for line in chunk.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.upper().startswith("SUMMARY"):
                summary = line.split(":", 1)[-1].strip()
            elif line.upper().startswith("DTSTART"):
                dtstart = line.split(":", 1)[-1].strip()
        if not summary:
            continue
        start = _parse_dt(dtstart, day=day)
        if not start or start.date() != day:
            continue
        time_str = start.strftime("%H:%M") if start.hour or start.minute else ""
        events.append({"summary": summary, "time": time_str, "source": "ics"})
    events.sort(key=lambda e: e.get("time") or "99:99")
    return events


def fetch_events_for_month(month: str) -> dict[str, list[dict[str, Any]]]:
    """Return ICS events keyed by YYYY-MM-DD for the given month."""
    url = ics_url()
    if not url or not month:
        return {}
    try:
        y, m = map(int, month.split("-")[:2])
        month_start = date(y, m, 1)
        if m == 12:
            month_end = date(y + 1, 1, 1)
        else:
            month_end = date(y, m + 1, 1)
    except (TypeError, ValueError):
        return {}
    try:
        from jarvis.security.url_guard import UnsafeURLError, assert_safe_fetch_url

        try:
            url = assert_safe_fetch_url(url)
        except UnsafeURLError as exc:
            log.debug("ICS URL blocked: %s", exc)
            return {}
        req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/3.2 Calendar"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            final = getattr(resp, "geturl", lambda: url)()
            try:
                assert_safe_fetch_url(final)
            except UnsafeURLError as exc:
                log.debug("ICS redirect blocked: %s", exc)
                return {}
            text = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        log.debug("ICS fetch failed: %s", exc)
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    day = month_start
    while day < month_end:
        events = _parse_ics_events(text, day)
        if events:
            out[day.isoformat()] = events
        day = date.fromordinal(day.toordinal() + 1)
    return out


def fetch_events_for_day(day: date | None = None) -> list[dict[str, Any]]:
    url = ics_url()
    if not url:
        return []
    day = day or date.today()
    try:
        from jarvis.security.url_guard import UnsafeURLError, assert_safe_fetch_url

        try:
            url = assert_safe_fetch_url(url)
        except UnsafeURLError as exc:
            log.debug("ICS URL blocked: %s", exc)
            return []
        req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/3.2 Calendar"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            final = getattr(resp, "geturl", lambda: url)()
            try:
                assert_safe_fetch_url(final)
            except UnsafeURLError as exc:
                log.debug("ICS redirect blocked: %s", exc)
                return []
            text = resp.read().decode("utf-8", errors="replace")
        return _parse_ics_events(text, day)
    except Exception as exc:
        log.debug("ICS fetch failed: %s", exc)
        return []
