"""Shared widget schema — honest availability, never fake data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def make_widget(
    *,
    id: str,
    title: str,
    owner: str,
    category: str,
    priority: int = 50,
    available: bool = True,
    health: str = "ok",
    reason: str = "",
    coach: str = "",
    payload: dict[str, Any] | None = None,
    actions: list[dict[str, Any]] | None = None,
    deep_links: list[dict[str, Any]] | None = None,
    empty: bool = False,
    error: str = "",
    loading: bool = False,
    refreshed_at: str | None = None,
    aliases: list[str] | None = None,
    description: str = "",
) -> dict[str, Any]:
    """Build one widget contract. Hide or coach when unavailable/empty."""
    status = "ready"
    if loading:
        status = "loading"
    elif error:
        status = "error"
        health = "error"
    elif not available:
        status = "unavailable"
    elif empty:
        status = "empty"

    return {
        "id": id,
        "title": title,
        "description": description,
        "owner": owner,
        "category": category,
        "priority": int(priority),
        "health": health,
        "available": bool(available),
        "status": status,
        "reason": reason,
        "coach": coach,
        "empty": bool(empty),
        "error": error or None,
        "loading": bool(loading),
        "payload": payload or {},
        "actions": actions or [],
        "deep_links": deep_links or [],
        "refreshed_at": refreshed_at or _now_iso(),
        "aliases": aliases or [],
        # Presentation hint — UI must hide or coach, never invent content
        "render": "show" if available and not empty and not error else ("coach" if coach else "hide"),
    }


def validate_widget(w: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("id", "title", "owner", "category"):
        if not w.get(key):
            errors.append(f"missing_{key}")
    if w.get("render") not in ("show", "hide", "coach"):
        errors.append("invalid_render")
    if w.get("available") and w.get("empty") and w.get("render") == "show":
        errors.append("empty_shown_without_coach")
    return errors
