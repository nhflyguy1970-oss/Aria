"""Journal REST API routes (GUI bullet journal panel)."""

from __future__ import annotations


def register_routes(app, assistant) -> None:
    """Journal HTTP routes are registered in jarvis.gui.extra_routes."""
    del app, assistant
