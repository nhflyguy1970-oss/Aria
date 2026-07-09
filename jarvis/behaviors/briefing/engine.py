"""Briefing action implementations — morning briefing and news detail expansion."""

from __future__ import annotations

from jarvis.behaviors.briefing.context import BriefingContext
from jarvis.response import err, ok


class BriefingEngine:
    @classmethod
    def morning_briefing(cls, ctx: BriefingContext, params: dict, message: str) -> dict:
        from jarvis.briefing_news import persist_briefing_headlines
        from jarvis.morning_briefing import build_briefing, mark_briefing_shown

        briefing = build_briefing(journal=ctx.journal, memory_store=ctx.memory_store)
        mark_briefing_shown(briefing["day"])
        headlines = briefing.get("briefing_headlines") or persist_briefing_headlines(
            briefing.get("news") or {}
        )
        if headlines:
            ctx.session.note_briefing_headlines(headlines)
        return ok(
            briefing["markdown"],
            module="briefing",
            type="briefing",
            open_task_count=briefing["open_task_count"],
            weather_line=briefing["weather_line"],
        )

    @classmethod
    def briefing_news_detail(cls, ctx: BriefingContext, params: dict, message: str) -> dict:
        from jarvis.briefing_news import (
            expand_headline_detail,
            load_recent_headlines,
            match_headline,
        )
        from jarvis.profiles import web_search_disabled

        headlines = ctx.session.last_briefing_headlines or load_recent_headlines()
        if not headlines:
            return err(
                "No briefing headlines saved yet. Say **morning briefing** first.",
                module="briefing",
            )

        query = (params.get("query") or message or "").strip()
        title_hint = (params.get("title") or "").strip()
        headline = match_headline(title_hint or query, headlines)
        if not headline and title_hint:
            headline = match_headline(title_hint, headlines)
        if not headline:
            national = [h for h in headlines if h.get("category") == "national"]
            local = [h for h in headlines if h.get("category") == "local"]
            parts: list[str] = []
            for index, item in enumerate(national[:6], 1):
                parts.append(f"National {index}. {item.get('title', 'Headline')}")
            for index, item in enumerate(local[:6], 1):
                parts.append(f"Local {index}. {item.get('title', 'Headline')}")
            listing = "\n".join(parts) or "\n".join(
                f"{index}. {item.get('title', 'Headline')}" for index, item in enumerate(headlines[:8], 1)
            )
            return ok(
                "Which briefing story should I expand?\n\n"
                f"{listing}\n\n"
                "Reply with **local headline 2**, **national headline 1**, or words from the title.",
                module="briefing",
                type="clarification",
            )

        if web_search_disabled():
            return err(
                "Web search is disabled (offline profile). Switch profile to expand briefing stories.",
                module="briefing",
            )

        answer = expand_headline_detail(headline, user_query=query)
        ctx.session.note_briefing_headlines(headlines)
        return ok(
            answer,
            module="briefing",
            type="news_detail",
            headline=headline,
        )
