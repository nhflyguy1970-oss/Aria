"""Managed alternate interfaces — Open WebUI."""

from __future__ import annotations

import os
from typing import Any


def openwebui_url() -> str:
    return os.getenv("JARVIS_OPENWEBUI_URL", "http://127.0.0.1:3000").rstrip("/")


def status() -> dict[str, Any]:
    from jarvis.workstation.registry import component

    comp = component("open_webui")
    if comp is None:
        return {"ok": False, "error": "open_webui not registered"}
    return {"ok": comp.healthy(), "url": openwebui_url(), "component": comp.to_dict()}


def start() -> dict[str, Any]:
    from jarvis.workstation.lifecycle import up

    return up("open_webui")


def inference_url() -> str:
    """URL coding tools and Open WebUI should use for models."""
    litellm = os.getenv("JARVIS_LITELLM_URL", "http://127.0.0.1:4000").rstrip("/")
    ollama = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    try:
        from jarvis.inference.gateway import litellm_available

        if litellm_available():
            return f"{litellm}/v1"
    except Exception:
        pass
    return f"{ollama}/v1"
