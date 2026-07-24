"""Cross-domain situational briefing — world state + weather + headlines."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any


def situational_enabled() -> bool:
    return os.getenv("JARVIS_SITUATIONAL_BRIEFING", "1") != "0"


def _personalized_greeting(*, when: datetime, memory_store, assistant=None) -> dict[str, Any]:
    from jarvis.morning_briefing import profile_first_name, time_greeting

    greet = time_greeting(when=when)
    name = profile_first_name(memory_store)
    text = f"{greet}, {name}." if name else f"{greet}."
    return {"greeting": text, "name": name}


def build_situational_briefing(
    *,
    journal,
    memory_store,
    assistant=None,
    include_news: bool = True,
) -> dict[str, Any]:
    """Combine world state, weather, and optional headlines."""
    from jarvis.branding import assistant_name
    from jarvis.journal_weather import format_weather_line, weather_for_day
    from jarvis.modules.journal import _today
    from jarvis.morning_briefing import profile_first_name, time_greeting
    from jarvis.world_state import refresh_world_state_cache, world_state_summary

    ref = datetime.now()
    d_iso = _today()
    greeting = _personalized_greeting(when=ref, memory_store=memory_store, assistant=assistant)
    state = refresh_world_state_cache(memory_store=memory_store)
    world_md = world_state_summary(state)

    page = journal.daily_get(d_iso) if journal else {}
    weather = (page or {}).get("weather") or weather_for_day(d_iso) or {}
    weather_line = format_weather_line(weather) if weather else ""

    lines = [
        greeting.get("greeting") or f"{time_greeting(when=ref)}.",
        "",
        "**Situational status**",
        world_md,
    ]
    if weather_line:
        lines.extend(["", f"**Weather:** {weather_line}"])

    news: dict[str, Any] = {"enabled": False, "national": [], "local": []}
    if include_news and os.getenv("JARVIS_BRIEFING_NEWS", "1") != "0":
        from jarvis.briefing_news import fetch_briefing_news, format_news_markdown

        news = fetch_briefing_news(
            memory_store=memory_store,
            weather=weather,
            force_refresh=False,
        )
        block = format_news_markdown(news)
        if block:
            lines.extend(block if isinstance(block, list) else [block])

    open_tasks = journal.open_tasks(limit=5) if journal else []
    if open_tasks:
        total = journal.stats().get("open_tasks", len(open_tasks))
        lines.extend(["", f"**Open tasks ({total})**"])
        for t in open_tasks[:5]:
            lines.append(f"- {(t.get('content') or '')[:100]}")

    lines.extend(
        [
            "",
            f"_Say **situational briefing** or **what's my status** anytime · {assistant_name()}_",
        ]
    )
    return {
        "day": d_iso,
        "greeting": greeting,
        "world_state": state,
        "weather": weather,
        "weather_line": weather_line,
        "news": news,
        "markdown": "\n".join(lines),
        "name": profile_first_name(memory_store),
    }
