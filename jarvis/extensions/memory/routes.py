"""Memory fast-path routing rules."""

from __future__ import annotations

import re

from jarvis.router_table import RouteRule


def _remember_text(message: str) -> str:
    text = re.sub(
        r"^(please\s+)?(remember|don't forget|note that|keep in mind)\s*(that\s+)?",
        "",
        message,
        flags=re.I,
    ).strip()
    return re.sub(r"^(these|the following)\s+facts?\s*:?\s*", "", text, flags=re.I).strip()


def memory_routes():
    return [
        RouteRule(
            "memory_about_user",
            15,
            "user profile",
            lambda m, lower, _s: bool(
                re.search(
                    r"\b(something i like|what do i like|my hobbies|about me\b|who am i\b|tell me about myself)\b",
                    lower,
                )
            ),
            params=lambda m: {"question": m},
        ),
        RouteRule(
            "recall",
            16,
            "recall memories",
            lambda m, lower, _s: bool(re.search(r"\b(what do you remember|recall|my memories)\b", lower)),
        ),
        RouteRule(
            "memory_search",
            17,
            "memory search",
            lambda m, lower, _s: bool(
                re.search(r"\b(search my memory|search memory|find in memory|memory search)\b", lower)
            ),
            params=lambda m: {
                "query": re.sub(
                    r"^(please\s+)?(search my memory|search memory|find in memory|memory search)\s*(for\s+)?",
                    "",
                    m,
                    flags=re.I,
                ).strip()
                or m
            },
        ),
        RouteRule(
            "remember",
            28,
            "remember fact",
            lambda m, lower, _s: bool(
                re.search(r"\b(remember|don't forget|note that|keep in mind)\b", lower)
                and not re.search(r"\bremember (this|our) conversation\b", lower)
            ),
            params=lambda m: {"text": _remember_text(m)},
        ),
    ]
