"""n8n workflow automation interface."""

from __future__ import annotations

import os
from typing import Any


def n8n_url() -> str:
    return os.getenv("JARVIS_N8N_URL", "http://127.0.0.1:5678").rstrip("/")


def status() -> dict[str, Any]:
    from jarvis.workstation.registry import component

    comp = component("n8n")
    if comp is None:
        return {"ok": False, "error": "n8n not registered"}
    return {"ok": comp.healthy(), "url": n8n_url(), "component": comp.to_dict()}


def start() -> dict[str, Any]:
    from jarvis.workstation.lifecycle import up

    return up("n8n")


def jarvis_webhook_base() -> str:
    """Base URL external automations should call."""
    port = os.getenv("JARVIS_PORT", "8765")
    host = os.getenv("JARVIS_HOST", "127.0.0.1")
    return f"http://{host}:{port}"
