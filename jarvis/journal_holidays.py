"""US public holidays and common observances for bullet journal monthly calendars."""

from __future__ import annotations

import calendar
import os
from datetime import date, timedelta


def _holiday_state() -> str | None:
    st = os.getenv("JARVIS_HOLIDAY_STATE", "").strip().upper()
    if st:
        return st
    loc = os.getenv("JARVIS_WEATHER_LOCATION", "").strip().upper()
    if ", NH" in loc or loc.endswith(" NH"):
        return "NH"
    return None


def _include_observances() -> bool:
    return os.getenv("JARVIS_HOLIDAY_OBSERVANCES", "1").strip().lower() not in ("0", "false", "no")


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Nth weekday (0=Mon … 6=Sun) in month."""
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    count = 0
    for d in cal.itermonthdates(year, month):
        if d.month != month:
            continue
        if d.weekday() == weekday:
            count += 1
            if count == n:
                return d
    raise ValueError(f"weekday {weekday} occurrence {n} missing in {year}-{month:02d}")


def _last_weekday(year: int, month: int, weekday: int) -> date:
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    last: date | None = None
    for d in cal.itermonthdates(year, month):
        if d.month == month and d.weekday() == weekday:
            last = d
    if last is None:
        raise ValueError(f"weekday {weekday} missing in {year}-{month:02d}")
    return last


def _observe_fixed(d: date) -> date:
    """Federal-style weekend observation for fixed-date holidays."""
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def _easter_sunday(year: int) -> date:
    """Anonymous Gregorian algorithm."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = ((h + ell - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _us_federal_holidays(year: int) -> list[tuple[date, str]]:
    return [
        (_observe_fixed(date(year, 1, 1)), "New Year's Day"),
        (_nth_weekday(year, 1, calendar.MONDAY, 3), "Martin Luther King Jr. Day"),
        (_nth_weekday(year, 2, calendar.MONDAY, 3), "Presidents' Day"),
        (_last_weekday(year, 5, calendar.MONDAY), "Memorial Day"),
        (_observe_fixed(date(year, 6, 19)), "Juneteenth"),
        (_observe_fixed(date(year, 7, 4)), "Independence Day"),
        (_nth_weekday(year, 9, calendar.MONDAY, 1), "Labor Day"),
        (_nth_weekday(year, 10, calendar.MONDAY, 2), "Columbus Day"),
        (_observe_fixed(date(year, 11, 11)), "Veterans Day"),
        (_nth_weekday(year, 11, calendar.THURSDAY, 4), "Thanksgiving"),
        (_observe_fixed(date(year, 12, 25)), "Christmas Day"),
    ]


def _us_observances(year: int) -> list[tuple[date, str]]:
    """Widely recognized US dates (not necessarily days off work)."""
    thanksgiving = _nth_weekday(year, 11, calendar.THURSDAY, 4)
    return [
        (date(year, 2, 14), "Valentine's Day"),
        (date(year, 3, 17), "St. Patrick's Day"),
        (_easter_sunday(year), "Easter"),
        (_nth_weekday(year, 5, calendar.SUNDAY, 2), "Mother's Day"),
        (_nth_weekday(year, 6, calendar.SUNDAY, 3), "Father's Day"),
        (date(year, 10, 31), "Halloween"),
        (thanksgiving + timedelta(days=1), "Black Friday"),
        (date(year, 12, 24), "Christmas Eve"),
        (date(year, 12, 31), "New Year's Eve"),
    ]


def _nh_state_holidays(year: int) -> list[tuple[date, str]]:
    """New Hampshire observes the same schedule as US federal for public holidays."""
    return _us_federal_holidays(year)


def _add_holidays(
    out: dict[str, list[dict]],
    pairs: list[tuple[date, str]],
    kind: str,
) -> None:
    for d, name in pairs:
        key = d.isoformat()
        out.setdefault(key, []).append({"name": name, "kind": kind})


def holidays_for_year(year: int, *, state: str | None = None) -> dict[str, list[dict]]:
    """Holidays keyed by ISO date (YYYY-MM-DD)."""
    st = (state if state is not None else _holiday_state()) or ""
    out: dict[str, list[dict]] = {}
    kind = "state" if st == "NH" else "federal"
    federal = _nh_state_holidays(year) if st == "NH" else _us_federal_holidays(year)
    _add_holidays(out, federal, kind)
    if _include_observances():
        _add_holidays(out, _us_observances(year), "observance")
    return out


def holidays_for_month(month: str, *, state: str | None = None) -> dict[str, list[dict]]:
    """Holidays in YYYY-MM keyed by full date string."""
    y, _m = map(int, month.split("-"))
    all_year = holidays_for_year(y, state=state)
    prefix = f"{month}-"
    return {k: v for k, v in all_year.items() if k.startswith(prefix)}
