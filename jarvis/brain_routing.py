"""Fast vs deep chat model selection (thinking / nonthinking)."""

from __future__ import annotations

import os
import re

from jarvis.p1_flags import brain_routing_enabled

_DEEP_RE = re.compile(
    r"\b(why|explain|analyze|debug|fix|implement|refactor|prove|calculate|math|"
    r"code|algorithm|optimize|design|architect|compare|trade-?off|step by step|"
    r"specs?|specifications?|cores?|threads?|clock|tdp|benchmark|ghz|ryzen|intel|amd)\b",
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


_CODE_OR_PLAN_RE = re.compile(
    r"\b(code|coding|debug(?:ging)?|bug|traceback|stack ?trace|exception|refactor|implement|function|"
    r"class|algorithm|compile|unit tests?|regex|sql|python|javascript|typescript|rust|bash|script|"
    r"plan|planning|roadmap|migration|architecture|architect|design doc|break (?:it|this) down)\b",
    re.I,
)
_HARD_RE = re.compile(
    r"\b(hard|complex|tricky|carefully|thorough(?:ly)?|in depth|deep dive|step[- ]by[- ]step plan|"
    r"multi[- ]step|end[- ]to[- ]end|race condition|deadlock|concurrency|use the specialist)\b",
    re.I,
)


def needs_specialist(message: str | None) -> bool:
    """Hard coding/planning work: escalate to the selectively invoked specialist."""
    text = (message or "").strip()
    if not text or not _CODE_OR_PLAN_RE.search(text):
        return False
    return bool(len(text) > 600 or "```" in text or "Traceback (most recent call last)" in text
                or text.count("\n") >= 8 or _HARD_RE.search(text))


def specialist_model(message: str | None) -> tuple[str, str]:
    """(model, note). Empty model = stay on the primary; the note says why."""
    from jarvis.model_store import explicit_saved_model

    model = (explicit_saved_model("specialist") or "").strip()
    if not model or not needs_specialist(message):
        return "", ""
    from jarvis import gpu_scheduler

    feasible, reason = gpu_scheduler.heavy_feasible(model)
    if not feasible:
        return "", f"specialist {model} skipped: {reason}"
    return model, f"hard coding/planning request → specialist {model}"


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
    if params is None:
        params = {}
    # The UI/session selection is owner intent; router params may contain defaults.
    explicit = (session_chat_model or params.get("model") or "").strip()
    if explicit:
        return explicit
    mode = (params.get("thinking_mode") or "").strip().lower()
    if action == "chat" and mode != "fast" and not voice:
        # Before knowledge mode: a hard coding/planning question is specialist work.
        special, note = specialist_model(message)
        if note:
            params["_specialist_note"] = note
        if special:
            return special
    if params.get("knowledge_mode"):
        return reasoning_model()
    if mode == "deep" or needs_deep_thinking(message, action=action):
        return reasoning_model()
    if mode == "fast" or voice:
        return fast_chat_model()
    from jarvis.model_store import model_for

    return model_for("conversation")
