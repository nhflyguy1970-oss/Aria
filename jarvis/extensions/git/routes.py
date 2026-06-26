"""Git fast-path routes."""

from __future__ import annotations

import re

from jarvis.router_table import RouteRule


def git_routes():
    return [
        RouteRule(
            "git_status",
            22,
            "git status",
            lambda m, lower, _s: bool(re.search(r"\bgit status\b", lower)),
        ),
        RouteRule(
            "git_diff",
            23,
            "git diff",
            lambda m, lower, _s: bool(re.search(r"\bgit diff\b", lower)),
            params=lambda m: {"file": ""},
        ),
    ]
