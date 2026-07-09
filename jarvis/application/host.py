"""Aria application host — registers with AI Platform when attached."""

from __future__ import annotations

import logging
import os
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

logger = logging.getLogger("jarvis.application")

_ATTACHED = False


def create_host():
    return AriaApplicationHost()


class AriaApplicationHost:
    """Application contract for Aria on AI Platform."""

    def register(self):
        from aiplatform.applications.host import ApplicationRegistration

        return ApplicationRegistration(
            app_id="aria",
            install_path=str(PROJECT_ROOT),
            component_ids=["aria", "piper", "whisper", "comfyui", "homeassistant"],
            probe_ids=["aria", "opencode", "piper", "whisper"],
            acceptance_ids=["aria", "opencode", "claude_code"],
        )

    def attach(self) -> bool:
        global _ATTACHED
        try:
            from jarvis.application import registry as aria_registry

            aria_registry.register_with_platform()
            _ATTACHED = True
            return True
        except Exception as exc:
            logger.debug("Aria attach failed: %s", exc)
            return False

    def detach(self) -> bool:
        global _ATTACHED
        _ATTACHED = False
        return True

    def start(self) -> bool:
        from jarvis.services import ensure_services

        ensure_services(pull_models=False)
        return True

    def stop(self) -> bool:
        return True

    def health(self) -> bool:
        from jarvis.services import _jarvis_port_open

        return _jarvis_port_open()

    def capabilities(self):
        from aiplatform.applications.host import ApplicationCapabilities

        return ApplicationCapabilities(
            id="aria",
            label="Aria",
            version="3.1.0",
            namespaces=["aria", "profile", "default"],
            features=["chat", "voice", "vision", "engineering", "briefing"],
        )

    def dependencies(self) -> list[str]:
        return ["ollama"]

    def configuration(self) -> dict[str, Any]:
        return {
            "host": os.getenv("JARVIS_HOST", "127.0.0.1"),
            "port": os.getenv("JARVIS_PORT", "8765"),
            "install_path": str(PROJECT_ROOT),
        }


HOST = AriaApplicationHost()


def attach_if_present() -> bool:
    """Attach Aria extensions when AI Platform is available."""
    try:
        import aiplatform  # noqa: F401
    except ImportError:
        return False
    return HOST.attach()
