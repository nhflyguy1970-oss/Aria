"""Agent coordinator — compatibility wrapper over Specialist Team orchestrator."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from jarvis.specialists.composer import map_roles_to_specialists, suggest_roles_legacy
from jarvis.specialists.engine import run_team

logger = logging.getLogger("jarvis.agents")

AGENT_CHAIN_KEYWORDS = {
    "research": ("research", "investigate", "find out", "learn about", "search"),
    "coding": ("implement", "fix", "code", "refactor", "build", "debug"),
    "documentation": ("document", "write docs", "readme", "adr"),
    "qa": ("test", "verify", "qa", "regression", "lint"),
    "planning": ("plan", "break down", "roadmap", "steps"),
    "knowledge": ("index", "ingest", "knowledge", "sync"),
    "operations": ("status", "diagnose", "recover", "workstation"),
}


class AgentRole(StrEnum):
    PLANNER = "planning"
    RESEARCH = "research"
    CODING = "coding"
    DOCUMENTATION = "documentation"
    QA = "qa"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    TRAINING = "training"
    AUTOMATION = "automation"
    OPERATIONS = "operations"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


@dataclass
class AgentStep:
    role: str
    action: str
    ok: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: int = 0


def suggest_agents(goal: str) -> list[str]:
    return suggest_roles_legacy(goal)


class AgentCoordinator:
    """Legacy facade — delegates to unified Specialist Team engine."""

    def __init__(self, assistant: Any) -> None:
        self._assistant = assistant

    def run_chain(
        self,
        goal: str,
        *,
        roles: list[str] | None = None,
        stop_on_error: bool = True,
    ) -> dict[str, Any]:
        result = run_team(
            self._assistant,
            goal,
            roles=roles,
            specialists=map_roles_to_specialists(roles) if roles else None,
            confirm=True,
            stop_on_error=stop_on_error,
            budget={"require_confirm": False},
            trigger="compat-legacy",
            emit_bridges=True,
            approve_writes=True,
        )
        # Legacy field names
        return {
            "ok": result.get("ok"),
            "chain_id": result.get("run_id"),
            "goal": goal,
            "roles": roles or [s.get("role") for s in (result.get("steps") or []) if s.get("role")],
            "steps": [
                {
                    "role": s.get("role") or s.get("agent"),
                    "action": s.get("action") or s.get("organ") or "",
                    "ok": s.get("ok"),
                    "message": s.get("message") or s.get("error") or "",
                    "elapsed_ms": s.get("elapsed_ms") or 0,
                    "data": s.get("data") or {},
                }
                for s in (result.get("steps") or [])
                if s.get("agent") != "synthesizer"
            ],
            "summary": result.get("summary") or result.get("synthesis") or "",
            "run_id": result.get("run_id"),
            "status": result.get("status"),
            "team": result.get("team"),
        }


def run_agent_chain(assistant: Any, goal: str, **kwargs: Any) -> dict[str, Any]:
    return AgentCoordinator(assistant).run_chain(goal, **kwargs)
