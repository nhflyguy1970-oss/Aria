"""Specialized agent handlers — discovery, selection, invocation, mission steps."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action(
    "agent_list", module="general", description="List ARIA's specialized agents", info=True
)
def agent_list(assistant, params: dict, message: str) -> dict:
    from jarvis import specialized_agents as agents

    include_disabled = bool(params.get("include_disabled"))
    items = [a.to_dict() for a in agents.list_agents(include_disabled=include_disabled)]
    lines = [f"- `{a['id']}` **{a['name']}** ({a['role']}) — {a['description']}" for a in items]
    return ok("\n".join(lines) or "No agents registered.", module="general", agents=items)


@register_action("agent_get", module="general", description="Show one specialized agent", info=True)
def agent_get(assistant, params: dict, message: str) -> dict:
    from jarvis import specialized_agents as agents

    agent_id = (params.get("agent_id") or params.get("id") or "").strip()
    agent = agents.get(agent_id)
    if not agent:
        return err(f"No agent `{agent_id}`.", module="general")
    data = agent.to_dict(include_instructions=True)
    lines = [
        f"**{agent.name}** (`{agent.id}`) — {agent.role}",
        agent.description,
        f"Capabilities: {', '.join(agent.capabilities)}",
        f"Allowed actions: {', '.join(agent.allowed_actions)}",
    ]
    if agent.denied_actions:
        lines.append(f"Denied actions: {', '.join(agent.denied_actions)}")
    if agent.limitations:
        lines.append("Limitations: " + "; ".join(agent.limitations))
    return ok("\n".join(lines), module="general", agent=data)


@register_action(
    "agent_capabilities",
    module="general",
    description="Show which specialists provide which capabilities",
    info=True,
)
def agent_capabilities(assistant, params: dict, message: str) -> dict:
    from jarvis import specialized_agents as agents

    caps = agents.capabilities()
    lines = [f"- {cap}: {', '.join(ids)}" for cap, ids in caps.items()]
    return ok("\n".join(lines), module="general", capabilities=caps)


@register_action(
    "agent_select",
    module="general",
    description="Choose the right specialist for a task, with reasoning",
    info=True,
)
def agent_select(assistant, params: dict, message: str) -> dict:
    from jarvis import specialized_agents as agents

    task = (params.get("task") or message or "").strip()
    if not task and not params.get("capability"):
        return err("Describe the task to select a specialist.", module="general")
    selection = agents.select(task, required_capability=(params.get("capability") or "").strip())
    if not selection.get("agent_id"):
        return err(selection["reason"], module="general", selection=selection)
    return ok(
        f"Selected **{selection['agent']['name']}** (`{selection['agent_id']}`) — {selection['reason']}",
        module="general",
        selection=selection,
    )


@register_action("agent_invoke", module="general", description="Invoke a specialized agent")
def agent_invoke(assistant, params: dict, message: str) -> dict:
    from jarvis import specialized_agents as agents

    task = (params.get("task") or message or "").strip()
    if not task:
        return err("An agent invocation needs a task.", module="general")
    agent_id = (params.get("agent_id") or "").strip()
    action = (params.get("action") or "").strip()
    action_params = params.get("params") or {}
    if not isinstance(action_params, dict):
        return err("params must be an object.", module="general")

    if agent_id:
        result = agents.invoke(
            agent_id, task, assistant=assistant, action=action, params=action_params
        )
    else:
        result = agents.select_and_invoke(
            task,
            assistant=assistant,
            required_capability=(params.get("capability") or "").strip(),
            action=action,
            params=action_params,
        )
    if not result.get("ok"):
        return err(result.get("error") or "Agent invocation failed", module="general", **result)
    return ok(
        f"{result.get('agent_name') or result['agent_id']} handled: {task[:80]}",
        module="general",
        **result,
    )


@register_action(
    "agent_step",
    module="general",
    description="Run a specialist as a mission step (used by the mission worker)",
)
def agent_step(assistant, params: dict, message: str) -> dict:
    """Lets a persistent mission delegate a step to a specialist."""
    from jarvis import specialized_agents as agents

    agent_id = (params.get("agent_id") or "").strip()
    task = (params.get("task") or "").strip()
    if not agent_id or not task:
        return err("agent_step needs agent_id and task", module="general")
    result = agents.invoke(
        agent_id,
        task,
        assistant=assistant,
        action=(params.get("action") or "").strip(),
        params=params.get("params") or {},
    )
    if not result.get("ok"):
        return err(result.get("error") or "agent step failed", module="general", **result)
    return ok(f"{agent_id} completed step", module="general", **result)
