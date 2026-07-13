"""Aria Core — Reasoning (delegates to jarvis.assistant / llm)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("reasoning")


def get_assistant() -> Any:
    """Return the live JarvisAssistant instance when available."""
    try:
        from jarvis.assistant_instance import get_assistant as _get

        return _get()
    except Exception:
        from jarvis import assistant as _assistant

        return getattr(_assistant, "JarvisAssistant", _assistant)


def chat(message: str, **kwargs: Any) -> Any:
    """Best-effort chat via existing assistant.process when present."""
    asst = get_assistant()
    if hasattr(asst, "process"):
        return asst.process(message, **kwargs)
    if callable(asst):
        return asst(message, **kwargs)
    raise RuntimeError("Aria Core reasoning: assistant process() unavailable")
