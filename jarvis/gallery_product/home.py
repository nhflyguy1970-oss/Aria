"""Gallery Home snapshot."""

from __future__ import annotations

from typing import Any

from jarvis.gallery_product.terminology import BOUNDARIES, TERMINOLOGY


def gallery_home_snapshot(assistant: Any | None = None) -> dict[str, Any]:
    from jarvis.config import is_uncensored
    from jarvis.gallery_product.collections import list_collections, list_favorites
    from jarvis.gallery_product.library import list_images
    from jarvis.gallery_product.soft_delete import list_trash
    from jarvis.media_jobs import busy_state

    recent = list_images(offset=0, limit=12, include_artifacts=False)
    try:
        busy = busy_state()
    except Exception:
        busy = {}
    return {
        "ok": True,
        "product": "gallery",
        "title": "Gallery",
        "philosophy": BOUNDARIES.get("philosophy"),
        "boundaries": BOUNDARIES,
        "terminology": TERMINOLOGY,
        "shortcut": "Ctrl+Shift+G",
        "viewer_uncensored": is_uncensored(),
        "library": {
            "total": recent.get("total"),
            "recent": recent.get("images") or [],
        },
        "favorites": (list_favorites().get("items") or [])[:12],
        "collections": (list_collections().get("items") or [])[:12],
        "trash": (list_trash(limit=8).get("items") or []),
        "jobs": busy,
        "sections": [
            {"id": "home", "label": "Overview"},
            {"id": "generate", "label": "Generation"},
            {"id": "library", "label": "Library"},
            {"id": "engine", "label": "Image Engine"},
            {"id": "editing", "label": "Editing"},
            {"id": "collections", "label": "Collections"},
            {"id": "trash", "label": "Trash"},
        ],
        "links": {
            "video": "video",
            "meme": "meme",
            "maker": "maker",
            "models": "models",
            "jobs": "jobs",
            "chat": "chat",
            "documents": "documents",
            "mission_control": "mission-control",
        },
    }
