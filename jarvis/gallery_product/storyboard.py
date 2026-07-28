"""Suggest storyboard order for Video Studio — never auto-create video."""

from __future__ import annotations

from typing import Any

from jarvis.gallery_product.metadata import get_meta


def suggest_storyboard_order(names: list[str]) -> dict[str, Any]:
    """Order by creation/mtime metadata then prompt similarity — suggestion only."""
    scored = []
    for name in names or []:
        meta = get_meta(name)
        scored.append(
            {
                "name": name,
                "ts": float(meta.get("created_at") or meta.get("updated_at") or 0),
                "prompt": (meta.get("prompt") or "")[:80],
            }
        )
    scored.sort(key=lambda x: x["ts"])
    ordered = [s["name"] for s in scored] or list(names or [])
    return {
        "ok": True,
        "suggested_order": ordered,
        "paths_csv": ",".join(ordered),
        "auto_create_video": False,
        "message": "Suggestion only — open Video Studio to create a storyboard clip",
    }
