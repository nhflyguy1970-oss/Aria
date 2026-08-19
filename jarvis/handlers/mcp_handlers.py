"""MCP ecosystem handlers — provider configuration, discovery, invocation, audit.

Discovery is deliberately separate from invocation: listing what a provider
offers grants no authority to run any of it.
"""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _mcp():
    from jarvis import mcp

    mcp.ensure_mcp_skills_loaded()
    return mcp


@register_action(
    "mcp_provider_list", module="general", description="List configured MCP providers", info=True
)
def mcp_provider_list(assistant, params: dict, message: str) -> dict:
    mcp = _mcp()
    providers = mcp.list_providers()
    if not providers:
        return ok("No MCP providers configured.", module="general", providers=[])
    rows = [mcp.health(p.provider_id) for p in providers]
    lines = [
        f"- `{r['provider_id']}` [{r['trust']}/{r['health']}] {r['config'].get('name', '')}"
        + (f" — {r['unavailable_reason']}" if r["unavailable_reason"] else "")
        for r in rows
    ]
    return ok("\n".join(lines), module="general", providers=rows)


@register_action(
    "mcp_provider_status", module="general", description="Show one MCP provider", info=True
)
def mcp_provider_status(assistant, params: dict, message: str) -> dict:
    mcp = _mcp()
    provider_id = (params.get("provider_id") or "").strip()
    if not provider_id:
        return err("Which provider? Pass provider_id.", module="general")
    detail = mcp.health(provider_id)
    if not detail["known"]:
        return err(
            f"No such MCP provider: {provider_id}",
            module="general",
            error_kind="unknown_provider",
            provider=detail,
        )
    lines = [
        f"**{provider_id}** [{detail['trust']}] transport={detail['config'].get('transport')}",
        f"health={detail['health']} · invocations={detail['invocations']} "
        f"· failures={detail['failures']}",
        f"tools={detail['tool_count']} resources={detail['resource_count']} "
        f"prompts={detail['prompt_count']}",
    ]
    if detail["unavailable_reason"]:
        lines.append(f"Unavailable: {detail['unavailable_reason']}")
    if detail["last_error"]:
        lines.append(f"Last error: {detail['last_error'][:200]}")
    return ok("\n".join(lines), module="general", provider=detail)


@register_action(
    "mcp_discover",
    module="general",
    description="Discover an MCP provider's tools, resources and prompts",
    info=True,
)
def mcp_discover(assistant, params: dict, message: str) -> dict:
    mcp = _mcp()
    provider_id = (params.get("provider_id") or "").strip()
    if not provider_id:
        return err("Which provider? Pass provider_id.", module="general")
    envelope = mcp.discover(
        provider_id,
        requester=(params.get("requester") or params.get("agent_id") or "").strip(),
        refresh=bool(params.get("refresh", True)),
    )
    if envelope["status"] != mcp.SUCCESS:
        return err(
            envelope.get("error") or f"discovery {envelope['status']}",
            module="general",
            error_kind=envelope["error_kind"],
            envelope=envelope,
        )
    snapshot = envelope["result"]
    lines = [
        f"**{provider_id}** {snapshot['server_info'].get('name', '')} "
        f"{snapshot['server_info'].get('version', '')}",
        f"tools: {', '.join(t['name'] for t in snapshot['tools']) or '—'}",
        f"resources: {len(snapshot['resources'])} · prompts: {len(snapshot['prompts'])}",
    ]
    return ok("\n".join(lines), module="general", envelope=envelope, discovery=snapshot)


@register_action(
    "mcp_tools",
    module="general",
    description="List known MCP tools, provider-qualified",
    info=True,
)
def mcp_tools(assistant, params: dict, message: str) -> dict:
    mcp = _mcp()
    tools = mcp.qualified_tools()
    provider_id = (params.get("provider_id") or "").strip()
    if provider_id:
        tools = [t for t in tools if t["provider_id"] == provider_id]
    if not tools:
        return ok("No MCP tools discovered yet.", module="general", tools=[])
    lines = [
        f"- `{t['qualified_name']}` [{t['impact']}]"
        + ("" if t["available"] else f" (unavailable: {t['unavailable_reason']})")
        for t in tools
    ]
    return ok("\n".join(lines), module="general", tools=tools)


@register_action("mcp_invoke", module="general", description="Invoke an MCP tool")
def mcp_invoke(assistant, params: dict, message: str) -> dict:
    mcp = _mcp()
    provider_id = (params.get("provider_id") or "").strip()
    tool = (params.get("tool") or "").strip()
    qualified_name = (params.get("qualified_name") or "").strip()
    if qualified_name and not (provider_id and tool):
        try:
            provider_id, tool = mcp.split_qualified(qualified_name)
        except mcp.ProviderDefinitionError as exc:
            return err(str(exc), module="general", error_kind="invalid_name")
    if not provider_id or not tool:
        return err("mcp_invoke needs provider_id and tool.", module="general")
    arguments = params.get("arguments")
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        return err("arguments must be an object.", module="general", error_kind="schema")

    envelope = mcp.call_tool(
        provider_id,
        tool,
        arguments,
        requester=(params.get("requester") or params.get("agent_id") or "").strip(),
        skill_id=(params.get("skill_id") or "").strip(),
        mission_id=(params.get("mission_id") or "").strip(),
        authorized_high_impact=bool(params.get("authorized_high_impact")),
    )
    text = f"`{provider_id}:{tool}` → {envelope['status']} ({envelope['duration_ms']}ms)"
    if envelope["status"] != mcp.SUCCESS:
        return err(
            envelope.get("error") or text,
            module="general",
            error_kind=envelope["error_kind"] or envelope["status"],
            envelope=envelope,
        )
    return ok(text, module="general", envelope=envelope, result=envelope["result"])


@register_action(
    "mcp_invoke_high_impact",
    module="general",
    description="Permission gate for high-impact MCP tools (never called directly)",
)
def mcp_invoke_high_impact(assistant, params: dict, message: str) -> dict:
    return err(
        "mcp_invoke_high_impact is a permission gate, not an operation. "
        "Use mcp_invoke with authorized_high_impact.",
        module="general",
        error_kind="gate_only",
    )


@register_action("mcp_resource", module="general", description="Retrieve an MCP resource")
def mcp_resource(assistant, params: dict, message: str) -> dict:
    mcp = _mcp()
    provider_id = (params.get("provider_id") or "").strip()
    uri = (params.get("uri") or "").strip()
    if not provider_id or not uri:
        return err("mcp_resource needs provider_id and uri.", module="general")
    envelope = mcp.read_resource(
        provider_id,
        uri,
        requester=(params.get("requester") or params.get("agent_id") or "").strip(),
        skill_id=(params.get("skill_id") or "").strip(),
        mission_id=(params.get("mission_id") or "").strip(),
    )
    if envelope["status"] != mcp.SUCCESS:
        return err(
            envelope.get("error") or f"resource {envelope['status']}",
            module="general",
            error_kind=envelope["error_kind"] or envelope["status"],
            envelope=envelope,
        )
    return ok(f"retrieved {uri}", module="general", envelope=envelope, result=envelope["result"])


@register_action(
    "mcp_prompt",
    module="general",
    description="Retrieve an MCP provider prompt as content",
    info=True,
)
def mcp_prompt(assistant, params: dict, message: str) -> dict:
    mcp = _mcp()
    provider_id = (params.get("provider_id") or "").strip()
    name = (params.get("name") or "").strip()
    if not provider_id or not name:
        return err("mcp_prompt needs provider_id and name.", module="general")
    envelope = mcp.get_prompt(
        provider_id,
        name,
        params.get("arguments") or {},
        requester=(params.get("requester") or params.get("agent_id") or "").strip(),
        skill_id=(params.get("skill_id") or "").strip(),
    )
    if envelope["status"] != mcp.SUCCESS:
        return err(
            envelope.get("error") or f"prompt {envelope['status']}",
            module="general",
            error_kind=envelope["error_kind"] or envelope["status"],
            envelope=envelope,
        )
    return ok(
        f"prompt `{name}` retrieved as content (not executed)",
        module="general",
        envelope=envelope,
        prompt=envelope["result"],
    )


@register_action("mcp_set_trust", module="general", description="Set an MCP provider's trust level")
def mcp_set_trust(assistant, params: dict, message: str) -> dict:
    mcp = _mcp()
    provider_id = (params.get("provider_id") or "").strip()
    trust = (params.get("trust") or "").strip()
    if not provider_id or not trust:
        return err("mcp_set_trust needs provider_id and trust.", module="general")
    try:
        defn = mcp.set_trust(provider_id, trust)
    except mcp.ProviderNotFound as exc:
        return err(str(exc), module="general", error_kind="unknown_provider")
    except mcp.ProviderRegistryError as exc:
        return err(str(exc), module="general", error_kind="invalid_trust")
    return ok(
        f"`{provider_id}` trust set to {defn.trust}.", module="general", provider=defn.to_dict()
    )


@register_action(
    "mcp_history", module="general", description="Show MCP invocation history", info=True
)
def mcp_history(assistant, params: dict, message: str) -> dict:
    mcp = _mcp()
    invocation_id = (params.get("invocation_id") or "").strip()
    if invocation_id:
        from jarvis.mcp import store as mcp_store

        record = mcp_store.get_invocation(invocation_id)
        if not record:
            return err(f"No such invocation: {invocation_id}", module="general")
        return ok(
            f"`{record['provider_id']}:{record['target']}` — {record['status']}",
            module="general",
            invocation=record,
        )
    rows = mcp.history(
        provider_id=(params.get("provider_id") or "").strip(),
        requester=(params.get("requester") or "").strip(),
        limit=int(params.get("limit") or 20),
    )
    if not rows:
        return ok("No MCP invocations recorded.", module="general", invocations=[])
    lines = [
        f"- `{r['id']}` {r['provider_id']}:{r['target'] or r['operation']} [{r['status']}]"
        f" by {r['requester'] or 'system'}"
        for r in rows
    ]
    return ok("\n".join(lines), module="general", invocations=rows)


@register_action(
    "mcp_step",
    module="general",
    description="Run an MCP operation as a mission step (used by the mission worker)",
)
def mcp_step(assistant, params: dict, message: str) -> dict:
    """Mission-backed MCP work; honours mission cancellation at each boundary."""
    mcp = _mcp()
    provider_id = (params.get("provider_id") or "").strip()
    operation = (params.get("operation") or "tool").strip()
    mission_id = (params.get("mission_id") or "").strip()
    if not provider_id:
        return err("mcp_step needs provider_id.", module="general")

    cancel_check = None
    if mission_id:
        from jarvis.missions import store as mstore

        def cancel_check() -> bool:  # noqa: E306
            return mstore.cancel_requested(mission_id)

    if operation == "resource":
        envelope = mcp.read_resource(
            provider_id,
            (params.get("uri") or "").strip(),
            requester=(params.get("requester") or "").strip(),
            skill_id=(params.get("skill_id") or "").strip(),
            mission_id=mission_id,
        )
    else:
        envelope = mcp.call_tool(
            provider_id,
            (params.get("tool") or "").strip(),
            params.get("arguments") or {},
            requester=(params.get("requester") or "").strip(),
            skill_id=(params.get("skill_id") or "").strip(),
            mission_id=mission_id,
            cancel_check=cancel_check,
            authorized_high_impact=bool(params.get("authorized_high_impact")),
        )
    if envelope["status"] != mcp.SUCCESS:
        # The mission runner treats a returned dict as a completed step, so a
        # failing provider call has to raise or the mission would report success
        # for work that did not happen. Transient provider problems use the
        # engine's own retry path; a refusal or a real tool error does not,
        # because retrying cannot change the answer.
        from jarvis.missions.engine import MissionCancelled, RetryableError

        detail = f"mcp {operation} {envelope['status']}: {envelope.get('error') or 'no detail'}"
        if envelope["status"] == mcp.CANCELLED:
            # Cancelled is not failed: let the mission record it as cancelled.
            raise MissionCancelled(detail)
        if envelope["status"] in (mcp.UNAVAILABLE, mcp.TIMEOUT):
            raise RetryableError(detail)
        raise RuntimeError(detail)
    return ok(f"mcp {operation} ok", module="general", envelope=envelope)


@register_action(
    "mcp_provider_register",
    module="general",
    description="Register or update an MCP provider configuration",
)
def mcp_provider_register(assistant, params: dict, message: str) -> dict:
    """Configuration, not use.

    A provider registered here starts untrusted and can do nothing until an
    operator raises its trust and names the agents it accepts. Environment
    values go to the secrets file, never to the configuration record.
    """
    mcp = _mcp()
    from jarvis.mcp import definitions as mcp_defs
    from jarvis.mcp import secrets as mcp_secrets

    provider_id = (params.get("provider_id") or "").strip()
    if not provider_id:
        return err("mcp_provider_register needs provider_id.", module="general")

    command = params.get("command") or []
    if isinstance(command, str):
        # An argv list is required; a shell string is never split and run.
        return err(
            "command must be a list of arguments, not a shell string.",
            module="general",
            error_kind="command_form",
        )
    tool_impacts = params.get("tool_impacts") or {}
    if not isinstance(tool_impacts, dict):
        return err("tool_impacts must be an object.", module="general", error_kind="schema")

    try:
        defn = mcp_defs.ProviderDefinition(
            provider_id=provider_id,
            name=(params.get("name") or provider_id).strip(),
            description=(params.get("description") or "").strip(),
            transport=(params.get("transport") or mcp_defs.STDIO).strip(),
            command=tuple(str(c) for c in command),
            cwd=(params.get("cwd") or "").strip(),
            url=(params.get("url") or "").strip(),
            allow_local=bool(params.get("allow_local")),
            # Never trusted on arrival, whatever the caller asks for.
            trust=mcp_defs.UNTRUSTED,
            impact=(params.get("impact") or mcp_defs.READ).strip(),
            tool_impacts=tuple(sorted((str(k), str(v)) for k, v in tool_impacts.items())),
            allowed_agents=tuple(params.get("allowed_agents") or ()),
            denied_agents=tuple(params.get("denied_agents") or ()),
            allowed_skills=tuple(params.get("allowed_skills") or ()),
            allowed_tools=tuple(params.get("allowed_tools") or ()),
            denied_tools=tuple(params.get("denied_tools") or ()),
            required_actions=tuple(params.get("required_actions") or ()),
            timeout_s=float(params.get("timeout_s") or 30.0),
        )
        mcp.register(defn, replace=True, persist=True)
    except mcp.ProviderDefinitionError as exc:
        return err(str(exc), module="general", error_kind="invalid_provider")
    except (TypeError, ValueError) as exc:
        return err(str(exc), module="general", error_kind="invalid_provider")

    env = params.get("env")
    env_keys: list[str] = []
    if isinstance(env, dict) and env:
        env_keys = mcp_secrets.set_provider_env(
            provider_id, {str(k): str(v) for k, v in env.items()}
        )

    return ok(
        f"Provider `{provider_id}` registered as {defn.trust}. "
        "Raise its trust explicitly before it can execute anything.",
        module="general",
        provider=defn.to_dict(),
        env_keys=env_keys,
    )


@register_action(
    "mcp_provider_remove", module="general", description="Remove an MCP provider configuration"
)
def mcp_provider_remove(assistant, params: dict, message: str) -> dict:
    mcp = _mcp()
    from jarvis.mcp import secrets as mcp_secrets

    provider_id = (params.get("provider_id") or "").strip()
    if not provider_id:
        return err("mcp_provider_remove needs provider_id.", module="general")
    removed = mcp.unregister(provider_id)
    mcp_secrets.clear_provider_env(provider_id)
    if not removed:
        return err(
            f"No such MCP provider: {provider_id}", module="general", error_kind="unknown_provider"
        )
    return ok(f"Provider `{provider_id}` removed.", module="general")
