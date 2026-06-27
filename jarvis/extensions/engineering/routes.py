"""Engineering voice/chat routes."""

from __future__ import annotations

import re

from jarvis.router_table import RouteRule


def engineering_routes() -> list[RouteRule]:
    return [
        RouteRule(
            "cad_status",
            8,
            "cad status",
            lambda m, lower, _s: bool(re.search(r"\b(cad status|cad tools|engineering status)\b", lower)),
        ),
        RouteRule(
            "generate_cad",
            12,
            "generate cad",
            lambda m, lower, _s: bool(
                re.search(r"\b(design|generate|create|make)\b.+\b(cad|stl|part|adapter|bracket|hose)\b", lower)
                or re.search(r"\bengineering design\b", lower)
            ),
            lambda m: {"prompt": m.strip()},
        ),
        RouteRule(
            "iterate_cad",
            13,
            "iterate cad",
            lambda m, lower, _s: bool(
                re.search(r"\b(iterate|edit|modify|change|update)\b.+\b(cad|design|model|part|stl)\b", lower)
                or re.search(r"\bmake it (taller|shorter|wider|thinner|thicker|bigger|smaller)\b", lower)
            ),
            lambda m: {"prompt": m.strip(), "edit": True},
        ),
        RouteRule(
            "slice_stl",
            10,
            "slice stl",
            lambda m, lower, _s: bool(re.search(r"\bslice\b.+\b(stl|g-?code)\b", lower)),
        ),
        RouteRule(
            "printer_status",
            8,
            "printer status",
            lambda m, lower, _s: bool(re.search(r"\b(printer|moonraker|klipper)\b.+\bstatus\b", lower)),
        ),
        RouteRule(
            "teach_cad",
            14,
            "teach cad",
            lambda m, lower, _s: bool(re.search(r"\bteach\s+cad\b", lower)),
            lambda m: {},
        ),
    ]
