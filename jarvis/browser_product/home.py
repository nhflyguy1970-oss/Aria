"""Browser Home snapshot."""

from __future__ import annotations

from typing import Any

from jarvis.browser_product.terminology import BOUNDARIES, TERMINOLOGY


def browser_home_snapshot(assistant: Any | None = None) -> dict[str, Any]:
    from jarvis.browser_agent import status
    from jarvis.browser_product.activity_bridge import recent_events
    from jarvis.browser_product.downloads import list_downloads
    from jarvis.browser_product.history import list_bookmarks, list_history, list_notes
    from jarvis.browser_product.session import profile_dir, session_info

    st = status()
    info = session_info()
    hist = list_history(limit=12)
    books = list_bookmarks(limit=12)
    downloads = list_downloads(limit=12)
    notes = list_notes(limit=12)
    return {
        "ok": True,
        "product": "browser",
        "title": "Browser",
        "philosophy": BOUNDARIES.get("philosophy"),
        "boundaries": BOUNDARIES,
        "terminology": TERMINOLOGY,
        "shortcut": "Ctrl+Shift+B",
        "status": st,
        "session": info,
        "profile_dir": str(profile_dir()),
        "history": hist.get("items") or [],
        "bookmarks": books.get("items") or [],
        "downloads": downloads.get("items") or [],
        "notes": notes.get("items") or [],
        "activity": recent_events(limit=12),
        "security": {
            "ssrf_guard": True,
            "checkout_heuristics": True,
            "downloads_gated": True,
            "download_dir": downloads.get("dir"),
        },
        "modes": st.get("modes_available") or {},
        "quick_actions": [
            {"id": "navigate", "label": "Open URL"},
            {"id": "screenshot", "label": "Screenshot"},
            {"id": "run_dom", "label": "Run DOM task"},
            {"id": "save_docs", "label": "Save page to Documents"},
            {"id": "pause", "label": "Pause"},
            {"id": "takeover", "label": "Takeover"},
        ],
        "links": {
            "projects": "projects",
            "documents": "documents",
            "memory": "memory",
            "chat": "chat",
            "jobs": "jobs",
            "activity": "activity",
            "models": "models",
            "coding": "coding",
        },
    }
