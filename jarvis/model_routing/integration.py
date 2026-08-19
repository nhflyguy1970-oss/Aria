"""Turning ARIA's existing callers into routing requests.

Agents already declare a preferred role and model requirements; skills declare
model requirements; missions and research already work in roles. This module
translates those into RoutingRequests so there is one selection path rather than
a separate one per subsystem — and so routing never becomes a way to widen what
a caller is allowed to do.
"""

from __future__ import annotations

from typing import Any

from jarvis.model_routing import capabilities as caps
from jarvis.model_routing.request import BALANCED, RoutingRequest

# Agent model_requirements strings ARIA already uses, mapped to capabilities.
_REQUIREMENT_CAPABILITIES = {
    "code": caps.CODING,
    "coding": caps.CODING,
    "long_context": caps.LONG_CONTEXT,
    "tools": caps.TOOL_USE,
    "tool_use": caps.TOOL_USE,
    "vision": caps.VISION,
    "reasoning": caps.REASONING,
    "research": caps.RESEARCH,
    "structured_output": caps.STRUCTURED_OUTPUT,
}

# Agent role → the role name the model registry already uses.
_AGENT_ROLE = {
    "research": "web_research",
    "coding": "coding",
    "analysis": "reasoning",
    "general": "conversation",
}


def _capabilities_for(requirements: tuple[str, ...]) -> tuple[list[str], bool, bool]:
    """Split declared requirements into capabilities and the explicit flags.

    A requirement ARIA does not recognise is dropped rather than guessed at:
    inventing a capability here would be exactly the thing this milestone
    forbids.
    """
    required: list[str] = []
    tools = vision = False
    for raw in requirements or ():
        capability = _REQUIREMENT_CAPABILITIES.get(str(raw).strip().lower())
        if capability is None:
            continue
        if capability == caps.TOOL_USE:
            tools = True
        elif capability == caps.VISION:
            vision = True
        else:
            required.append(capability)
    return sorted(set(required)), tools, vision


def request_for_agent(
    agent: Any,
    *,
    task_type: str = "",
    min_context_tokens: int = 0,
    require_tools: bool = False,
    require_vision: bool = False,
    require_structured_output: bool = False,
    preferred_model: str = "",
    skill_id: str = "",
    mission_id: str = "",
    latency_preference: str = BALANCED,
) -> RoutingRequest:
    """Build a routing request from a specialist's own declaration.

    This reads the agent; it never changes it. Routing decides which model does
    the work, not what the agent is permitted to do.
    """
    role = _AGENT_ROLE.get(getattr(agent, "role", ""), "conversation")
    required, tools, vision = _capabilities_for(tuple(getattr(agent, "model_requirements", ())))
    return RoutingRequest(
        task_type=task_type or getattr(agent, "role", "") or "general",
        role=role,
        required_capabilities=tuple(required),
        require_tools=require_tools or tools,
        require_vision=require_vision or vision,
        require_structured_output=require_structured_output,
        min_context_tokens=min_context_tokens,
        preferred_model=preferred_model,
        latency_preference=latency_preference,
        agent_id=getattr(agent, "id", ""),
        skill_id=skill_id,
        mission_id=mission_id,
        requester=getattr(agent, "id", ""),
    )


def request_for_role(
    role: str,
    *,
    task_type: str = "",
    min_context_tokens: int = 0,
    require_tools: bool = False,
    require_vision: bool = False,
    require_structured_output: bool = False,
    preferred_model: str = "",
    requester: str = "",
    mission_id: str = "",
    latency_preference: str = BALANCED,
) -> RoutingRequest:
    """Build a routing request for one of ARIA's existing model roles."""
    return RoutingRequest(
        task_type=task_type or role or "general",
        role=role,
        require_tools=require_tools,
        require_vision=require_vision,
        require_structured_output=require_structured_output,
        min_context_tokens=min_context_tokens,
        preferred_model=preferred_model,
        latency_preference=latency_preference,
        requester=requester,
        mission_id=mission_id,
    )


def resolve_model_for_role(role: str, **kwargs: Any) -> str:
    """The model a role should use now, or "" when nothing is compatible.

    Falls back to the configured registry answer only when routing itself
    cannot run, so a routing outage degrades to today's behaviour rather than
    to no model at all.
    """
    from jarvis.model_routing.router import route

    try:
        decision = route(request_for_role(role, **kwargs))
        if decision.ok:
            return decision.selected_model
    except Exception:  # noqa: BLE001 - never let routing break model resolution
        import logging

        logging.getLogger("jarvis.model_routing").warning(
            "routing failed for role %s; using the configured registry", role, exc_info=True
        )
    from jarvis.model_store import model_for

    return model_for(role)
