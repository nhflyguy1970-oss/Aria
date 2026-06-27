"""Fly-tying fast-path routes."""

from __future__ import annotations

import re

from jarvis.router_table import RouteRule


def flytying_routes() -> list[RouteRule]:
    return [
        RouteRule(
            "fly_status",
            8,
            "fly status",
            lambda _m, lower, _s: bool(
                re.search(r"\b(fly[- ]?tying|blackfly)\b.+\bstatus\b", lower)
                or lower.strip() in ("fly tying status", "flytying status", "blackfly status")
            ),
        ),
        RouteRule(
            "fly_gold_build",
            9,
            "fly gold build",
            lambda _m, lower, _s: bool(re.search(r"\b(build|rebuild)\b.+\b(fly[- ]?tying\s+)?gold\b", lower)),
        ),
        RouteRule(
            "fly_recipe",
            11,
            "fly recipe",
            lambda _m, lower, _s: bool(
                re.search(
                    r"\b(show|get|give me|how (?:do i|to) tie)\b.+\b(recipe|pattern|fly)\b",
                    lower,
                )
                or re.search(r"\b(recipe|pattern)\s+for\b.+\b(fly|nymph|dry|streamer|emerger)\b", lower)
            ),
            lambda m: {"name": m.strip()},
        ),
        RouteRule(
            "fly_ask",
            12,
            "fly ask",
            lambda _m, lower, _s: bool(
                re.search(
                    r"\b(what (?:fly|flies|pattern)|which (?:fly|pattern)|fly tying question)\b",
                    lower,
                )
                or re.search(r"\b(fly[- ]?tying)\b.+\b(help|advice|suggest|recommend)\b", lower)
            ),
            lambda m: {"question": m.strip()},
        ),
        RouteRule(
            "fly_search",
            13,
            "fly search",
            lambda _m, lower, _s: bool(
                re.search(r"\b(search|find|list)\b.+\b(fly|flies|patterns?|recipes?)\b", lower)
                or re.search(r"\b(dry fly|nymph|streamer|emerger)\b.+\bpatterns?\b", lower)
            ),
            lambda m: {"query": m.strip()},
        ),
    ]
