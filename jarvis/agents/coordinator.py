"""Agent coordinator — cooperating specialists with shared context."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

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


_ROLE_ACTIONS: dict[str, str] = {
    AgentRole.PLANNER.value: "plan_create",
    AgentRole.RESEARCH.value: "unified_search",
    AgentRole.CODING.value: "coding_read",
    AgentRole.DOCUMENTATION.value: "journal_log",
    AgentRole.QA.value: "run_tests",
    AgentRole.KNOWLEDGE.value: "knowledge_sync",
    AgentRole.MEMORY.value: "memory_search",
    AgentRole.AUTOMATION.value: "workstation_recover",
    AgentRole.OPERATIONS.value: "workstation_diagnose",
    AgentRole.MONITORING.value: "workstation_status",
    AgentRole.DEPLOYMENT.value: "upgrade_verify",
    AgentRole.TRAINING.value: "tool_list",
}


def suggest_agents(goal: str) -> list[str]:
    """Infer agent chain from goal text."""
    lower = (goal or "").lower()
    roles: list[str] = []
    if any(k in lower for k in AGENT_CHAIN_KEYWORDS["planning"]):
        roles.append(AgentRole.PLANNER.value)
    if any(k in lower for k in AGENT_CHAIN_KEYWORDS["research"]):
        roles.append(AgentRole.RESEARCH.value)
    if any(k in lower for k in AGENT_CHAIN_KEYWORDS["coding"]):
        roles.append(AgentRole.CODING.value)
    if any(k in lower for k in AGENT_CHAIN_KEYWORDS["documentation"]):
        roles.append(AgentRole.DOCUMENTATION.value)
    if any(k in lower for k in AGENT_CHAIN_KEYWORDS["qa"]):
        roles.append(AgentRole.QA.value)
    if any(k in lower for k in AGENT_CHAIN_KEYWORDS["knowledge"]):
        roles.append(AgentRole.KNOWLEDGE.value)
    if any(k in lower for k in AGENT_CHAIN_KEYWORDS["operations"]):
        roles.append(AgentRole.OPERATIONS.value)
    if not roles:
        roles = [AgentRole.RESEARCH.value, AgentRole.PLANNER.value]
    return roles


def _params_for_role(role: str, goal: str, context: dict[str, Any]) -> dict[str, Any]:
    prior = context.get("last_message") or ""
    if role == AgentRole.RESEARCH.value:
        return {"query": goal, "refresh": False}
    if role == AgentRole.PLANNER.value:
        return {"title": goal[:120], "description": prior[:2000] or goal}
    if role == AgentRole.CODING.value:
        return {"path": context.get("path") or ".", "task": goal}
    if role == AgentRole.MEMORY.value:
        return {"query": goal}
    if role == AgentRole.DOCUMENTATION.value:
        return {"text": f"Agent chain note: {goal}\n{prior[:500]}"}
    return {"query": goal, "task": goal}


class AgentCoordinator:
    """Orchestrate multi-agent handoffs through behavior actions."""

    def __init__(self, assistant: Any) -> None:
        self._assistant = assistant

    def run_chain(
        self,
        goal: str,
        *,
        roles: list[str] | None = None,
        stop_on_error: bool = True,
    ) -> dict[str, Any]:
        from jarvis.handlers.registry import call_action, has_action

        chain_id = uuid.uuid4().hex[:12]
        selected = roles or suggest_agents(goal)
        context: dict[str, Any] = {"goal": goal, "chain_id": chain_id, "artifacts": []}
        steps: list[dict[str, Any]] = []

        for role in selected:
            action = _ROLE_ACTIONS.get(role)
            if not action or not has_action(action):
                steps.append(
                    {
                        "role": role,
                        "action": action or "",
                        "ok": False,
                        "message": f"No action for role {role}",
                    }
                )
                if stop_on_error:
                    break
                continue

            params = _params_for_role(role, goal, context)
            started = time.time()
            try:
                result = call_action(self._assistant, action, params, goal)
                ok = bool(result.get("ok", True))
                message = str(result.get("message") or "")[:2000]
            except Exception as exc:
                ok = False
                message = str(exc)
                result = {"ok": False, "error": str(exc)}

            elapsed = int((time.time() - started) * 1000)
            step = {
                "role": role,
                "action": action,
                "ok": ok,
                "message": message,
                "elapsed_ms": elapsed,
                "data": {k: v for k, v in result.items() if k not in ("message",)},
            }
            steps.append(step)
            context["artifacts"].append(step)
            context["last_message"] = message
            if not ok and stop_on_error:
                break

        ok_count = sum(1 for s in steps if s.get("ok"))
        summary_lines = [
            f"- **{s['role']}** ({s['action']}): {'ok' if s['ok'] else 'failed'}" for s in steps
        ]
        return {
            "ok": ok_count == len(steps) and bool(steps),
            "chain_id": chain_id,
            "goal": goal,
            "roles": selected,
            "steps": steps,
            "summary": "## Agent chain\n\n" + "\n".join(summary_lines),
        }


def run_agent_chain(assistant: Any, goal: str, **kwargs: Any) -> dict[str, Any]:
    return AgentCoordinator(assistant).run_chain(goal, **kwargs)
