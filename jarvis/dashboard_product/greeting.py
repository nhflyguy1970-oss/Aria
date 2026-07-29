"""Greeting helpers — honest personalization without inventing data."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def personalized_greeting(*, when: datetime | None = None, assistant: Any = None) -> str:
    """Time-based greeting with optional profile first name."""
    from jarvis.morning_briefing import profile_first_name, time_greeting

    when = when or datetime.now()
    base = time_greeting(when=when)
    name = None
    if assistant is not None:
        try:
            name = profile_first_name(getattr(assistant, "memory", None))
        except Exception:
            name = None
    if name:
        return f"{base}, {name}"
    return base


def greeting_payload(*, assistant: Any = None, when: datetime | None = None) -> dict[str, Any]:
    when = when or datetime.now()
    greeting = personalized_greeting(when=when, assistant=assistant)
    short = greeting.split(",")[0] if "," in greeting else greeting
    return {
        "greeting": greeting,
        "greeting_short": short,
        "welcome": "Welcome back" if when.hour >= 5 else "Still up?",
        "date": when.strftime("%A, %B %d"),
        "date_label": when.strftime("%A, %B %d"),
        "time": when.strftime("%I:%M %p").lstrip("0"),
        "time_display": when.strftime("%I:%M %p").lstrip("0"),
        "iso": when.isoformat(timespec="seconds"),
    }
