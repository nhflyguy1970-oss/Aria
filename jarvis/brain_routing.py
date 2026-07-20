"""Fast vs deep chat model selection (thinking / nonthinking)."""

from __future__ import annotations

import os
import re

from jarvis.p1_flags import brain_routing_enabled

_DEEP_RE = re.compile(
    r"\b(why|explain|analyze|debug|fix|implement|refactor|prove|calculate|math|"
    r"code|algorithm|optimize|design|architect|compare|trade-?off|step by step)\b",
    re.I,
)


def needs_deep_thinking(message: str | None, *, action: str = "chat") -> bool:
    if not brain_routing_enabled():
        return False
    if action != "chat":
        return False
    text = (message or "").strip()
    if len(text) > 400:
        return True
    if _DEEP_RE.search(text):
        return True
    if text.count("?") >= 2:
        return True
    return False


def fast_chat_model() -> str:
    env = (os.getenv("JARVIS_FAST_MODEL") or "").strip()
    if env:
        return env
    from jarvis.model_store import model_for

    return model_for("fast_chat")


def reasoning_model() -> str:
    env = (os.getenv("JARVIS_REASONING_MODEL") or "").strip()
    if env:
        return env
    from jarvis.model_store import model_for

    return model_for("reasoning")


def select_chat_model(
    message: str | None,
    params: dict | None = None,
    *,
    action: str = "chat",
    voice: bool = False,
    session_chat_model: str = "",
) -> str:
    """Pick conversational model: explicit override → brain routing → conversation role."""
    params = params or {}
    explicit = (params.get("model") or session_chat_model or "").strip()
    if explicit:
        return explicit
    mode = (params.get("thinking_mode") or "").strip().lower()
    if mode == "deep" or needs_deep_thinking(message, action=action):
        return reasoning_model()
    if mode == "fast" or voice:
        return fast_chat_model()
    from jarvis.model_store import model_for

    return model_for("conversation")
