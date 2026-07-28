"""Specialist Team orchestration — AI OS capability orchestration (not CrewAI/AutoGen).

Chat → Team propose → Confirm → Run → Job/Activity → Inspect
Reuses CodingAgent, Memory, Planner, Documents, Vision, etc.
"""

from __future__ import annotations

from jarvis.specialists.composer import compose_team
from jarvis.specialists.engine import explain_run, propose_team, run_team
from jarvis.specialists.history import get_run, list_runs, search_runs

__all__ = [
    "compose_team",
    "propose_team",
    "run_team",
    "explain_run",
    "list_runs",
    "get_run",
    "search_runs",
]
