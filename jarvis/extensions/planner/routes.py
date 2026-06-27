"""Fast-path routes for planner and system info."""

from __future__ import annotations

import re

from jarvis.router_table import RouteRule


def planner_routes():
    return [
        RouteRule(
            "system_info",
            9,
            "system status",
            lambda m, lower, _s: bool(
                re.search(r"\b(system status|what'?s my status|what do i have|what's going on|status snapshot)\b", lower)
            ),
        ),
        RouteRule(
            "planner_set_timer",
            15,
            "set timer",
            lambda m, lower, _s: bool(re.search(r"\b(set|start)\s+(a\s+)?timer\b", lower)),
            lambda m: {"duration": re.sub(r".*timer\s+(?:for\s+)?", "", m, flags=re.I).strip()},
        ),
        RouteRule(
            "planner_set_alarm",
            15,
            "set alarm",
            lambda m, lower, _s: bool(re.search(r"\b(set|create)\s+(an\s+)?alarm\b", lower)),
            lambda m: {"time": re.sub(r".*alarm\s+(?:for\s+)?(?:at\s+)?", "", m, flags=re.I).strip()},
        ),
        RouteRule(
            "planner_add_task",
            16,
            "add task",
            lambda m, lower, _s: bool(
                re.search(r"\b(add|create)\s+.+?\s+to\s+(my\s+)?(to-?do|task) list\b", lower)
                or re.search(r"\badd\s+(buy|task)\b", lower)
            ),
            lambda m: {"text": re.sub(r".*add\s+", "", m, flags=re.I).strip()},
        ),
        RouteRule(
            "planner_today",
            17,
            "schedule today",
            lambda m, lower, _s: bool(
                re.search(r"\b(what'?s on my schedule|my schedule today|planner today)\b", lower)
            ),
        ),
        RouteRule(
            "curated_briefing",
            18,
            "curated news",
            lambda m, lower, _s: bool(re.search(r"\b(curated (news|briefing)|tech headlines)\b", lower)),
        ),
        RouteRule(
            "audio_stop",
            6,
            "stop audio",
            lambda m, lower, _s: bool(re.search(r"\b(stop (speaking|audio|playback)|pause audio)\b", lower)),
        ),
        RouteRule(
            "audio_pause",
            6,
            "pause audio",
            lambda m, lower, _s: bool(re.search(r"\b(pause (speaking|audio)|resume (speaking|audio))\b", lower)),
        ),
    ]
