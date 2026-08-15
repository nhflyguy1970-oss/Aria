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
        RouteRule(
            "git_commit",
            24,
            "git commit",
            lambda m, lower, _s: bool(re.match(r"^commit:\s*.+", lower)),
            params=lambda m: {
                "message": re.sub(r"^commit:\s*", "", m, count=1, flags=re.I).strip()
            },
        ),
        RouteRule(
            "git_branch",
            25,
            "git branch",
            lambda m, lower, _s: bool(re.search(r"\bcreate branch\b", lower)),
            params=lambda m: {
                "name": (re.search(r"create branch\s+(\S+)", m, flags=re.I) or [None, ""])[1]
            },
        ),
    ]
