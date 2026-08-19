"""Specialist invocation — permission enforcement and observable execution.

A specialist may only call the actions its definition allows. Enforcement
happens here, before ARIA's action registry is reached, so a specialist cannot
borrow the process's authority by naming an action it was never granted.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from jarvis.specialized_agents import registry
from jarvis.specialized_agents.definitions import AgentDefinition

# Actions whose own layer decides authority or provenance from the requester.
# The agent's identity is stamped here rather than trusted from the payload, so
# an agent cannot ask as somebody else — or as nobody, which would read as
# unrestricted operator context, and would leave a routed call unattributable.
SKILL_ACTIONS = frozenset(
    {
        "skill_invoke",
        "skill_step",
        "mcp_invoke",
        "mcp_resource",
        "mcp_prompt",
        "mcp_discover",
        "mcp_step",
        "model_execute",
        "model_step",
        "model_route",
    }
)

log = logging.getLogger("jarvis.specialized_agents")


class PermissionDenied(PermissionError):
    """A specialist attempted an action outside its declared permissions."""


class ContractError(ValueError):
    """The invocation did not satisfy the agent's input contract."""


def resolve_model(agent: AgentDefinition) -> str:
    """Model for this specialist, chosen by the router."""
    return resolve_model_decision(agent).get("model", "")


def resolve_model_decision(agent: AgentDefinition) -> dict[str, Any]:
    """The specialist's model plus the reasoning behind it.

    Routing reads the agent's own declared role and requirements; it never
    changes what the agent is permitted to do. If routing cannot run, this
    degrades to the configured registry rather than to no model at all.
    """
    try:
        from jarvis.model_routing import route
        from jarvis.model_routing.integration import request_for_agent

        decision = route(request_for_agent(agent))
        if decision.ok:
            return {
                "model": decision.selected_model,
                "provider": decision.provider,
                "selection_method": decision.selection_method,
                "reason": decision.reason,
                "routed": True,
                "capability_evidence": dict(decision.capability_evidence),
                "candidates_considered": len(decision.candidates),
                "compatible": len(decision.accepted()),
            }
        # Nothing compatible is a real answer, not a reason to invent one.
        log.warning("no compatible model for agent %s: %s", agent.id, decision.reason)
        return {"model": "", "routed": True, "reason": decision.reason, "provider": ""}
    except Exception:  # noqa: BLE001 - model selection must never break invocation
        log.warning("routing unavailable for agent %s", agent.id, exc_info=True)

    try:
        from jarvis.config import MODELS

        fallback = MODELS.get(agent.preferred_model_role, "") or MODELS.get("general", "")
        return {
            "model": fallback,
            "provider": "ollama",
            "selection_method": "configured_registry",
            "reason": "routing unavailable; used the configured role model",
            "routed": False,
        }
    except Exception:  # noqa: BLE001
        return {"model": "", "routed": False, "reason": "no model configuration available"}


def check_permission(agent: AgentDefinition, action: str) -> None:
    if not agent.permits(action):
        raise PermissionDenied(f"Agent {agent.id!r} is not permitted to invoke action {action!r}")


def validate_input(agent: AgentDefinition, payload: dict[str, Any]) -> None:
    missing = [k for k in agent.input_contract if not str(payload.get(k) or "").strip()]
    if missing:
        raise ContractError(f"Agent {agent.id!r} requires: {missing}")


def call_action(
    agent: AgentDefinition,
    assistant: Any,
    action: str,
    params: dict[str, Any] | None = None,
    message: str = "",
) -> dict[str, Any]:
    """Invoke an ARIA action on the agent's behalf, if permitted."""
    check_permission(agent, action)
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action as registry_call

    ensure_handlers_loaded()
    payload = dict(params or {})
    if action in SKILL_ACTIONS:
        # The skills layer decides authority from the requester, so the agent's
        # identity is stamped here rather than trusted from the payload. An
        # agent must not be able to ask for a skill as somebody else — or as
        # nobody, which would read as unrestricted operator context.
        payload["requester"] = agent.id
    return registry_call(assistant, action, payload, message or action)


def invoke(
    agent_id: str,
    task: str,
    *,
    assistant: Any = None,
    action: str = "",
    params: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a specialist.

    Without an action this establishes the specialist's assignment — selection,
    permissions, model and instructions — which is what a caller needs before
    delegating work. With an action it executes that action under the agent's
    permissions.
    """
    started = time.perf_counter()
    agent = registry.get(agent_id)
    if not agent:
        return {"ok": False, "agent_id": agent_id, "error": f"No such agent: {agent_id}"}
    if not agent.enabled:
        return {"ok": False, "agent_id": agent_id, "error": f"Agent disabled: {agent_id}"}

    payload = {"task": task, **(context or {})}
    try:
        validate_input(agent, payload)
    except ContractError as exc:
        return {"ok": False, "agent_id": agent.id, "error": str(exc), "error_kind": "contract"}

    routing = resolve_model_decision(agent)
    model = routing.get("model", "")
    result: dict[str, Any] = {
        "ok": True,
        "agent_id": agent.id,
        "agent_name": agent.name,
        "role": agent.role,
        "task": task,
        "model": model,
        "model_routing": routing,
        "allowed_actions": list(agent.allowed_actions),
        "denied_actions": list(agent.denied_actions),
        "system_instructions": agent.system_instructions,
        "result": None,
    }

    if action:
        try:
            result["result"] = call_action(agent, assistant, action, params, task)
            result["action"] = action
        except PermissionDenied as exc:
            log.warning("Permission denied for agent %s action %s", agent.id, action)
            return {
                "ok": False,
                "agent_id": agent.id,
                "action": action,
                "error": str(exc),
                "error_kind": "permission_denied",
                "allowed_actions": list(agent.allowed_actions),
            }
        except Exception as exc:  # noqa: BLE001 - surfaced, never swallowed
            log.exception("Agent %s failed action %s", agent.id, action)
            return {
                "ok": False,
                "agent_id": agent.id,
                "action": action,
                "error": f"{type(exc).__name__}: {exc}",
                "error_kind": "execution",
            }
    else:
        result["result"] = {
            "assignment": f"{agent.name} ({agent.role}) assigned",
            "responsibilities": list(agent.responsibilities),
            "limitations": list(agent.limitations),
        }

    result["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
    return result


def select_and_invoke(
    task: str,
    *,
    assistant: Any = None,
    required_capability: str = "",
    action: str = "",
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pick the right specialist for a task, then run it — with the reasoning kept."""
    selection = registry.select(task, required_capability=required_capability)
    if not selection.get("agent_id"):
        return {"ok": False, "error": selection["reason"], "selection": selection}
    outcome = invoke(selection["agent_id"], task, assistant=assistant, action=action, params=params)
    outcome["selection"] = selection
    return outcome
