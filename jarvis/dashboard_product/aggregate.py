"""Home aggregate — gather product summaries into honest widgets."""

from __future__ import annotations

import logging
import time
from typing import Any

from jarvis.dashboard_product.attention import build_attention
from jarvis.dashboard_product.brief import build_daily_brief
from jarvis.dashboard_product.cache import load_layout, save_last_good
from jarvis.dashboard_product.greeting import greeting_payload
from jarvis.dashboard_product.schema import make_widget

logger = logging.getLogger("jarvis.dashboard_product.aggregate")


def _safe(label: str, fn):
    try:
        return fn(), None
    except Exception as exc:
        logger.warning("dashboard aggregate %s: %s", label, exc)
        return None, str(exc)


def _weather_widget(assistant: Any) -> dict[str, Any]:
    weather: dict[str, Any] = {}
    err = None
    try:
        from datetime import date

        from jarvis.journal_weather import format_weather_line, weather_for_day

        w = weather_for_day(date.today().isoformat()) or {}
        if w:
            weather = {
                "summary": format_weather_line(w) or w.get("summary") or w.get("condition") or "",
                "condition": w.get("condition") or w.get("summary") or "",
                "high": w.get("high") or w.get("temp_high"),
                "low": w.get("low") or w.get("temp_low"),
                "unit": w.get("unit") or "°",
                "location": w.get("location") or w.get("place") or "",
                "icon": w.get("icon") or "",
                "hint": "",
            }
    except Exception as exc:
        err = str(exc)

    if weather.get("summary") or weather.get("condition"):
        return make_widget(
            id="time_weather",
            title="Time & weather",
            owner="Journal",
            category="glance",
            priority=25,
            available=True,
            payload={"weather": weather},
            deep_links=[{"label": "Journal", "view": "journal"}],
            description="Local weather from Journal weather services.",
        )
    return make_widget(
        id="time_weather",
        title="Time & weather",
        owner="Journal",
        category="glance",
        priority=25,
        available=False,
        empty=True,
        coach="Weather unavailable — configure Journal weather or check network.",
        reason=err or "no_weather",
        payload={"weather": {"hint": "Weather unavailable"}},
        deep_links=[{"label": "Journal", "view": "journal"}],
    )


def _health_widget() -> dict[str, Any]:
    data: dict[str, Any] = {}
    err = None
    try:
        # Prefer existing health helpers without HTTP
        from jarvis.system_monitor import collect_stats

        stats = collect_stats() or {}
        models = (stats.get("ollama_models") or [])[:5]
        data = {
            "ollama_models": [m.get("name") or m.get("model") for m in models if isinstance(m, dict)],
            "cpu_percent": stats.get("cpu_percent"),
            "ram_percent": (stats.get("ram") or {}).get("percent"),
            "ready_hint": "open_mission_control",
        }
    except Exception as exc:
        err = str(exc)

    if data:
        return make_widget(
            id="provider_health",
            title="Provider health",
            owner="Mission Control",
            category="health",
            priority=30,
            available=True,
            payload=data,
            actions=[{"label": "Open Mission Control", "view": "workstation"}],
            deep_links=[{"label": "Mission Control", "view": "workstation"}],
            description="Summary only — Mission Control owns diagnostics.",
        )
    return make_widget(
        id="provider_health",
        title="Provider health",
        owner="Mission Control",
        category="health",
        priority=30,
        available=False,
        coach="Open Mission Control for provider diagnostics.",
        reason=err or "health_unavailable",
        deep_links=[{"label": "Mission Control", "view": "workstation"}],
    )


def _planner_widget() -> dict[str, Any]:
    snap, err = _safe("planner", lambda: __import__("jarvis.planner_store", fromlist=["planner_snapshot"]).planner_snapshot())
    if not snap or not snap.get("enabled"):
        return make_widget(
            id="today_glance",
            title="Today at a glance",
            owner="Planner",
            category="productivity",
            priority=35,
            available=False,
            coach="Planner is disabled or empty — enable Planner to see tasks and events.",
            reason=err or "planner_disabled",
            deep_links=[{"label": "Planner", "view": "planner"}],
        )
    tasks = [t for t in (snap.get("tasks") or []) if not t.get("completed")]
    events = snap.get("events_today") or []
    empty = not tasks and not events
    return make_widget(
        id="today_glance",
        title="Today at a glance",
        owner="Planner",
        category="productivity",
        priority=35,
        available=True,
        empty=empty,
        coach="No open tasks or events today — add one in Planner." if empty else "",
        payload={
            "active_tasks": len(tasks),
            "events_today": len(events),
            "task_preview": [t.get("text") for t in tasks[:3]],
            "event_preview": [e.get("title") for e in events[:3]],
        },
        deep_links=[{"label": "Planner", "view": "planner"}, {"label": "Calendar", "view": "calendar"}],
    )


def _calendar_widget() -> dict[str, Any]:
    from jarvis.calendar_bridges import dashboard_summary

    data, err = _safe("calendar", dashboard_summary)
    data = data or {}
    items = data.get("items") or []
    if err and not items and not data.get("ok"):
        return make_widget(
            id="calendar_summary",
            title="Calendar",
            owner="Calendar",
            category="productivity",
            priority=40,
            available=False,
            coach="Calendar feeds unavailable — open Calendar to configure ICS.",
            reason=err,
            deep_links=[{"label": "Calendar", "view": "calendar"}],
        )
    empty = len(items) == 0
    return make_widget(
        id="calendar_summary",
        title="Calendar",
        owner="Calendar",
        category="productivity",
        priority=40,
        available=True,
        empty=empty,
        coach="No calendar events today." if empty else "",
        payload={
            "count": data.get("count", len(items)),
            "items": [
                {"title": e.get("title"), "time": e.get("time"), "source": e.get("source")}
                for e in items[:5]
            ],
            "ics_status": data.get("ics_status"),
        },
        deep_links=[{"label": "Calendar", "view": "calendar"}],
    )


def _journal_widget(assistant: Any) -> dict[str, Any]:
    try:
        journal = getattr(assistant, "journal", None)
        if journal is None:
            from jarvis.modules.journal import Journal

            journal = Journal()
        from jarvis.modules.journal import _today

        page = journal.daily_get(_today())
        open_n = journal.stats().get("open_tasks", 0)
        prompts = page.get("prompts") or {}
        morning = (prompts.get("morning") or prompts.get("morning_question") or "").strip()
        empty = not morning and not open_n
        return make_widget(
            id="journal_reminder",
            title="Journal",
            owner="Journal",
            category="productivity",
            priority=45,
            available=True,
            empty=empty,
            coach="No journal prompt yet — open Journal to write today's note." if empty else "",
            payload={"open_tasks": open_n, "morning_prompt": morning[:200], "bullets": len(page.get("bullets") or [])},
            deep_links=[{"label": "Journal", "view": "journal"}],
        )
    except Exception as exc:
        return make_widget(
            id="journal_reminder",
            title="Journal",
            owner="Journal",
            category="productivity",
            priority=45,
            available=False,
            coach="Journal unavailable.",
            reason=str(exc),
            deep_links=[{"label": "Journal", "view": "journal"}],
        )


def _memory_widget(assistant: Any) -> dict[str, Any]:
    try:
        mem = getattr(assistant, "memory", None)
        if mem is None:
            return make_widget(
                id="memory_highlights",
                title="Memory",
                owner="Memory",
                category="ai",
                priority=50,
                available=False,
                coach="Memory store not ready.",
                deep_links=[{"label": "Memory", "view": "memory"}],
            )
        entries = []
        try:
            entries = list(mem.list_entries(namespace="profile") or [])[:3]
        except Exception:
            try:
                entries = list(mem.recent(limit=3) or [])  # type: ignore[attr-defined]
            except Exception:
                entries = []
        empty = not entries
        return make_widget(
            id="memory_highlights",
            title="Memory",
            owner="Memory",
            category="ai",
            priority=50,
            available=True,
            empty=empty,
            coach="No memory highlights yet." if empty else "",
            payload={
                "items": [
                    {"id": e.get("id"), "content": (e.get("content") or "")[:160]}
                    for e in entries
                    if isinstance(e, dict)
                ]
            },
            deep_links=[{"label": "Memory", "view": "memory"}],
        )
    except Exception as exc:
        return make_widget(
            id="memory_highlights",
            title="Memory",
            owner="Memory",
            category="ai",
            priority=50,
            available=False,
            coach="Memory unavailable.",
            reason=str(exc),
            deep_links=[{"label": "Memory", "view": "memory"}],
        )


def _projects_widget() -> dict[str, Any]:
    projects: list = []
    err = None
    try:
        from jarvis.project_services import suggest_projects

        sug = suggest_projects() or {}
        projects = sug.get("projects") or sug.get("items") or sug.get("suggestions") or []
        if isinstance(projects, dict):
            projects = list(projects.values())
    except Exception as exc1:
        err = str(exc1)
        try:
            from jarvis.projects_store import list_projects  # type: ignore

            projects = list_projects() or []
            err = None
        except Exception as exc2:
            err = str(exc2)
            projects = []
    if not isinstance(projects, list):
        projects = []
    # normalize dict-ish suggestions
    norm = []
    for p in projects[:8]:
        if isinstance(p, str):
            norm.append({"name": p, "slug": p})
        elif isinstance(p, dict):
            norm.append(p)
    projects = norm
    if err and not projects:
        return make_widget(
            id="projects",
            title="Projects",
            owner="Projects",
            category="productivity",
            priority=55,
            available=False,
            coach="No projects index — open Projects to create one.",
            reason=err,
            deep_links=[{"label": "Projects", "view": "projects"}],
        )
    empty = len(projects) == 0
    return make_widget(
        id="projects",
        title="Projects",
        owner="Projects",
        category="productivity",
        priority=55,
        available=True,
        empty=empty,
        coach="No active projects." if empty else "",
        payload={
            "count": len(projects),
            "items": [
                {"name": p.get("name") or p.get("slug") or p.get("title"), "slug": p.get("slug")}
                for p in projects[:5]
                if isinstance(p, dict)
            ],
        },
        deep_links=[{"label": "Projects", "view": "projects"}],
    )


def _scenes_widget() -> dict[str, Any]:
    try:
        from jarvis.scenes import list_presets  # type: ignore

        presets = list_presets() or []
    except Exception:
        try:
            import json
            from pathlib import Path

            from jarvis.config import DATA_DIR

            path = Path(DATA_DIR) / "scene_presets.json"
            if path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
                presets = data.get("presets") or data if isinstance(data, dict) else []
                if isinstance(presets, dict):
                    presets = [{"id": k, **v} if isinstance(v, dict) else {"id": k} for k, v in presets.items()]
            else:
                presets = []
        except Exception as exc:
            return make_widget(
                id="scenes",
                title="Home scenes",
                owner="Smart Home",
                category="home",
                priority=60,
                available=False,
                coach="No scene presets — open Smart Home setup.",
                reason=str(exc),
                deep_links=[{"label": "Smart Home setup", "action": "ha_setup"}],
            )

    empty = len(presets) == 0
    return make_widget(
        id="scenes",
        title="Home scenes",
        owner="Smart Home",
        category="home",
        priority=60,
        available=True,
        empty=empty,
        coach="No presets. Configure Home Assistant scene presets." if empty else "",
        payload={
            "presets": [
                {"id": p.get("id"), "label": p.get("label") or p.get("name") or p.get("id")}
                for p in presets[:8]
                if isinstance(p, dict)
            ]
        },
        actions=[{"label": "Activate", "type": "scene"}] if not empty else [],
        deep_links=[{"label": "Smart Home", "action": "ha_setup"}],
    )


def _news_widget(*, category: str = "") -> dict[str, Any]:
    try:
        from jarvis.curated_news import get_curated_headlines

        # Cache-first — never block Home on a cold news crawl
        data = get_curated_headlines(use_ai=False, category=category or "", force_refresh=False)
    except Exception as exc:
        return make_widget(
            id="news",
            title="News",
            owner="News",
            category="brief",
            priority=70,
            available=False,
            coach="News unavailable — use Daily Brief or ask Chat.",
            reason=str(exc),
            error=str(exc),
        )
    if not data.get("enabled"):
        return make_widget(
            id="news",
            title="News",
            owner="News",
            category="brief",
            priority=70,
            available=False,
            coach="Curated news is disabled.",
            payload=data,
        )
    headlines = data.get("headlines") or []
    empty = len(headlines) == 0
    return make_widget(
        id="news",
        title="News",
        owner="News",
        category="brief",
        priority=70,
        available=True,
        empty=empty,
        coach="No headlines yet — try Refresh or ask Aria for a news briefing." if empty else "",
        payload={
            "headlines": headlines[:8],
            "breaking": data.get("breaking"),
            "categories": data.get("categories") or [],
            "category": data.get("category") or "all",
            "fetched_at": data.get("fetched_at"),
        },
        deep_links=[{"label": "Daily Brief", "view": "dashboard", "widget": "daily_brief"}],
    )


def _suggestions_widget() -> dict[str, Any]:
    try:
        from jarvis.suggestions import get_suggestions  # type: ignore

        items = get_suggestions() or []
    except Exception:
        try:
            from jarvis.chat_suggestions import list_suggestions  # type: ignore

            items = list_suggestions() or []
        except Exception as exc:
            return make_widget(
                id="suggestions",
                title="Try asking Aria",
                owner="Chat",
                category="ai",
                priority=80,
                available=False,
                coach="Open Chat to talk with Aria.",
                reason=str(exc),
                deep_links=[{"label": "Chat", "view": "chat"}],
            )
    # normalize
    chips = []
    for s in items[:8]:
        if isinstance(s, str):
            chips.append(s)
        elif isinstance(s, dict):
            chips.append(s.get("text") or s.get("prompt") or s.get("label") or "")
    chips = [c for c in chips if c]
    empty = not chips
    return make_widget(
        id="suggestions",
        title="Try asking Aria",
        owner="Chat",
        category="ai",
        priority=80,
        available=True,
        empty=empty,
        coach="No suggestions yet — open Chat." if empty else "",
        payload={"suggestions": chips},
        deep_links=[{"label": "Chat", "view": "chat"}],
    )


def _attention_widget(attention: dict[str, Any]) -> dict[str, Any]:
    empty = bool(attention.get("empty"))
    return make_widget(
        id="attention",
        title="Attention",
        owner="Dashboard",
        category="attention",
        priority=5,
        available=True,
        empty=empty,
        coach="" if not empty else attention.get("message") or "Nothing urgent.",
        # Empty attention still shows as a calm status (coach/show ok)
        payload=attention,
        deep_links=[{"label": "Mission Control", "view": "workstation"}],
    )


def _brief_widget(brief: dict[str, Any]) -> dict[str, Any]:
    available = bool(brief.get("available"))
    empty = bool(brief.get("empty"))
    return make_widget(
        id="daily_brief",
        title="Daily Brief",
        owner="Morning Briefing",
        category="brief",
        priority=10,
        available=available,
        empty=empty or not available,
        coach=brief.get("coach") or "",
        error=brief.get("error") or "",
        payload=brief,
        deep_links=brief.get("deep_links") or [],
        description="One morning ritual — Morning Briefing owns source data.",
    )


def _launcher_widgets() -> list[dict[str, Any]]:
    return [
        make_widget(
            id="quick_launch",
            title="Quick launch",
            owner="Dashboard",
            category="launcher",
            priority=20,
            available=True,
            payload={"client_owned": True, "note": "Favorites and recents come from browser UI prefs."},
            deep_links=[{"label": "Home", "view": "dashboard"}],
        ),
        make_widget(
            id="resume",
            title="Resume",
            owner="Dashboard",
            category="launcher",
            priority=15,
            available=True,
            payload={"client_owned": True, "note": "Resume uses recent views and prompt history in the browser."},
            deep_links=[{"label": "Home", "view": "dashboard"}],
        ),
        make_widget(
            id="search_shortcuts",
            title="Search",
            owner="Search",
            category="launcher",
            priority=85,
            available=True,
            payload={"hint": "Open Search Home for federated find."},
            deep_links=[{"label": "Search", "view": "search"}],
            actions=[{"label": "Open Search", "view": "search"}],
        ),
        make_widget(
            id="notifications_summary",
            title="Notifications",
            owner="Notifications",
            category="attention",
            priority=12,
            available=True,
            payload=_notifications_payload(),
            deep_links=[{"label": "Open Notifications", "action": "open_notifications"}],
            actions=[{"label": "Open inbox", "action": "open_notifications"}],
            description="Unread and critical summary — Notifications owns the inbox.",
        ),
    ]


def _notifications_payload() -> dict[str, Any]:
    try:
        from jarvis.notifications_product.dashboard_bridge import dashboard_notifications_summary

        return dashboard_notifications_summary()
    except Exception as exc:
        return {"error": str(exc), "unread": 0, "critical": 0, "note": "Notifications summary unavailable"}



def build_home_aggregate(
    *,
    assistant: Any = None,
    news_category: str = "",
    use_cache_on_error: bool = True,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    greet = greeting_payload(assistant=assistant)
    attention = build_attention(assistant=assistant)
    brief = build_daily_brief(assistant=assistant)

    widgets: list[dict[str, Any]] = []
    widgets.append(_attention_widget(attention))
    widgets.append(_brief_widget(brief))
    widgets.extend(_launcher_widgets())

    tw = _weather_widget(assistant)
    # Merge clock into time_weather payload
    tw.setdefault("payload", {})["time_display"] = greet.get("time_display")
    tw["payload"]["date_label"] = greet.get("date_label")
    if tw.get("render") == "hide" or (not tw.get("available") and not tw.get("coach")):
        # Still show time even without weather
        tw["available"] = True
        tw["render"] = "show"
        tw["empty"] = False
        tw["status"] = "ready"
    widgets.append(tw)

    widgets.append(_health_widget())
    widgets.append(_planner_widget())
    widgets.append(_calendar_widget())
    widgets.append(_journal_widget(assistant))
    widgets.append(_memory_widget(assistant))
    widgets.append(_projects_widget())
    widgets.append(_scenes_widget())
    widgets.append(_news_widget(category=news_category))
    widgets.append(_suggestions_widget())

    layout = load_layout()
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    failures = [
        {"id": w["id"], "error": w.get("error") or w.get("reason"), "status": w.get("status")}
        for w in widgets
        if w.get("status") in ("error", "unavailable")
    ]
    available_n = sum(1 for w in widgets if w.get("available") and w.get("render") == "show")

    diagnostics = {
        "healthy": len([f for f in failures if f.get("status") == "error"]) == 0,
        "widget_count": len(widgets),
        "widgets_showing": available_n,
        "widget_failures": failures[:20],
        "latency_ms": latency_ms,
        "cache": {"last_good_written": True},
        "version": "1.0.0",
        "updated_label": "Updated just now",
        "generated_at": greet.get("iso"),
    }

    widgets.append(
        make_widget(
            id="diagnostics",
            title="Home diagnostics",
            owner="Dashboard",
            category="health",
            priority=95,
            available=True,
            payload=diagnostics,
            deep_links=[
                {"label": "API", "href": "/api/dashboard/home"},
                {"label": "Mission Control", "view": "workstation"},
            ],
        )
    )

    # Enforce honest render field
    for w in widgets:
        if w.get("status") == "empty" and w.get("id") == "attention":
            w["render"] = "show"  # calm clear state is useful
        elif w.get("error"):
            w["render"] = "coach" if w.get("coach") else "hide"
        elif not w.get("available"):
            w["render"] = "coach" if w.get("coach") else "hide"
        elif w.get("empty") and w.get("id") not in ("attention",):
            w["render"] = "coach" if w.get("coach") else "hide"

    payload = {
        "ok": True,
        "product": "Dashboard",
        "home": "Home",
        "generated_at": greet.get("iso"),
        "latency_ms": latency_ms,
        "greeting": greet,
        "attention": attention,
        "daily_brief": brief,
        "widgets": widgets,
        "layout": layout,
        "diagnostics": diagnostics,
        "deep_links": {
            "planner": "#planner",
            "calendar": "#calendar",
            "journal": "#journal",
            "mission_control": "#workstation",
            "search": "#search",
            "settings": "#settings",
            "chat": "#chat",
        },
        "kasa": {"count": 0, "note": "Device counts live on Smart Home — not duplicated here."},
        # Compat fields for older UI / PySide
        "welcome": greet.get("welcome"),
        "greeting_short": greet.get("greeting_short"),
        "date_label": greet.get("date_label"),
        "time_display": greet.get("time_display"),
        "weather": (tw.get("payload") or {}).get("weather") or {},
        "planner": {
            "enabled": True,
            "tasks": [],
            "events_today": [],
            **{
                k: (next((x for x in widgets if x["id"] == "today_glance"), {}).get("payload") or {}).get(k)
                for k in ()
            },
        },
        "intelligence": {
            "note": "Replaced by Attention + Daily Brief — no invented Live intelligence.",
            "daily_focus": (brief.get("preview") or "")[:200],
            "priority": (attention.get("items") or [{}])[0].get("title", "") if attention.get("items") else "",
            "intel_alert": "",
            "smart_home": "",
        },
        "news": (next((x for x in widgets if x["id"] == "news"), {}).get("payload") or {}),
    }

    # Attach planner counts into compat planner block
    glance = next((x for x in widgets if x["id"] == "today_glance"), {})
    gp = glance.get("payload") or {}
    payload["planner"] = {
        "enabled": glance.get("available", False),
        "active_tasks": gp.get("active_tasks", 0),
        "events_today_count": gp.get("events_today", 0),
        "task_preview": gp.get("task_preview") or [],
        "event_preview": gp.get("event_preview") or [],
        "tasks": [],
        "events_today": [],
    }

    try:
        save_last_good(payload)
    except Exception as exc:
        logger.debug("save_last_good: %s", exc)

    return payload
