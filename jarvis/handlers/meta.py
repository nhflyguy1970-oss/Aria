"""Meta / info handlers (greeting, capabilities, clear, models)."""

from __future__ import annotations

import re

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
    lower = (message or "").lower().strip()
    # Explicit briefing requests still get the full morning briefing.
    if re.search(r"good (morning|afternoon|evening)\b", lower) and re.search(
        r"\b(briefing|brief|status|news|update|report)\b", lower
    ):
        from jarvis.handlers.registry import call_action

        return call_action(assistant, "morning_briefing", params, message)
    return ok(greeting_message(), module=None, type="info")


@register_action("clear", module="general", description="Clear active branch messages")
def clear(assistant, params: dict, message: str) -> dict:
    bid = assistant.branches.active_id or "main"
    return assistant.clear_branch_messages(bid)


@register_action("weather_forecast", module="general", description="Weather forecast")
def weather_forecast(assistant, params: dict, message: str) -> dict:
    from jarvis.journal_weather import parse_weather_day, weather_forecast_text

    day = (params.get("day") or "").strip() or parse_weather_day(message)
    return ok(
        weather_forecast_text(day, message=message),
        module="general",
        type="weather",
    )
