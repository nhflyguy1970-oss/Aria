"""Widget catalog — products own data; Dashboard indexes presentation."""

from __future__ import annotations

from typing import Any

WIDGET_DEFS: list[dict[str, Any]] = [
    {
        "id": "attention",
        "title": "Attention",
        "owner": "Dashboard",
        "category": "attention",
        "priority": 5,
        "description": "Running/failed jobs, overdue tasks, provider issues, upcoming meetings.",
        "aliases": ["alerts", "priority", "up next"],
        "deep_link": {"view": "dashboard", "widget": "attention"},
    },
    {
        "id": "daily_brief",
        "title": "Daily Brief",
        "owner": "Morning Briefing",
        "category": "brief",
        "priority": 10,
        "description": "One morning ritual card — indexes Morning Briefing, Planner, Calendar.",
        "aliases": ["briefing", "morning", "today"],
        "deep_link": {"view": "dashboard", "widget": "daily_brief"},
    },
    {
        "id": "resume",
        "title": "Resume",
        "owner": "Dashboard",
        "category": "launcher",
        "priority": 15,
        "description": "Continue last view / project / prompt with grounded suggestions.",
        "aliases": ["continue", "welcome", "smart welcome"],
        "deep_link": {"view": "dashboard", "widget": "resume"},
    },
    {
        "id": "quick_launch",
        "title": "Quick launch",
        "owner": "Dashboard",
        "category": "launcher",
        "priority": 20,
        "description": "Favorites and recent views.",
        "aliases": ["favorites", "launcher"],
        "deep_link": {"view": "dashboard", "widget": "quick_launch"},
    },
    {
        "id": "time_weather",
        "title": "Time & weather",
        "owner": "Journal",
        "category": "glance",
        "priority": 25,
        "description": "Local time and weather from Journal/weather services.",
        "aliases": ["clock", "weather"],
        "deep_link": {"view": "dashboard", "widget": "time_weather"},
    },
    {
        "id": "provider_health",
        "title": "Provider health",
        "owner": "Mission Control",
        "category": "health",
        "priority": 30,
        "description": "Lightweight provider summary — Mission Control owns detail.",
        "aliases": ["ollama", "health", "providers"],
        "deep_link": {"view": "workstation"},
    },
    {
        "id": "today_glance",
        "title": "Today at a glance",
        "owner": "Planner",
        "category": "productivity",
        "priority": 35,
        "description": "Active tasks and today's events — Planner owns the store.",
        "aliases": ["tasks", "events", "stats"],
        "deep_link": {"view": "planner"},
    },
    {
        "id": "calendar_summary",
        "title": "Calendar",
        "owner": "Calendar",
        "category": "productivity",
        "priority": 40,
        "description": "Upcoming calendar events.",
        "aliases": ["meetings", "schedule"],
        "deep_link": {"view": "calendar"},
    },
    {
        "id": "journal_reminder",
        "title": "Journal",
        "owner": "Journal",
        "category": "productivity",
        "priority": 45,
        "description": "Today's journal prompt or open-task reminder.",
        "aliases": ["bullet journal", "notes"],
        "deep_link": {"view": "journal"},
    },
    {
        "id": "memory_highlights",
        "title": "Memory",
        "owner": "Memory",
        "category": "ai",
        "priority": 50,
        "description": "High-signal memory highlights — Memory owns the store.",
        "aliases": ["recalls", "acm"],
        "deep_link": {"view": "memory"},
    },
    {
        "id": "projects",
        "title": "Projects",
        "owner": "Projects",
        "category": "productivity",
        "priority": 55,
        "description": "Active projects chip.",
        "aliases": ["coding projects"],
        "deep_link": {"view": "projects"},
    },
    {
        "id": "scenes",
        "title": "Home scenes",
        "owner": "Smart Home",
        "category": "home",
        "priority": 60,
        "description": "Activate scene presets — Smart Home owns devices.",
        "aliases": ["scenes", "kasa", "home assistant"],
        "deep_link": {"view": "dashboard", "widget": "scenes"},
    },
    {
        "id": "news",
        "title": "News",
        "owner": "News",
        "category": "brief",
        "priority": 70,
        "description": "Curated headlines (optional). Prefer Daily Brief for morning ritual.",
        "aliases": ["headlines", "breaking"],
        "deep_link": {"view": "dashboard", "widget": "news"},
    },
    {
        "id": "suggestions",
        "title": "Try asking Aria",
        "owner": "Chat",
        "category": "ai",
        "priority": 80,
        "description": "Grounded suggestion chips → Chat.",
        "aliases": ["prompts", "suggestions"],
        "deep_link": {"view": "chat"},
    },
    {
        "id": "search_shortcuts",
        "title": "Search",
        "owner": "Search",
        "category": "launcher",
        "priority": 85,
        "description": "Open Search Home — Search owns retrieval.",
        "aliases": ["find", "federated"],
        "deep_link": {"view": "search"},
    },
    {
        "id": "diagnostics",
        "title": "Home diagnostics",
        "owner": "Dashboard",
        "category": "health",
        "priority": 95,
        "description": "Aggregate health, cache, widget failures, latency.",
        "aliases": ["diagnostics", "health home"],
        "deep_link": {"view": "dashboard", "widget": "diagnostics"},
    },
]


def list_widget_defs() -> list[dict[str, Any]]:
    return [dict(w) for w in WIDGET_DEFS]


def widget_def(widget_id: str) -> dict[str, Any] | None:
    for w in WIDGET_DEFS:
        if w["id"] == widget_id:
            return dict(w)
    return None


def search_widgets(query: str, *, limit: int = 24) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    if not q:
        return list_widget_defs()[:limit]
    scored: list[tuple[int, dict[str, Any]]] = []
    for w in WIDGET_DEFS:
        blob = " ".join(
            [
                w.get("id", ""),
                w.get("title", ""),
                w.get("description", ""),
                w.get("owner", ""),
                w.get("category", ""),
                " ".join(w.get("aliases") or []),
            ]
        ).lower()
        score = 0
        if q in blob:
            score += 10
        for token in q.split():
            if token in blob:
                score += 3
        if score:
            scored.append((score, w))
    scored.sort(key=lambda x: (-x[0], x[1].get("priority", 99)))
    return [dict(w) for _, w in scored[:limit]]
