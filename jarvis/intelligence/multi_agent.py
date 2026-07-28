"""Cooperating multi-agent orchestration — compatibility wrapper.

Prefer jarvis.specialists.run_team for new code.
"""

from __future__ import annotations

from typing import Any

from jarvis.specialists.catalog import SPECIALISTS as _CATALOG
from jarvis.specialists.composer import compose_team
from jarvis.specialists.engine import run_team
from jarvis.specialists.scratchpad import SharedScratchpad

# Back-compat export shape
SPECIALISTS: dict[str, dict[str, str]] = {
    sid: {"role": str(m.get("role") or sid), "action": str(m.get("organ") or sid)}
    for sid, m in _CATALOG.items()
    if not m.get("alias_of")
}


def resolve_specialists(goal: str, specialists: list[str] | None = None) -> list[str]:
    return list(compose_team(goal, specialists=specialists)["team"])


def run_multi_agent(
    assistant: Any,
    goal: str,
    *,
    specialists: list[str] | None = None,
    stop_on_error: bool = False,
    max_agents: int = 6,
) -> dict[str, Any]:
    """Legacy entry — confirms automatically for API compatibility; prefer explicit confirm."""
    result = run_team(
        assistant,
        goal,
        specialists=(specialists or [])[:max_agents] or None,
        confirm=True,
        stop_on_error=stop_on_error,
        budget={"max_specialists": max_agents, "require_confirm": False},
        trigger="compat-legacy",
        emit_bridges=True,
        approve_writes=True,  # legacy callers expected execution
    )
    # Shape compat fields
    result.setdefault("specialists", result.get("team"))
    return result


# Re-export scratchpad name
__all__ = ["SPECIALISTS", "SharedScratchpad", "resolve_specialists", "run_multi_agent"]
