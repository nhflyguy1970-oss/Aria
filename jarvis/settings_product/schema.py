"""Shared Preference schema — catalog entries only; products own values."""

from __future__ import annotations

from typing import Any

REQUIRED_FIELDS = (
    "id",
    "title",
    "description",
    "category",
    "owner",
    "type",
    "default",
    "deep_link",
    "aliases",
)


def make_preference(
    *,
    id: str,
    title: str,
    description: str,
    category: str,
    owner: str,
    type: str = "link",
    default: Any = None,
    validation: dict[str, Any] | None = None,
    deep_link: dict[str, Any] | None = None,
    aliases: list[str] | None = None,
    keywords: str = "",
    editable_in_settings: bool = False,
    sensitive: bool = False,
) -> dict[str, Any]:
    """Normalize a catalog preference entry."""
    return {
        "id": id,
        "title": title,
        "description": description,
        "category": category,
        "owner": owner,
        "type": type,  # link | toggle | select | text | action
        "default": default,
        "validation": dict(validation or {}),
        "deep_link": dict(deep_link or {"view": "settings", "section": category}),
        "aliases": list(aliases or []),
        "keywords": keywords,
        "editable_in_settings": bool(editable_in_settings),
        "sensitive": bool(sensitive),
    }


def validate_preference(entry: dict[str, Any]) -> bool:
    return isinstance(entry, dict) and all(k in entry for k in REQUIRED_FIELDS)
