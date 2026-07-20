"""Relative temporal cue resolution for autobiographical episodic events.

LM-independent · host-independent. Resolves conversational time phrases into
approximate absolute windows used as Experience.t_start / filter bounds.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from time import time

_DAY = 86400.0
_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_TEMPORAL_TOKEN = re.compile(
    r"\b("
    r"yesterday|today|this\s+morning|this\s+afternoon|this\s+evening|"
    r"last\s+night|last\s+week|last\s+month|"
    r"last\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
    r")\b",
    re.I,
)


@dataclass(frozen=True)
class TemporalWindow:
    """Resolved relative time window for an episodic event or query."""

    cue: str
    t_start: float
    t_end: float
    label: str

    @property
    def midpoint(self) -> float:
        return self.t_start + max(0.0, (self.t_end - self.t_start) * 0.5)


def normalize_temporal_cue(raw: str) -> str:
    """Normalize a temporal phrase to a stable cue key."""
    s = re.sub(r"\s+", " ", (raw or "").strip().lower())
    return s.replace(" ", "_")


def extract_temporal_cue(text: str) -> str | None:
    """Return the first relative temporal cue in text, or None."""
    m = _TEMPORAL_TOKEN.search(text or "")
    if not m:
        return None
    return normalize_temporal_cue(m.group(1))


def resolve_temporal_window(
    cue: str,
    *,
    now: float | None = None,
) -> TemporalWindow | None:
    """Map a normalized cue (e.g. ``yesterday``) to a time window.

    Windows are approximate local-calendar buckets relative to ``now``.
    """
    key = normalize_temporal_cue(cue)
    if not key:
        return None
    now = time() if now is None else float(now)
    # Local civil day bounds from epoch (host timezone).
    lt = __import__("datetime").datetime.fromtimestamp(now)
    day_start = lt.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    day_end = day_start + _DAY - 1.0

    if key == "today":
        return TemporalWindow(key, day_start, day_end, "today")
    if key == "yesterday":
        return TemporalWindow(key, day_start - _DAY, day_start - 1.0, "yesterday")
    if key == "this_morning":
        return TemporalWindow(key, day_start, day_start + 12 * 3600 - 1.0, "this morning")
    if key == "this_afternoon":
        return TemporalWindow(
            key, day_start + 12 * 3600, day_start + 17 * 3600 - 1.0, "this afternoon"
        )
    if key == "this_evening":
        return TemporalWindow(key, day_start + 17 * 3600, day_end, "this evening")
    if key == "last_night":
        return TemporalWindow(
            key, day_start - 6 * 3600, day_start - 1.0, "last night"
        )
    if key == "last_week":
        # Prior 7 calendar days ending yesterday (exclude today).
        return TemporalWindow(
            key, day_start - 7 * _DAY, day_start - 1.0, "last week"
        )
    if key == "last_month":
        year, month = lt.year, lt.month
        if month == 1:
            year, month = year - 1, 12
        else:
            month -= 1
        first = lt.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(year, month)[1]
        last = first.replace(day=last_day, hour=23, minute=59, second=59)
        return TemporalWindow(
            key, first.timestamp(), last.timestamp(), "last month"
        )
    if key.startswith("last_"):
        wd = key.replace("last_", "", 1)
        target = _WEEKDAYS.get(wd)
        if target is None:
            return None
        # Most recent prior occurrence of that weekday (not today if same).
        delta = (lt.weekday() - target) % 7
        if delta == 0:
            delta = 7
        start = day_start - delta * _DAY
        return TemporalWindow(
            key, start, start + _DAY - 1.0, f"last {wd}"
        )
    return None


def window_contains(window: TemporalWindow, t: float) -> bool:
    return window.t_start <= float(t) <= window.t_end
