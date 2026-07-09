"""Morning briefing — journal, weather, and open tasks on launch or chat."""

from __future__ import annotations

import os
import re
from datetime import date, datetime
from typing import Any

from jarvis.config import _load_chat_settings, _write_chat_settings
from jarvis.journal_weather import format_weather_line, weather_for_day


def briefing_enabled() -> bool:
    return os.getenv("JARVIS_BRIEFING", "1") != "0"


def last_briefing_shown() -> str | None:
    state = _load_chat_settings().get("morning_briefing") or {}
    shown = state.get("last_shown")
    return str(shown) if shown else None


def mark_briefing_shown(day: str | None = None) -> None:
    d = day or date.today().isoformat()
    data = _load_chat_settings()
    data.setdefault("morning_briefing", {})["last_shown"] = d
    _write_chat_settings(data)


def should_show_launch_briefing(*, day: str | None = None) -> bool:
    if not briefing_enabled():
        return False
    d = day or date.today().isoformat()
    return last_briefing_shown() != d


def briefing_visible(*, force: bool = False, day: str | None = None) -> bool:
    """True when automatic UI (pinned card, launch popup) may show the briefing."""
    if force:
        return briefing_enabled()
    return should_show_launch_briefing(day=day)


def time_greeting(*, when: datetime | None = None) -> str:
    when = when or datetime.now()
    h = when.hour
    if 5 <= h < 12:
        return "Good morning"
    if 12 <= h < 17:
        return "Good afternoon"
    if 17 <= h < 22:
        return "Good evening"
    return "Hello"


def profile_first_name(memory_store) -> str | None:
    if memory_store is None:
        return None
    for entry in memory_store.list_entries(namespace="profile"):
        tags = entry.get("tags") or []
        if "name" not in tags:
            continue
        m = re.match(r"User's name is (.+?)\.?$", (entry.get("content") or "").strip(), re.I)
        if m:
            name = m.group(1).strip()
            return name.split()[0] if name else None
    return None


def _format_date_heading(d: date) -> str:
    return d.strftime("%A, %B ") + str(d.day)


def build_briefing(
    *,
    journal,
    memory_store=None,
    day: str | None = None,
    reference: datetime | None = None,
    include_quote: bool = True,
    include_news: bool = True,
    max_tasks: int = 8,
) -> dict[str, Any]:
    """Assemble briefing data and markdown for GUI or chat."""
    from jarvis.modules.journal import _format_bullet, _today

    if include_news and os.getenv("JARVIS_BRIEFING_NEWS", "1") == "0":
        include_news = False

    ref = reference or datetime.now()
    d_iso = day or _today()
    d = date.fromisoformat(d_iso)
    greeting = time_greeting(when=ref)
    name = profile_first_name(memory_store)
    salutation = f"{greeting}, {name}." if name else f"{greeting}."

    page = journal.daily_get(d_iso)
    weather = page.get("weather") or weather_for_day(d_iso) or {}
    weather_line = format_weather_line(weather) if weather else ""

    open_tasks = journal.open_tasks(limit=max_tasks)
    total_open = journal.stats().get("open_tasks", len(open_tasks))

    events: list[dict] = []
    today_tasks: list[dict] = []
    timeline = journal.daily_timeline(d_iso)
    for ev in timeline.get("events", []):
        events.append(
            {
                "type": "event",
                "content": ev.get("content", ""),
                "time": ev.get("time", ""),
            }
        )
    for b in page.get("bullets", []):
        if b.get("type") == "event" and not b.get("time"):
            events.append(b)
        elif b.get("type") == "task" and b.get("status") == "open":
            today_tasks.append(b)

    from jarvis.calendar_ics import fetch_events_for_day

    ics_events = fetch_events_for_day(d)
    calendar_note = ""
    try:
        from jarvis.modules.journal import _month_key

        mk = _month_key(d)
        monthly = journal.monthly_get(mk)
        calendar_note = (monthly.get("calendar_notes") or {}).get(str(d.day), "") or ""
    except Exception:
        calendar_note = ""

    prompts = page.get("prompts") or {}
    morning_q = prompts.get("morning_question") or ""
    morning_ref = (prompts.get("morning") or "").strip()

    lines = [salutation, ""]
    date_line = f"**{_format_date_heading(d)}**"
    lines.append(f"{date_line} · {weather_line}" if weather_line else date_line)

    news: dict[str, Any] = {"enabled": False, "national": [], "local": [], "local_place": None}
    if include_news:
        from jarvis.briefing_news import fetch_briefing_news, format_news_markdown

        news = fetch_briefing_news(
            memory_store=memory_store,
            weather=weather,
            force_refresh=True,
        )
        lines.extend(format_news_markdown(news))

    if events or ics_events:
        lines.extend(["", "**Today's schedule**"])
        for ev in events[:6]:
            t = ev.get("time") or ""
            content = ev.get("content") or ""
            if t:
                lines.append(f"- **{t}** {content}")
            else:
                lines.append(f"- {_format_bullet(ev)}")
        for ev in ics_events[:4]:
            t = ev.get("time") or ""
            summary = ev.get("summary") or ""
            prefix = f"**{t}** " if t else ""
            lines.append(f"- {prefix}{summary} _(calendar)_")

    if calendar_note:
        lines.extend(["", f"**Calendar note:** {calendar_note}"])

    if today_tasks:
        lines.extend(["", "**Today's tasks**"])
        for t in today_tasks[:6]:
            lines.append(f"- {_format_bullet(t)}")

    other_tasks = [
        t for t in open_tasks if not str(t.get("section", "")).startswith(f"daily:{d_iso}")
    ]
    if other_tasks:
        label = (
            f"**Also on your list ({total_open} open)**"
            if total_open > len(other_tasks)
            else "**Also on your list**"
        )
        lines.extend(["", label])
        for t in other_tasks[:max_tasks]:
            section = t.get("section", "")
            lines.append(f"- [{section}] {_format_bullet(t)}")
        if total_open > max_tasks:
            lines.append(
                f"- _…and {total_open - max_tasks} more — say **open tasks** for the full list._"
            )
    elif not today_tasks and not events:
        lines.extend(["", "No open journal tasks — you're clear."])

    if morning_ref:
        lines.extend(["", f"**Morning note:** {morning_ref}"])
    elif morning_q:
        lines.extend(["", f"*{morning_q}*"])

    if include_quote:
        q = page.get("quote") or {}
        if q.get("text"):
            author = q.get("author", "")
            lines.append("")
            lines.append(f"> {q['text']}")
            if author:
                lines.append(f"> — {author}")

    if os.getenv("JARVIS_BRIEFING_HOME", "1") != "0":
        from jarvis.home_assistant import briefing_home_lines

        home_lines = briefing_home_lines(limit=6)
        if home_lines:
            lines.extend(["", *home_lines])

    if os.getenv("JARVIS_BRIEFING_ENV", "1") != "0":
        try:
            from jarvis.environment import briefing_line

            env_line = briefing_line()
            if env_line:
                lines.extend(["", f"**Lab:** {env_line}"])
        except Exception:
            pass

    if os.getenv("JARVIS_BRIEFING_WORKSTATION", "1") != "0":
        try:
            from jarvis.workstation.operations import diagnose

            diag = diagnose(force=False)
            if not diag.get("ok"):
                issues = diag.get("issues") or []
                critical = [i for i in issues if i.get("severity") == "critical"]
                if critical:
                    lines.extend(
                        ["", f"**Attention:** {critical[0].get('message', 'workstation issue')}"]
                    )
        except Exception:
            pass

    from jarvis.branding import assistant_name

    lines.extend(
        [
            "",
            f"_Ask **{assistant_name()}** to expand any headline — or say **morning briefing** anytime._",
        ]
    )

    from jarvis.briefing_news import persist_briefing_headlines

    briefing_headlines = persist_briefing_headlines(news) if news.get("enabled") else []

    return {
        "day": d_iso,
        "greeting": greeting,
        "name": name,
        "salutation": salutation,
        "weather": weather,
        "weather_line": weather_line,
        "open_tasks": open_tasks,
        "open_task_count": total_open,
        "today_events": events,
        "ics_events": ics_events,
        "calendar_note": calendar_note,
        "today_tasks": today_tasks,
        "morning_question": morning_q,
        "morning_reflection": morning_ref,
        "news": news,
        "briefing_headlines": briefing_headlines,
        "markdown": "\n".join(lines),
    }
