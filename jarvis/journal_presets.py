"""Starter bullet journal collections — optional templates users can enable."""

from __future__ import annotations

PRESET_COLLECTIONS: list[dict[str, str]] = [
    {
        "id": "books",
        "name": "Books to Read",
        "description": "Reading list, quotes, and takeaways",
    },
    {
        "id": "movies",
        "name": "Movies & Shows",
        "description": "Watch list and short reviews",
    },
    {
        "id": "projects",
        "name": "Projects",
        "description": "Side projects and long-term goals",
    },
    {
        "id": "ideas",
        "name": "Ideas",
        "description": "Brainstorming and someday-maybe items",
    },
    {
        "id": "gratitude",
        "name": "Gratitude",
        "description": "Things you're thankful for",
    },
    {
        "id": "health",
        "name": "Health & Fitness",
        "description": "Workouts, habits, and wellness notes",
    },
    {
        "id": "shopping",
        "name": "Shopping List",
        "description": "Things to buy or pick up",
    },
    {
        "id": "recipes",
        "name": "Recipes",
        "description": "Meals to try and cooking notes",
    },
    {
        "id": "travel",
        "name": "Travel",
        "description": "Trips, places, and packing ideas",
    },
    {
        "id": "learning",
        "name": "Learning",
        "description": "Courses, skills, and study topics",
    },
]


def preset_by_id(preset_id: str) -> dict | None:
    pid = (preset_id or "").strip().lower()
    return next((p for p in PRESET_COLLECTIONS if p["id"] == pid), None)


def list_presets(existing_names: list[str] | None = None) -> list[dict]:
    existing = {n.lower() for n in (existing_names or [])}
    out = []
    for preset in PRESET_COLLECTIONS:
        out.append({
            **preset,
            "active": preset["name"].lower() in existing,
        })
    return out
