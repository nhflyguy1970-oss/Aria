"""ICS subscribe layer — cached fetch, sync status, basic RRULE support."""

from __future__ import annotations

import logging
import os
import re
import time
import urllib.request
from datetime import date, datetime, timedelta
from typing import Any

from jarvis.calendar_time import format_hm, local_tz, parse_day, today_iso

log = logging.getLogger("jarvis.calendar.ics")

# In-memory cache: {url: {fetched_at, text, etag, error, events_by_day}}
_CACHE: dict[str, dict[str, Any]] = {}
_CACHE_TTL_SEC = int(os.getenv("JARVIS_ICS_CACHE_TTL", "300"))
_STATUS: dict[str, Any] = {
    "ok": True,
    "url": "",
    "last_sync": None,
    "last_error": None,
    "event_count": 0,
    "cached": False,
}


def ics_url() -> str:
    return (os.getenv("JARVIS_ICS_URL") or os.getenv("JARVIS_CALENDAR_ICS_URL") or "").strip()


def sync_status() -> dict[str, Any]:
    url = ics_url()
    st = dict(_STATUS)
    st["url"] = url
    st["configured"] = bool(url)
    if url and url in _CACHE:
        st["cached"] = True
        st["cache_age_sec"] = int(time.time() - _CACHE[url].get("fetched_at", 0))
    return st


def clear_ics_cache() -> None:
    _CACHE.clear()


def _unfold(text: str) -> str:
    return re.sub(r"\r?\n[ \t]", "", text)


def _parse_dt_value(value: str, *, params: str = "") -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    tz = local_tz()
    # DATE only
    if "VALUE=DATE" in params.upper() or (len(raw) == 8 and raw.isdigit()):
        try:
            d = datetime.strptime(raw[:8], "%Y%m%d")
            return d.replace(tzinfo=tz)
        except ValueError:
            return None
    if raw.endswith("Z"):
        try:
            dt = datetime.strptime(raw[:15], "%Y%m%dT%H%M%S").replace(tzinfo=__import__("datetime").timezone.utc)
            return dt.astimezone(tz)
        except ValueError:
            pass
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%dT%H%M%S%z"):
        try:
            chunk = raw[:15] if fmt.endswith("%S") and "+" not in raw and "-" not in raw[8:] else raw
            if fmt.endswith("%z") and len(raw) >= 15:
                dt = datetime.strptime(raw.replace("Z", "+0000")[:19] + (raw[-5:] if len(raw) > 15 else ""), "%Y%m%dT%H%M%S%z")
                return dt.astimezone(tz)
            dt = datetime.strptime(raw[:15], "%Y%m%dT%H%M%S")
            return dt.replace(tzinfo=tz)
        except ValueError:
            continue
    if len(raw) >= 8 and raw[:8].isdigit():
        try:
            d = datetime.strptime(raw[:8], "%Y%m%d")
            if "T" in raw and len(raw) >= 13:
                return d.replace(hour=int(raw[9:11]), minute=int(raw[11:13]), tzinfo=tz)
            return d.replace(tzinfo=tz)
        except ValueError:
            pass
    return None


def _field(chunk: str, name: str) -> tuple[str, str]:
    """Return (params, value) for first matching property."""
    for line in chunk.splitlines():
        line = line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith(name + ":") or upper.startswith(name + ";"):
            if ":" not in line:
                continue
            left, right = line.split(":", 1)
            params = left[len(name) :]
            return params, right.strip()
    return "", ""


def _parse_rrule(rrule: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for part in (rrule or "").split(";"):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        out[k.upper()] = v
    return out


def _rrule_dates(start: datetime, rrule: str, *, window_start: date, window_end: date) -> list[datetime]:
    """Expand basic daily/weekly/monthly RRULEs inside [window_start, window_end)."""
    rules = _parse_rrule(rrule)
    freq = (rules.get("FREQ") or "").upper()
    interval = int(rules.get("INTERVAL") or 1)
    count = int(rules.get("COUNT") or 0)
    until = None
    if rules.get("UNTIL"):
        until = _parse_dt_value(rules["UNTIL"])
    byday = [d.strip().upper() for d in (rules.get("BYDAY") or "").split(",") if d.strip()]
    weekday_map = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}

    results: list[datetime] = []
    cursor = start
    # Include start if in window
    limit = 400
    n = 0
    while n < limit:
        d = cursor.date()
        if until and cursor > until:
            break
        if count and len(results) >= count:
            break
        if d >= window_end:
            break
        if d >= window_start:
            ok = True
            if byday and freq == "WEEKLY":
                ok = cursor.weekday() in {weekday_map[x[-2:]] for x in byday if x[-2:] in weekday_map}
            if ok:
                results.append(cursor)
        if freq == "DAILY":
            cursor = cursor + timedelta(days=interval)
        elif freq == "WEEKLY":
            cursor = cursor + timedelta(days=7 * interval)
        elif freq == "MONTHLY":
            month = cursor.month - 1 + interval
            year = cursor.year + month // 12
            month = month % 12 + 1
            day = min(cursor.day, 28)
            try:
                cursor = cursor.replace(year=year, month=month, day=day)
            except ValueError:
                cursor = cursor + timedelta(days=30 * interval)
        else:
            # Unsupported frequency — only start instance
            break
        n += 1
        if not count and d > window_end + timedelta(days=366):
            break
    return results


def _parse_vevents(text: str, *, window_start: date, window_end: date) -> list[dict[str, Any]]:
    text = _unfold(text or "")
    events: list[dict[str, Any]] = []
    blocks = re.split(r"BEGIN:VEVENT", text, flags=re.I)
    for block in blocks[1:]:
        chunk = block.split("END:VEVENT", 1)[0]
        _sp, summary = _field(chunk, "SUMMARY")
        dp, dtstart = _field(chunk, "DTSTART")
        ep, dtend = _field(chunk, "DTEND")
        _rp, rrule = _field(chunk, "RRULE")
        _lp, location = _field(chunk, "LOCATION")
        if not summary:
            continue
        start = _parse_dt_value(dtstart, params=dp)
        if not start:
            continue
        end = _parse_dt_value(dtend, params=ep) if dtend else None
        all_day = "VALUE=DATE" in dp.upper() or (len(dtstart.strip()) == 8 and dtstart.strip().isdigit())
        instances = [start]
        if rrule:
            instances = _rrule_dates(start, rrule, window_start=window_start, window_end=window_end) or [start]
        duration = None
        if end and start:
            duration = max(15, int((end - start).total_seconds() // 60))
        for inst in instances:
            d = inst.date()
            if d < window_start or d >= window_end:
                continue
            time_str = "" if all_day else format_hm(inst)
            events.append(
                {
                    "id": f"ics:{d.isoformat()}:{summary[:40]}:{time_str}",
                    "summary": summary,
                    "title": summary,
                    "time": time_str,
                    "start_hm": time_str,
                    "day": d.isoformat(),
                    "source": "ics",
                    "location": location or "",
                    "all_day": all_day,
                    "duration_min": duration,
                    "recurring": bool(rrule),
                }
            )
    events.sort(key=lambda e: (e.get("day") or "", e.get("time") or "99:99", e.get("summary") or ""))
    return events


def _fetch_raw(url: str, *, force: bool = False) -> tuple[str, dict[str, Any]]:
    global _STATUS
    now = time.time()
    cached = _CACHE.get(url)
    if cached and not force and now - cached.get("fetched_at", 0) < _CACHE_TTL_SEC and cached.get("text"):
        _STATUS.update(
            {
                "ok": True,
                "url": url,
                "last_sync": cached.get("synced_at"),
                "last_error": None,
                "cached": True,
                "event_count": cached.get("event_count", 0),
            }
        )
        return cached["text"], {"from_cache": True}

    from jarvis.security.url_guard import UnsafeURLError, assert_safe_fetch_url

    try:
        safe = assert_safe_fetch_url(url)
    except UnsafeURLError as exc:
        _STATUS.update({"ok": False, "url": url, "last_error": str(exc), "cached": bool(cached)})
        log.warning("ICS URL blocked: %s", exc)
        if cached and cached.get("text"):
            return cached["text"], {"from_cache": True, "stale": True, "error": str(exc)}
        return "", {"error": str(exc)}

    try:
        req = urllib.request.Request(safe, headers={"User-Agent": "Jarvis/3.2 Calendar"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            final = getattr(resp, "geturl", lambda: safe)()
            try:
                assert_safe_fetch_url(final)
            except UnsafeURLError as exc:
                _STATUS.update({"ok": False, "last_error": str(exc)})
                log.warning("ICS redirect blocked: %s", exc)
                if cached and cached.get("text"):
                    return cached["text"], {"from_cache": True, "stale": True}
                return "", {"error": str(exc)}
            text = resp.read().decode("utf-8", errors="replace")
        synced = datetime.now().isoformat(timespec="seconds")
        _CACHE[url] = {
            "fetched_at": now,
            "synced_at": synced,
            "text": text,
            "event_count": 0,
        }
        _STATUS.update(
            {
                "ok": True,
                "url": url,
                "last_sync": synced,
                "last_error": None,
                "cached": False,
            }
        )
        log.info("ICS fetched ok (%s bytes)", len(text))
        return text, {"from_cache": False}
    except Exception as exc:
        log.warning("ICS fetch failed: %s", exc)
        _STATUS.update({"ok": False, "url": url, "last_error": str(exc), "cached": bool(cached)})
        if cached and cached.get("text"):
            return cached["text"], {"from_cache": True, "stale": True, "error": str(exc)}
        return "", {"error": str(exc)}


def fetch_events_for_range(
    start: date | str,
    end: date | str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Return events keyed by day plus sync meta for [start, end)."""
    url = ics_url()
    if not url:
        return {"events": {}, "status": sync_status(), "ok": True, "configured": False}
    ws = parse_day(start)
    we = parse_day(end)
    text, meta = _fetch_raw(url, force=force)
    if not text:
        return {
            "events": {},
            "status": sync_status(),
            "ok": False,
            "configured": True,
            "message": meta.get("error") or _STATUS.get("last_error") or "ICS unavailable",
        }
    items = _parse_vevents(text, window_start=ws, window_end=we)
    by_day: dict[str, list[dict[str, Any]]] = {}
    for e in items:
        by_day.setdefault(e["day"], []).append(e)
    if url in _CACHE:
        _CACHE[url]["event_count"] = sum(len(v) for v in by_day.values())
        _STATUS["event_count"] = _CACHE[url]["event_count"]
    return {
        "events": by_day,
        "status": sync_status(),
        "ok": True,
        "configured": True,
        "stale": bool(meta.get("stale")),
        "from_cache": bool(meta.get("from_cache")),
    }


def fetch_events_for_month(month: str) -> dict[str, list[dict[str, Any]]]:
    if not month:
        return {}
    try:
        y, m = map(int, month.split("-")[:2])
        start = date(y, m, 1)
        end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    except (TypeError, ValueError):
        return {}
    return fetch_events_for_range(start, end).get("events") or {}


def fetch_events_for_day(day: date | None = None) -> list[dict[str, Any]]:
    d = day or date.fromisoformat(today_iso())
    if isinstance(d, str):
        d = date.fromisoformat(d)
    end = d + timedelta(days=1)
    by = fetch_events_for_range(d, end).get("events") or {}
    return list(by.get(d.isoformat(), []))


def _parse_ics_events(text: str, day: date) -> list[dict[str, Any]]:
    """Backward-compatible helper used by movie_tiers.validate_ics_url."""
    end = day + timedelta(days=1)
    return _parse_vevents(text, window_start=day, window_end=end)


def refresh_ics(*, force: bool = True) -> dict[str, Any]:
    url = ics_url()
    if not url:
        return {"ok": False, "message": "No ICS URL configured", "status": sync_status()}
    d = date.fromisoformat(today_iso())
    result = fetch_events_for_range(d, d + timedelta(days=30), force=force)
    return {
        "ok": bool(result.get("ok")),
        "message": result.get("message")
        or ("ICS refreshed" if result.get("ok") else "ICS refresh failed"),
        "status": result.get("status") or sync_status(),
        "days": len(result.get("events") or {}),
    }
