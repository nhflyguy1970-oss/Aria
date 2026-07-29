"""Dashboard/Home bridge — summary only; Dashboard never owns notifications."""

from __future__ import annotations

from typing import Any


def dashboard_notifications_summary() -> dict[str, Any]:
    from jarvis.notifications_product.digest import build_digest
    from jarvis.notifications_product.pipeline import unread_summary
    from jarvis.notifications_product.preferences import load_preferences

    summary = unread_summary()
    digest = build_digest("needs_attention")
    prefs = load_preferences()
    return {
        "product": "Notifications",
        "owner": "Notifications",
        "enabled": bool(prefs.get("enabled")),
        "unread": summary.get("unread") or 0,
        "critical": summary.get("critical") or 0,
        "digest_title": digest.get("title"),
        "digest_summary": digest.get("summary"),
        "digest_count": digest.get("count") or 0,
        "deep_links": [
            {"label": "Open Notifications", "action": "open_notifications"},
            {"label": "Needs attention", "action": "open_notifications", "filter": "unread"},
        ],
        "note": "Home displays a summary. Notifications owns the inbox.",
    }
