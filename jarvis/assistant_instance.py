"""Shared JarvisAssistant instance — server and MCP must use the same object."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant

log = logging.getLogger("jarvis.assistant_instance")

_assistant: JarvisAssistant | None = None


def set_assistant(assistant: JarvisAssistant) -> None:
    global _assistant
    _assistant = assistant


def get_assistant() -> JarvisAssistant:
    global _assistant
    if _assistant is None:
        log.warning(
            "No shared JarvisAssistant registered — creating standalone instance "
            "(MCP state may diverge from the running server)"
        )
        from jarvis.assistant import JarvisAssistant
        from jarvis.config import is_uncensored

        _assistant = JarvisAssistant(uncensored=is_uncensored())
    return _assistant


def clear_assistant() -> None:
    """Test helper."""
    global _assistant
    _assistant = None
