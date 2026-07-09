"""High-confidence utterance hints for the local intent router (P1 #23)."""

from __future__ import annotations

import re
from typing import Any

_DURATION_RE = re.compile(
    r"(?P<n>\d+)\s*(?P<unit>minutes?|mins?|hours?|hrs?|seconds?|secs?)",
    re.I,
)
_ALARM_TIME_RE = re.compile(
    r"(?:at|for)\s+(?P<time>\d{1,2}(?::\d{2})?\s*(?:am|pm)?(?:\s+tomorrow)?)",
    re.I,
)
_TASK_RE = re.compile(r"^(?:add(?:\s+a)?\s+)?task\s+(.+)$", re.I)

_ITERATE_CAD_PATTERNS = (
    r"^(?:modify|change|iterate|edit|update)\s+(?:the\s+)?(?:cad|design|model|part|stl)\s*(?::|to)?\s*(.+)$",
    r"^(?:make it|make the)\s+((?:taller|shorter|wider|thinner|thicker|bigger|smaller)\b.*)$",
)

_GENERATE_CAD_PATTERNS = (
    r"^(?:design|generate|create|make)\s+(?:a\s+)?(?:cad\s+)?(?:stl\s+)?(?:for\s+)?(.+)$",
    r"^(?:design|generate|create)\s+(?:a\s+)?(?:3d\s+)?(?:part|model)\s+(?:for\s+)?(.+)$",
    r"^generate\s+cad\s+(?:for\s+)?(.+)$",
)


def try_hint_route(message: str | None) -> dict[str, Any] | None:
    """Fast regex router for common voice phrases (~0ms). Returns intent dict or None."""
    if not message:
        return None
    text = message.strip()
    if not text or len(text) > 280:
        return None
    lower = text.lower()

    if re.search(r"\b(stop|halt)\b.+\b(audio|playback|music|speaking)\b", lower) or lower in (
        "stop",
        "stop audio",
        "stop playback",
        "stop speaking",
    ):
        return _hit("audio_stop")

    if re.search(r"\b(pause|hold)\b.+\b(audio|playback|music)\b", lower) or lower in (
        "pause",
        "pause audio",
        "pause playback",
    ):
        return _hit("audio_pause")

    if re.search(r"\b(good morning|morning briefing)\b", lower):
        return _hit("morning_briefing")

    if re.search(r"\bwhat am i working on\b", lower):
        return _hit("what_am_i_working_on")

    if re.search(r"\bwhat changed since yesterday\b", lower):
        return _hit("what_changed_since_yesterday")

    if re.search(r"\banything broken\b|\bwhat(?:'s| is) broken\b", lower):
        return _hit("anything_broken")

    if re.search(r"\brepositories? need attention\b|\bany repos?\b", lower):
        return _hit("repos_need_attention")

    if re.search(r"\bovernight (?:summary|activity|report)\b", lower):
        return _hit("overnight_summary")

    if re.search(r"\bwhat should i work on next\b|\bwhat(?:'s| is) next\b", lower):
        return _hit("what_should_i_work_on_next")

    if re.search(r"\breview (?:my )?(?:current )?branch\b", lower):
        return _hit("review_current_branch")

    if re.search(r"\btoday(?:'s)? (?:ai )?recommendations\b", lower):
        return _hit("today_recommendations")

    if re.search(r"\b(situational briefing|what(?:'s| is) my status|status briefing)\b", lower):
        return _hit("situational_briefing")

    if re.search(r"\b(news briefing|curated news|headlines|tech news)\b", lower):
        return _hit("curated_briefing")

    if re.search(r"\b(system status|system info|gpu status|what(?:'s| is) running)\b", lower):
        return _hit("system_info")

    if re.search(
        r"\b(planner today|today(?:'s)? schedule|what(?:'s| is) on my (?:planner|calendar) today)\b",
        lower,
    ):
        return _hit("planner_today")

    if re.search(r"\b(smart home|home assistant)\b.+\bstatus\b", lower) or lower in (
        "home status",
        "smart home status",
    ):
        return _hit("ha_status")

    if re.search(r"\bweather\b", lower) or re.search(r"forecast (?:for|in)\b", lower):
        loc = _extract_location(text)
        params = {"location": loc} if loc else {}
        return _hit("weather_forecast", params)

    if re.search(r"\b(search (?:the )?web|search for|look up|google)\b", lower):
        query = re.sub(
            r"^(?:please\s+)?(?:search(?:\s+the\s+web)?\s+for|search for|look up|google)\s+",
            "",
            text,
            flags=re.I,
        ).strip()
        return _hit("web_search", {"query": query or text})

    if _looks_like_timer(lower):
        duration = _extract_duration(text) or _extract_duration(lower)
        params: dict[str, str] = {}
        if duration:
            params["duration"] = duration
        return _hit("planner_set_timer", params)

    if re.search(r"\b(alarm|wake me)\b", lower):
        params = {}
        match = _ALARM_TIME_RE.search(text) or _ALARM_TIME_RE.search(lower)
        if match:
            params["time"] = match.group("time").strip()
        return _hit("planner_set_alarm", params)

    match = _TASK_RE.match(text)
    if match:
        return _hit("planner_add_task", {"text": match.group(1).strip()})

    if re.search(r"\bturn (?:on|off|toggle)\b", lower) or re.search(r"\b(dim|brighten)\b", lower):
        params = _parse_ha_control(text, lower)
        if params:
            return _hit("ha_control", params)

    cad_iterate = _parse_iterate_cad(text, lower)
    if cad_iterate:
        return _hit("iterate_cad", cad_iterate)

    cad_new = _parse_generate_cad(text, lower)
    if cad_new:
        return _hit("generate_cad", cad_new)

    if lower in ("hello", "hi", "hey", "thanks", "thank you"):
        return _hit("chat")

    if re.search(r"\b(explain|why does|step by step|prove that|debug)\b", lower):
        return {
            "action": "chat",
            "params": {"thinking_mode": "deep"},
            "thinking": "hint:deep",
            "router": "hint",
        }

    return None


def _hit(action: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "action": action,
        "params": dict(params or {}),
        "thinking": f"hint:{action}",
        "router": "hint",
        "router_ms": 0,
    }


def _looks_like_timer(lower: str) -> bool:
    if re.search(r"\b(timer|countdown)\b", lower):
        return True
    if re.search(r"\bset (?:a )?timer\b", lower):
        return True
    if re.search(r"\btimer for\b", lower):
        return True
    if re.search(r"\bfor \d+\s*(?:minutes?|mins?|hours?|secs?)\b", lower) and "alarm" not in lower:
        return True
    return False


def _extract_duration(text: str) -> str | None:
    match = _DURATION_RE.search(text)
    if not match:
        return None
    unit = match.group("unit").lower()
    if unit.startswith("min"):
        unit = "minutes"
    elif unit.startswith("hour") or unit == "hr":
        unit = "hours"
    elif unit.startswith("sec"):
        unit = "seconds"
    return f"{match.group('n')} {unit}"


def _extract_location(text: str) -> str | None:
    match = re.search(r"(?:weather|forecast)\s+(?:for|in)\s+(.+?)(?:\?|$)", text, re.I)
    if match:
        return match.group(1).strip(" ?.")
    return None


def _parse_ha_control(text: str, lower: str) -> dict[str, str] | None:
    action = "toggle"
    if re.search(r"\bturn on\b", lower) or re.search(r"\bturn on the\b", lower):
        action = "on"
    elif re.search(r"\bturn off\b", lower):
        action = "off"
    elif re.search(r"\bdim\b", lower):
        action = "on"
    target = ""
    match = re.search(r"\bturn (?:on|off|toggle)\s+(?:the\s+)?(.+)$", text, re.I)
    if match:
        target = match.group(1).strip(" .?!")
    if not target:
        match = re.search(r"\b(?:dim|brighten)\s+(?:the\s+)?(.+)$", text, re.I)
        if match:
            target = match.group(1).strip(" .?!")
    if not target:
        return None
    return {"target": target, "action": action}


def _parse_iterate_cad(text: str, lower: str) -> dict[str, str] | None:
    if re.search(
        r"\b(make it|make the)\s+(taller|shorter|wider|thinner|thicker|bigger|smaller)\b", lower
    ):
        match = re.search(
            r"\b(make it|make the)\s+((?:taller|shorter|wider|thinner|thicker|bigger|smaller)\b.*)$",
            text,
            re.I,
        )
        prompt = match.group(0).strip(" .?!") if match else text.strip(" .?!")
        return {"prompt": prompt, "edit": "true"}

    for pattern in _ITERATE_CAD_PATTERNS:
        match = re.match(pattern, text, re.I)
        if match:
            return {"prompt": match.group(1).strip(" .?!"), "edit": "true"}

    if re.search(r"\b(iterate|modify)\b.+\b(design|cad|model|part)\b", lower):
        return {"prompt": text.strip(" .?!"), "edit": "true"}

    return None


def _parse_generate_cad(text: str, lower: str) -> dict[str, str] | None:
    if re.search(r"\b(iterate|modify|edit|update|make it)\b", lower) and re.search(
        r"\b(taller|thicker|thinner|wider|shorter|bigger|smaller)\b",
        lower,
    ):
        return None

    for pattern in _GENERATE_CAD_PATTERNS:
        match = re.match(pattern, text, re.I)
        if match:
            return {"prompt": match.group(1).strip(" .?!")}

    if re.search(r"\b(design|generate|create)\b.+\b(cad|stl|adapter|bracket|part)\b", lower):
        return {"prompt": text.strip(" .?!")}

    return None


def contradicts_hint(message: str | None, action: str) -> bool:
    """True when a model route likely conflicts with obvious utterance intent."""
    if not message:
        return False
    lower = message.lower()

    if action == "morning_briefing" and _looks_like_timer(lower):
        return True
    if (
        action == "planner_set_alarm"
        and _looks_like_timer(lower)
        and "alarm" not in lower
        and "wake" not in lower
    ):
        return True
    if action == "morning_briefing" and re.search(r"\bturn (?:on|off)\b", lower):
        return True
    if action == "planner_set_timer" and re.search(r"\bgood morning\b", lower):
        return True
    if action == "generate_cad" and _parse_iterate_cad(message, lower):
        return True
    if action == "chat" and _parse_iterate_cad(message, lower):
        return True
    if action in (
        "planner_set_alarm",
        "planner_set_timer",
        "morning_briefing",
        "chat",
    ) and re.search(
        r"\bturn (?:on|off|toggle)\b",
        lower,
    ):
        return True
    if action == "planner_set_alarm" and re.search(r"\b(?:lights?|lamp|room)\b", lower):
        return True
    if action == "briefing_news_detail":
        from jarvis.briefing_news import looks_like_general_expansion

        if looks_like_general_expansion(message):
            return True
    return False
