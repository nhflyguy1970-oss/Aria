"""Meta / info handlers (greeting, capabilities, clear, models)."""

from __future__ import annotations

from jarvis.capabilities import capabilities_message, greeting_message, models_guide
from jarvis.handlers.registry import register_action
from jarvis.response import ok


@register_action(
    "capabilities", info=True, module="general", description="List assistant capabilities"
)
def capabilities(assistant, params: dict, message: str) -> dict:
    return ok(capabilities_message(), module=None, type="info")


@register_action("models_info", info=True, module="general", description="Ollama model guide")
def models_info(assistant, params: dict, message: str) -> dict:
    msg = models_guide()
    status = assistant.get_status()
    if status.get("models_missing"):
        msg += "\n\n**Missing on your system:** " + ", ".join(
            f"`{m}`" for m in status["models_missing"]
        )
        msg += "\n\nRun `./scripts/pull-models.sh` to install recommended models."
    return ok(msg, module=None, type="info")


@register_action("greeting", info=True, module="general", description="Friendly hello")
def greeting(assistant, params: dict, message: str) -> dict:
    """Instant social hello — never invoke briefing/NLU/LLM for trivial greets."""
    return ok(greeting_message(), module=None, type="info")


@register_action("clear", module="general", description="Clear active branch messages")
def clear(assistant, params: dict, message: str) -> dict:
    bid = assistant.branches.active_id or "main"
    return assistant.clear_branch_messages(bid)


@register_action(
    "reflex_reply",
    info=True,
    module="general",
    description="Instant reflex acknowledgement / control reply",
)
def reflex_reply(assistant, params: dict, message: str) -> dict:
    text = (params or {}).get("reply") or "OK."
    return ok(str(text), module=None, type="info")


@register_action(
    "session_interrupt",
    info=True,
    module="general",
    description="Stop / cancel current conversational work",
)
def session_interrupt(assistant, params: dict, message: str) -> dict:
    try:
        if getattr(assistant, "session", None) is not None:
            assistant.session.pending_clarification = None
    except Exception:
        pass
    return ok((params or {}).get("reply") or "Stopped.", module=None, type="info")


@register_action(
    "session_continue",
    info=True,
    module="general",
    description="Continue after an interrupt",
)
def session_continue(assistant, params: dict, message: str) -> dict:
    return ok((params or {}).get("reply") or "Continuing.", module=None, type="info")


@register_action(
    "session_repeat",
    info=True,
    module="general",
    description="Repeat the last assistant reply",
)
def session_repeat(assistant, params: dict, message: str) -> dict:
    last = ""
    try:
        branch = getattr(assistant, "branches", None)
        if branch is not None:
            msgs = getattr(branch, "messages", None) or getattr(branch, "active_messages", None)
            if callable(msgs):
                msgs = msgs()
            if not msgs and hasattr(assistant, "session"):
                msgs = getattr(assistant.session, "messages", None) or []
            if isinstance(msgs, list):
                for m in reversed(msgs):
                    if isinstance(m, dict) and m.get("role") == "assistant" and m.get("content"):
                        last = str(m["content"])
                        break
    except Exception:
        last = ""
    if not last:
        return ok("Nothing to repeat yet.", module=None, type="info")
    return ok(last, module=None, type="info")


@register_action("weather_forecast", module="general", description="Weather forecast")
def weather_forecast(assistant, params: dict, message: str) -> dict:
    from jarvis.journal_weather import parse_weather_day, weather_forecast_text

    day = (params.get("day") or "").strip() or parse_weather_day(message)
    return ok(
        weather_forecast_text(day, message=message),
        module="general",
        type="weather",
    )
