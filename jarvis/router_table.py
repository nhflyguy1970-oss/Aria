"""Declarative fast-path routes (Phase 3 router table)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Callable

from jarvis.session import SessionContext


@dataclass(frozen=True)
class RouteRule:
    action: str
    priority: int
    thinking: str
    match: Callable[[str, str, SessionContext], bool]
    params: Callable[[str], dict] | None = None


def _params_empty(_message: str) -> dict:
    return {}


def _rules() -> list[RouteRule]:
    from jarvis.router import (
        _is_capabilities_question,
        _is_greeting,
        _is_models_question,
    )

    return [
        RouteRule(
            "clear",
            5,
            "clear conversation",
            lambda m, lower, _s: bool(re.match(r"^clear[\s!.?,]*$", lower)),
        ),
        RouteRule(
            "models_info",
            8,
            "models question",
            lambda m, lower, _s: _is_models_question(lower),
        ),
        RouteRule(
            "capabilities",
            10,
            "capabilities question",
            lambda m, lower, _s: _is_capabilities_question(lower)
            or (
                re.search(r"^(hi|hello|hey)\b", lower) and _is_capabilities_question(lower)
            ),
        ),
        RouteRule(
            "morning_briefing",
            11,
            "morning briefing",
            lambda m, lower, _s: bool(
                re.search(r"^good morning\b", lower)
                and os.getenv("JARVIS_BRIEFING", "1") != "0"
            ),
        ),
        RouteRule(
            "greeting",
            12,
            "greeting",
            lambda m, lower, _s: _is_greeting(lower),
        ),
        RouteRule(
            "capabilities",
            14,
            "hello + help",
            lambda m, lower, _s: bool(
                re.match(r"^(hi|hello|hey)[\s!.?,]*$", lower)
                and re.search(r"\bhelp\b", lower)
            ),
        ),
        RouteRule(
            "journal_today",
            20,
            "journal today",
            lambda m, lower, _s: bool(
                re.search(r"\b(journal today|today'?s journal|daily log)\b", lower)
            ),
        ),
        RouteRule(
            "journal_monthly",
            21,
            "journal monthly",
            lambda m, lower, _s: bool(
                re.search(r"\b(monthly journal|journal this month)\b", lower)
            ),
        ),
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
        ),
        RouteRule(
            "weather_forecast",
            24,
            "weather",
            lambda m, lower, _s: bool(
                re.search(r"\b(weather|forecast|temperature)\b", lower)
                and not re.search(r"\bbriefing\b", lower)
            ),
        ),
    ]


_SORTED: list[RouteRule] | None = None


def _sorted_rules() -> list[RouteRule]:
    global _SORTED
    if _SORTED is None:
        rules = list(_rules())
        try:
            from jarvis.extensibility.loader import extension_routes

            rules.extend(extension_routes())
        except Exception:
            pass
        _SORTED = sorted(rules, key=lambda r: r.priority)
    return _SORTED


def match_router_table(message: str, session: SessionContext) -> dict | None:
    """Return route intent dict if a table rule matches, else None."""
    lower = message.lower().strip()
    for rule in _sorted_rules():
        try:
            if rule.match(message, lower, session):
                params = (rule.params or _params_empty)(message)
                return {"action": rule.action, "params": params, "thinking": rule.thinking}
        except Exception:
            continue
    return None


def list_rules() -> list[dict]:
    return [
        {
            "action": r.action,
            "priority": r.priority,
            "thinking": r.thinking,
        }
        for r in _sorted_rules()
    ]
