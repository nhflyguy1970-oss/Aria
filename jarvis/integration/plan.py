"""Deciding how much machinery a request actually needs.

The default is the smallest thing that could work. A question stays a question:
it does not acquire a workflow, a mission, a browser session or a research job
because the environment happens to have them. Escalation happens only on signals
that are present in the request itself, and every decision says which signal
caused it.

This is deliberately a small deterministic triage, not a planner. Where real
planning is needed the autonomous workflow system already provides it.
"""

from __future__ import annotations

import re
from typing import Any

from jarvis.integration import policy

# Routes, cheapest first.
ANSWER = "answer"
SKILL = "skill"
AGENT = "agent"
WORKFLOW = "workflow"
ROUTES = (ANSWER, SKILL, AGENT, WORKFLOW)

# Signals that a request needs more than a direct answer. Each is a phrase a
# person would actually write, and each names the capability it implies.
_SIGNALS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "research",
        re.compile(r"\b(research|investigate|find out|look into|survey)\b", re.I),
        "research",
    ),
    (
        "evidence",
        re.compile(r"\b(verify|evidence|corroborat|fact.?check|sources?)\b", re.I),
        "research",
    ),
    ("browser", re.compile(r"\b(browse|open the page|website|url|https?://)", re.I), "browser"),
    (
        "coding",
        re.compile(
            r"\b(refactor|implement|fix the (bug|test)|write a (test|function)|"
            r"repository|codebase)\b",
            re.I,
        ),
        "coding",
    ),
    ("tools", re.compile(r"\b(use the tool|mcp|external tool|provider)\b", re.I), "tool"),
    (
        "multi_step",
        re.compile(r"\b(then|after that|and then|step by step|first.*then)\b", re.I),
        "workflow",
    ),
    (
        "long_running",
        re.compile(
            r"\b(keep (working|going)|over time|in the background|"
            r"until (it|you) )\b",
            re.I,
        ),
        "workflow",
    ),
)

# More than this many distinct capability signals means the request genuinely
# spans subsystems, which is what a workflow is for.
WORKFLOW_SIGNAL_THRESHOLD = 2


def triage(request: str, *, autonomy: str = "", requester: str = "") -> dict[str, Any]:
    """Choose the smallest route that can serve the request, and explain it."""
    text = (request or "").strip()
    level = policy.effective_level(autonomy)

    matched: list[dict[str, str]] = []
    for name, pattern, capability in _SIGNALS:
        found = pattern.search(text)
        if found:
            matched.append(
                {
                    "signal": name,
                    "capability": capability,
                    "matched_text": found.group(0)[:60],
                }
            )

    capabilities = sorted({m["capability"] for m in matched})
    reasons: list[str] = []

    if not text:
        return _decision(ANSWER, ["the request is empty"], matched, capabilities, level)

    if not matched:
        # The overwhelmingly common case, and the one worth keeping cheap.
        return _decision(
            ANSWER,
            ["no signal that this needs tools, research or multiple steps"],
            matched,
            capabilities,
            level,
        )

    wants_workflow = len(capabilities) >= WORKFLOW_SIGNAL_THRESHOLD or any(
        m["capability"] == "workflow" for m in matched
    )

    if wants_workflow:
        reasons.append(f"{len(capabilities)} capability signal(s): {', '.join(capabilities)}")
        if policy.permits("workflow", level):
            return _decision(WORKFLOW, reasons, matched, capabilities, level)
        reasons.append(f"autonomy level {level} does not permit a workflow; using an agent")
        route = AGENT if policy.permits("agent", level) else ANSWER
        return _decision(route, reasons, matched, capabilities, level)

    capability = capabilities[0]
    reasons.append(f"single capability signal: {capability}")
    if capability in ("research", "browser", "coding") and policy.permits("agent", level):
        return _decision(AGENT, reasons, matched, capabilities, level)
    if policy.permits("skill", level):
        return _decision(SKILL, reasons, matched, capabilities, level)
    reasons.append(f"autonomy level {level} permits only a direct answer")
    return _decision(ANSWER, reasons, matched, capabilities, level)


def _decision(
    route: str,
    reasons: list[str],
    signals: list[dict[str, str]],
    capabilities: list[str],
    level: str,
) -> dict[str, Any]:
    return {
        "route": route,
        "autonomy": level,
        "reasons": reasons,
        "signals": signals,
        "capabilities": capabilities,
        "escalated": route != ANSWER,
        "bounds": policy.bounds_for(level),
        "explanation": (f"routed to {route}: " + "; ".join(reasons)),
    }


def suggested_agent(capabilities: list[str]) -> str:
    """Which specialist fits, using ARIA's existing roles."""
    if "coding" in capabilities:
        return "coding_specialist"
    if "research" in capabilities or "browser" in capabilities:
        return "research_specialist"
    if "tool" in capabilities:
        return "research_specialist"
    return "general_specialist"
