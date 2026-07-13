"""Aria Core — Interfaces (entrypoint pointers only)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("interfaces")


def describe_interfaces() -> dict[str, Any]:
    """Describe interface surfaces without starting servers."""
    return {
        "chat_gui": {
            "implementation": "jarvis.gui.server",
            "default_port": 8765,
            "role": "Primary Aria conversation UI",
        },
        "tray_daemon": {
            "implementation": "jarvis.daemon / jarvis.tray",
            "role": "Background Aria process + tray",
        },
        "cli": {
            "implementation": "jarvis.application.cli / ./aria",
            "role": "Standalone Aria lifecycle CLI",
        },
        "rest_api": {
            "implementation": "jarvis.gui.server /api/*",
            "role": "HTTP/WS API",
        },
        "mission_control": {
            "implementation": "aiplatform.mission_control",
            "default_port": 8780,
            "role": "Operational cockpit (not cognition)",
        },
        "mcp": {
            "implementation": "scripts/jarvis-mcp-server.py",
            "role": "Cursor MCP tools",
        },
        "owner": OWNER["owner"],
    }
