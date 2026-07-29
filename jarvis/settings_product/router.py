"""Deep-link router — resolve catalog entries to open payloads."""

from __future__ import annotations

from typing import Any

from jarvis.settings_product.catalog import build_catalog, search_catalog


def resolve_deep_link(pref_id: str = "", *, query: str = "") -> dict[str, Any]:
    entry = None
    if pref_id:
        for e in build_catalog():
            if e.get("id") == pref_id:
                entry = e
                break
    if not entry and query:
        hits = search_catalog(query, limit=1)
        entry = hits[0] if hits else None
    if not entry:
        return {
            "ok": False,
            "error": "preference not found",
            "open": {"view": "settings", "section": "all"},
        }
    open_payload = dict(entry.get("deep_link") or {})
    open_payload.setdefault("pref_id", entry.get("id"))
    open_payload.setdefault("category", entry.get("category"))
    return {
        "ok": True,
        "preference": entry,
        "open": open_payload,
        "message": f"Open {entry.get('title')} ({entry.get('owner')})",
    }


def list_deep_links() -> list[dict[str, Any]]:
    return [
        {
            "id": e["id"],
            "title": e["title"],
            "category": e["category"],
            "owner": e["owner"],
            "open": e.get("deep_link"),
        }
        for e in build_catalog()
    ]
