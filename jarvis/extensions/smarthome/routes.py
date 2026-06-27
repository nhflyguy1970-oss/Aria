"""Smart home fast routes."""

from __future__ import annotations

import re

from jarvis.router_table import RouteRule


def smarthome_routes() -> list[RouteRule]:
    return [
        RouteRule(
            "scene_recall",
            13,
            "scene preset",
            lambda m, lower, _s: bool(re.search(r"\b(movie mode|work mode)\b", lower)),
            lambda m: {"preset": "movie mode" if "movie" in m.lower() else "work mode"},
        ),
        RouteRule(
            "kasa_discover",
            14,
            "discover kasa",
            lambda m, lower, _s: bool(re.search(r"\b(discover|find|scan)\s+kasa\b", lower)),
        ),
    ]
