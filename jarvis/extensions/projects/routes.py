"""Fast-path routes for Projects workspace identity."""

from __future__ import annotations

import re

from jarvis.router_table import RouteRule


def project_routes():
    return [
        RouteRule(
            "project_switch",
            14,
            "switch project",
            (
                lambda m, lower, _s: bool(
                    re.search(r"\b(switch|open|use)\s+(?:to\s+)?project\b", lower)
                    or re.search(r"\b(switch|open)\s+to\s+[\w-]+\s+project\b", lower)
                )
            ),
            (
                lambda m: {
                    "slug": re.sub(
                        r".*?(?:project\s+|to\s+)",
                        "",
                        re.sub(r"\s+project\s*$", "", m, flags=re.I),
                        count=1,
                        flags=re.I,
                    ).strip()
                }
            ),
        ),
        RouteRule(
            "project_list",
            15,
            "list projects",
            (lambda m, lower, _s: bool(re.search(r"\b(list|show)\s+projects\b", lower))),
        ),
        RouteRule(
            "project_current",
            15,
            "current project",
            (
                lambda m, lower, _s: bool(
                    re.search(r"\b(current|active|which)\s+project\b", lower)
                    or lower.strip() in ("what project am i on", "what project are we on")
                )
            ),
        ),
        RouteRule(
            "project_status",
            15,
            "project status",
            (lambda m, lower, _s: bool(re.search(r"\bproject\s+status\b", lower))),
        ),
        RouteRule(
            "project_continue",
            14,
            "continue project",
            (
                lambda m, lower, _s: bool(
                    re.search(r"\bcontinue\s+(?:the\s+)?project\b", lower)
                    or re.search(r"\b(resume|continue)\s+working\s+on\b", lower)
                )
            ),
        ),
        RouteRule(
            "project_briefing",
            14,
            "project briefing",
            (
                lambda m, lower, _s: bool(
                    re.search(r"\bproject\s+briefing\b", lower)
                    or re.search(r"\b(brief|briefing)\s+(?:me\s+)?(?:on\s+)?(?:the\s+)?project\b", lower)
                )
            ),
        ),
        RouteRule(
            "project_create",
            14,
            "create project",
            (lambda m, lower, _s: bool(re.search(r"\b(create|new)\s+project\b", lower))),
        ),
        RouteRule(
            "project_home",
            16,
            "project home",
            (lambda m, lower, _s: bool(re.search(r"\bproject\s+home\b", lower))),
        ),
    ]
