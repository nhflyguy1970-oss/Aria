"""Agents behavior — cooperating multi-agent chains."""

from __future__ import annotations

from typing import Any

from jarvis.agents.coordinator import run_agent_chain, suggest_agents
from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action

_AGENT_ACTIONS = {
    "agent_suggest": lambda a, p, m: _suggest(p, m),
    "agent_chain": lambda a, p, m: _chain(a, p, m),
    "agent_job_start": lambda a, p, m: _job_start(a, p, m),
    "agent_job_status": lambda a, p, m: _job_status(p),
}


def _suggest(params: dict, message: str) -> dict:
    goal = (params.get("goal") or message or "").strip()
    roles = suggest_agents(goal)
    return {
        "ok": True,
        "message": f"Suggested agents: {', '.join(roles)}",
        "data": {"goal": goal, "roles": roles},
    }


def _chain(assistant, params: dict, message: str) -> dict:
    goal = (params.get("goal") or message or "").strip()
    if not goal:
        return {"ok": False, "message": "goal parameter required"}
    roles = params.get("roles")
    if isinstance(roles, str):
        roles = [r.strip() for r in roles.split(",") if r.strip()]
    result = run_agent_chain(
        assistant,
        goal,
        roles=roles if isinstance(roles, list) else None,
        stop_on_error=not bool(params.get("continue_on_error")),
    )
    return {
        "ok": result.get("ok", False),
        "message": result.get("summary") or "Agent chain complete.",
        "data": result,
    }


def _job_start(assistant, params: dict, message: str) -> dict:
    from jarvis.jobs.checkpointed import start_agent_job

    goal = (params.get("goal") or message or "").strip()
    if not goal:
        return {"ok": False, "message": "goal required"}
    roles = params.get("roles")
    if isinstance(roles, str):
        roles = [r.strip() for r in roles.split(",") if r.strip()]
    job = start_agent_job(assistant, goal, roles=roles if isinstance(roles, list) else None)
    return {
        "ok": True,
        "message": f"Started job `{job.id}` — {job.kind}",
        "data": job.to_dict(),
    }


def _job_status(params: dict) -> dict:
    from jarvis.jobs.checkpointed import job_status

    job_id = (params.get("job_id") or params.get("id") or "").strip()
    if not job_id:
        return {"ok": False, "message": "job_id required"}
    return job_status(job_id)


@register_behavior
class AgentsBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="agents",
            name="Agents",
            category="Agents",
            description="Cooperating agent chains with shared context and handoffs",
            module_path="jarvis.behaviors.agents",
            test_module="tests.test_agents",
            action_names=list(_AGENT_ACTIONS.keys()),
            dependencies=["capability_registry"],
            stability="stable",
            owner="application",
            version="1.0.0",
        )

    def attach(self) -> list[str]:
        for action, handler in _AGENT_ACTIONS.items():
            register_action(
                action,
                info=False,
                module="agents",
                description=action.replace("_", " "),
            )(self._bind(handler))
        return []

    def execute(self, orchestrator: Any, action: str, params: dict, message: str) -> dict | None:
        handler = _AGENT_ACTIONS.get(action)
        if handler is None:
            return None
        return handler(orchestrator, params, message)

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            return handler(orchestrator, params, message)

        return _entry
