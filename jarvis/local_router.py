"""Fast local intent router via small Ollama model (FunctionGemma-style JSON)."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from jarvis.p1_flags import local_router_enabled
from jarvis.session import SessionContext

log = logging.getLogger("jarvis.router")

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 120.0

# High-value voice / planner / status routes the mini-router may return.
_ROUTER_ACTIONS = (
    "system_info",
    "morning_briefing",
    "planner_add_task",
    "planner_set_timer",
    "planner_set_alarm",
    "planner_today",
    "curated_briefing",
    "audio_stop",
    "audio_pause",
    "ha_control",
    "ha_status",
    "web_search",
    "weather_forecast",
    "chat",
    "thinking",
    "nonthinking",
)


def router_model() -> str:
    return (os.getenv("JARVIS_ROUTER_MODEL") or "qwen3:1.7b").strip()


def _system_prompt() -> str:
    actions = ", ".join(_ROUTER_ACTIONS)
    return (
        "You are a fast intent router. Reply with ONLY one JSON object, no markdown.\n"
        f'Keys: "action" (one of: {actions}), "params" (object), "thinking" (short string).\n'
        "Use thinking for math/coding/debug/reasoning; nonthinking for greetings/simple facts.\n"
        "Map timers/alarms/tasks/planner/status/weather/HA/web to the matching action.\n"
        'If unsure, use {"action":"chat","params":{},"thinking":"chat"}.'
    )


def _parse_json(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start:end])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "action" not in data:
        return None
    data.setdefault("params", {})
    data.setdefault("thinking", data.get("action", "routed"))
    return data


def try_local_route(message: str, session: SessionContext) -> dict[str, Any] | None:
    """Return intent dict or None to fall through to full router."""
    if not local_router_enabled():
        return None
    text = (message or "").strip()
    if not text or len(text) > 280 or text.count("\n") > 2:
        return None

    cache_key = text.lower()
    cached = _CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL:
        return dict(cached[1])

    try:
        from jarvis import llm

        t0 = time.perf_counter()
        raw = llm.ask_with_system(
            router_model(),
            _system_prompt(),
            text,
            options={"temperature": 0, "num_predict": 120},
        )[0]
        ms = int((time.perf_counter() - t0) * 1000)
        parsed = _parse_json(raw)
        if not parsed:
            return None
        action = str(parsed.get("action") or "chat")
        if action == "thinking":
            parsed = {"action": "chat", "params": {"thinking_mode": "deep"}, "thinking": "deep chat"}
        elif action == "nonthinking":
            parsed = {"action": "chat", "params": {"thinking_mode": "fast"}, "thinking": "fast chat"}
        elif action not in _ROUTER_ACTIONS and action != "chat":
            return None
        parsed["router_ms"] = ms
        parsed["router"] = "local"
        _CACHE[cache_key] = (time.time(), parsed)
        return parsed
    except Exception as exc:
        log.debug("local router skipped: %s", exc)
        return None


def router_status() -> dict[str, Any]:
    return {
        "enabled": local_router_enabled(),
        "model": router_model(),
        "cache_entries": len(_CACHE),
    }
