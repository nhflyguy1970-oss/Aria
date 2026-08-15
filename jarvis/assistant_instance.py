"""Shared JarvisAssistant instance — server and MCP must use the same object.

C6: Never construct a second assistant in the daemon/MCP/scheduler.
When the serve process has not called set_assistant(), callers must fail
loudly (or use require_shared=False only in controlled tests).
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant

log = logging.getLogger("jarvis.assistant_instance")

_assistant: JarvisAssistant | None = None


def set_assistant(assistant: JarvisAssistant) -> None:
    global _assistant
    _assistant = assistant


def clear_assistant() -> None:
    """Test helper."""
    global _assistant
    _assistant = None


def has_shared_assistant() -> bool:
    return _assistant is not None


def get_assistant_or_none() -> JarvisAssistant | None:
    """Return the serve-registered assistant, or None (never constructs)."""
    return _assistant


def get_assistant(*, require_shared: bool | None = None) -> JarvisAssistant:
    """Return the process-global assistant registered by the serve process.

    By default refuses to construct a standalone instance (C6). Tests may
    pass require_shared=False or set JARVIS_ALLOW_STANDALONE_ASSISTANT=1.
    """
    global _assistant
    if _assistant is not None:
        return _assistant

    if require_shared is None:
        allow = os.getenv("JARVIS_ALLOW_STANDALONE_ASSISTANT", "").strip().lower() in (
            "1",
            "true",
            "yes",
        )
        # Pytest may construct assistants without a live serve process.
        in_test = bool(os.getenv("PYTEST_CURRENT_TEST"))
        require_shared = not (allow or in_test)

    if require_shared:
        raise RuntimeError(
            "No shared JarvisAssistant registered. Start the Aria serve process "
            "(python main.py serve / tray) before MCP, daemon job resume, or "
            "scheduler code that needs the live assistant. "
            "Refusing to create a divergent standalone instance (C6)."
        )

    log.warning(
        "Creating standalone JarvisAssistant (JARVIS_ALLOW_STANDALONE_ASSISTANT "
        "or require_shared=False) — state may diverge from a running server"
    )
    from jarvis.assistant import JarvisAssistant
    from jarvis.config import is_uncensored

    _assistant = JarvisAssistant(uncensored=is_uncensored())
    return _assistant
