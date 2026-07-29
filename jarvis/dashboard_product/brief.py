"""Daily Brief — one presentation card; Morning Briefing owns source data."""

from __future__ import annotations

from typing import Any


def build_daily_brief(*, assistant: Any = None) -> dict[str, Any]:
    """Aggregate Morning Briefing + light product glances. Never invent facts."""
    out: dict[str, Any] = {
        "available": False,
        "empty": True,
        "title": "Daily Brief",
        "salutation": "",
        "markdown": "",
        "sections": [],
        "deep_links": [
            {"label": "Open Chat briefing", "view": "chat", "action": "briefing"},
            {"label": "Planner", "view": "planner"},
            {"label": "Calendar", "view": "calendar"},
            {"label": "Journal", "view": "journal"},
        ],
        "coach": "",
        "source": "morning_briefing",
    }

    try:
        from jarvis.morning_briefing import briefing_enabled, build_briefing
    except Exception as exc:
        out["error"] = str(exc)
        out["coach"] = "Morning Briefing module unavailable."
        return out

    if not briefing_enabled():
        out["coach"] = "Morning Briefing is disabled (JARVIS_BRIEFING=0)."
        out["available"] = False
        return out

    journal = getattr(assistant, "journal", None) if assistant is not None else None
    if journal is None:
        try:
            from jarvis.modules.journal import Journal

            journal = Journal()
        except Exception:
            out["coach"] = "Journal not ready — Daily Brief needs Journal + Morning Briefing."
            return out

    try:
        brief = build_briefing(
            journal=journal,
            memory_store=getattr(assistant, "memory", None) if assistant else None,
            include_quote=False,
            include_news=False,  # News is a separate Home widget; avoid slow network on aggregate
            max_tasks=6,
        )
    except Exception as exc:
        out["error"] = str(exc)
        out["coach"] = "Could not build Daily Brief — check Journal and Calendar."
        return out

    sections: list[dict[str, Any]] = []
    if brief.get("weather_line"):
        sections.append({"id": "weather", "title": "Weather", "body": brief.get("weather_line")})
    if brief.get("events") or brief.get("ics_events"):
        sections.append(
            {
                "id": "schedule",
                "title": "Schedule",
                "body": f"{len(brief.get('events') or []) + len(brief.get('ics_events') or [])} items today",
            }
        )
    tasks = brief.get("today_tasks") or brief.get("open_tasks") or []
    if tasks:
        sections.append({"id": "tasks", "title": "Tasks", "body": f"{len(tasks)} open"})
    news = brief.get("news") or {}
    headlines = (news.get("national") or [])[:2] + (news.get("local") or [])[:1]
    if headlines:
        sections.append(
            {
                "id": "news",
                "title": "News",
                "body": "; ".join(str(h.get("title") or h)[:80] for h in headlines if h),
            }
        )

    md = (brief.get("markdown") or "").strip()
    out.update(
        {
            "available": True,
            "empty": not bool(md or sections),
            "salutation": brief.get("salutation") or brief.get("greeting") or "",
            "markdown": md[:4000],
            "preview": md.split("\n")[0][:200] if md else (sections[0]["body"] if sections else ""),
            "sections": sections,
            "weather_line": brief.get("weather_line") or "",
            "date_heading": brief.get("date_heading") or "",
            "coach": "" if (md or sections) else "Briefing is empty — add Journal bullets or enable news.",
            "render": "show" if (md or sections) else "coach",
        }
    )
    return out
