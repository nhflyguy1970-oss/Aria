"""MCP operations — authority, validation, bounds, and truthful envelopes.

The rule that shapes this module: a provider is outside ARIA's trust boundary.
It does not gain authority by describing itself as safe, its output is data
rather than instruction, and every operation is decided by ARIA policy before
the provider is contacted at all.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from typing import Any

from jarvis.computer_use.actions import redact
from jarvis.mcp import client, registry, store
from jarvis.mcp import definitions as defs
from jarvis.skills.contracts import ContractError, validate_payload

log = logging.getLogger("jarvis.mcp")

SUCCESS = "success"
PARTIAL = "partial"
FAILED = "failed"
DENIED = "denied"
UNAVAILABLE = "unavailable"
INVALID = "invalid"
TIMEOUT = "timeout"
CANCELLED = "cancelled"
STATUSES = (SUCCESS, PARTIAL, FAILED, DENIED, UNAVAILABLE, INVALID, TIMEOUT, CANCELLED)


class McpDenied(RuntimeError):
    """ARIA policy refused. Never softened into a failure."""


def _agent(requester: str):
    from jarvis import specialized_agents as agents

    return agents.get(requester) if requester else None


def check_authority(
    defn: defs.ProviderDefinition,
    tool_name: str = "",
    *,
    requester: str = "",
    skill_id: str = "",
    for_execution: bool = True,
    authorized_high_impact: bool = False,
) -> None:
    """Every reason ARIA might refuse, decided before the provider is contacted."""
    if for_execution and not defn.may_execute():
        raise McpDenied(f"{defn.provider_id}: {defn.unavailable_reason()}")
    if not for_execution and not defn.may_discover():
        raise McpDenied(f"{defn.provider_id}: {defn.unavailable_reason()}")

    if tool_name and not defn.permits_tool(tool_name):
        raise McpDenied(f"{defn.provider_id}: tool {tool_name!r} is not permitted")
    if skill_id and not defn.permits_skill(skill_id):
        raise McpDenied(f"{defn.provider_id}: skill {skill_id!r} may not use this provider")

    risk = defn.impact_of(tool_name) if tool_name else defn.impact
    if for_execution and risk == defs.HIGH_IMPACT and not authorized_high_impact:
        raise McpDenied(
            f"{defs.qualified(defn.provider_id, tool_name or '*')} is {risk} and needs "
            "explicit authorization"
        )

    if not requester:
        # Operator context. Provider policy above still applies.
        return

    agent = _agent(requester)
    if agent is None:
        raise McpDenied(f"No such agent: {requester}")
    if not agent.enabled:
        raise McpDenied(f"Agent disabled: {requester}")
    if not defn.permits_agent(requester):
        raise McpDenied(f"{defn.provider_id}: agent {requester} is not permitted")

    gate = defs.MCP_DISCOVER if not for_execution else defn.gate_action(tool_name)
    if not agent.permits(gate):
        raise McpDenied(f"Agent {requester} may not {gate.replace('_', ' ')}")
    # A provider may require ARIA actions; the agent must already hold them.
    for action in defn.required_actions:
        if not agent.permits(action):
            raise McpDenied(
                f"Agent {requester} lacks action {action!r} required by {defn.provider_id}"
            )


def _bound_output(payload: Any, limit: int) -> tuple[Any, bool]:
    """Keep one provider from returning more than ARIA will hold."""
    try:
        encoded = json.dumps(payload, default=str)
    except (TypeError, ValueError):
        return {"error": "provider result is not serialisable"}, True
    if len(encoded) <= limit:
        return payload, False
    if isinstance(payload, dict):
        keep = max(0, limit // 2)
        trimmed = dict(payload)
        if isinstance(trimmed.get("text"), str):
            trimmed["text"] = trimmed["text"][:keep]
        # Content blocks carry the same payload again, so trimming only "text"
        # left the oversized copy in place and the bound did nothing.
        blocks = trimmed.get("content")
        if isinstance(blocks, list):
            trimmed["content"] = [
                {**b, "text": b["text"][:keep]}
                if isinstance(b, dict) and isinstance(b.get("text"), str)
                else b
                for b in blocks
            ]
        if isinstance(trimmed.get("structured"), (dict, list)):
            trimmed["structured"] = {"truncated": True}
        trimmed["truncated"] = True
        again = json.dumps(trimmed, default=str)
        if len(again) <= limit:
            return trimmed, True
    return {"truncated": True, "preview": encoded[: max(0, limit - 128)]}, True


def _envelope(**kw: Any) -> dict[str, Any]:
    env = {
        "provider_id": kw.get("provider_id", ""),
        "provider_name": kw.get("provider_name", ""),
        "transport": kw.get("transport", ""),
        "operation": kw.get("operation", ""),
        "target": kw.get("target", ""),
        "invocation_id": kw.get("invocation_id", ""),
        "requester": kw.get("requester", ""),
        "skill_id": kw.get("skill_id", ""),
        "mission_id": kw.get("mission_id", ""),
        "status": kw.get("status", FAILED),
        "impact": kw.get("impact", defs.READ),
        "arguments": kw.get("arguments", {}),
        "result": kw.get("result"),
        "error": kw.get("error"),
        "error_kind": kw.get("error_kind", ""),
        "truncated": bool(kw.get("truncated")),
        "side_effects": kw.get("side_effects", []),
        "provenance": kw.get("provenance", {}),
        "started_at": kw.get("started_at", time.time()),
        "duration_ms": kw.get("duration_ms", 0.0),
    }
    env["ok"] = env["status"] == SUCCESS
    return env


def _finish(env: dict[str, Any], defn: defs.ProviderDefinition | None) -> dict[str, Any]:
    env["duration_ms"] = round((time.time() - env["started_at"]) * 1000, 2)
    # Redaction happens once, here, so nothing credential-shaped reaches the
    # audit trail, the caller, or a model.
    env["arguments"] = redact(env.get("arguments") or {})
    env["result"] = redact(env.get("result"))
    env["error"] = redact(env.get("error")) if env.get("error") else env.get("error")
    try:
        env["invocation_id"] = store.record_invocation(env)
        if defn is not None:
            store.bump_counters(defn.provider_id, failed=env["status"] != SUCCESS)
            if env["status"] in (UNAVAILABLE, TIMEOUT):
                store.record_health(defn.provider_id, "unreachable", error=env.get("error") or "")
            elif env["status"] == SUCCESS:
                store.record_health(defn.provider_id, "healthy")
    except Exception:  # noqa: BLE001 - audit must not mask the operation's outcome
        log.warning("could not persist MCP invocation", exc_info=True)
    return env


def _prepare(
    provider_id: str,
    operation: str,
    target: str,
    *,
    requester: str,
    skill_id: str,
    mission_id: str,
    arguments: dict[str, Any] | None,
) -> tuple[dict[str, Any], defs.ProviderDefinition | None]:
    env = _envelope(
        provider_id=provider_id,
        operation=operation,
        target=target,
        requester=requester,
        skill_id=skill_id,
        mission_id=mission_id,
        arguments=dict(arguments or {}),
        invocation_id=store.new_id(),
        started_at=time.time(),
    )
    try:
        defn = registry.require(provider_id)
    except registry.ProviderNotFound as exc:
        env.update(status=UNAVAILABLE, error=str(exc), error_kind="unknown_provider")
        return env, None
    env.update(
        provider_name=defn.name,
        transport=defn.transport,
        impact=defn.impact_of(target) if operation == "tool" else defn.impact,
    )
    return env, defn


def _provenance(defn: defs.ProviderDefinition, operation: str, target: str, **extra) -> dict:
    base = {
        "provider": defn.provider_id,
        "provider_name": defn.name,
        "transport": defn.transport,
        "operation": operation,
        "target": target,
        "trust": defn.trust,
        # External content. Never treated as inspected or verified here.
        "content_state": "retrieved_unverified",
    }
    base.update(extra)
    return base


# ------------------------------------------------------------------- discovery


def discover(provider_id: str, *, requester: str = "", refresh: bool = True) -> dict[str, Any]:
    """Handshake with a provider and list what it offers. Grants no execution."""
    env, defn = _prepare(
        provider_id, "discover", "", requester=requester, skill_id="", mission_id="", arguments={}
    )
    if defn is None:
        return _finish(env, None)
    try:
        check_authority(defn, requester=requester, for_execution=False)
    except McpDenied as exc:
        env.update(status=DENIED, error=str(exc), error_kind="permission_denied")
        return _finish(env, defn)

    if not refresh:
        cached = registry.cached_discovery(provider_id)
        if cached:
            env.update(
                status=SUCCESS,
                result=cached,
                provenance=_provenance(defn, "discover", "", cached=True),
            )
            return _finish(env, defn)
    try:
        launch = registry.launch_definition(provider_id)
        snapshot = client.describe(launch)
    except client.McpTimeout as exc:
        env.update(status=TIMEOUT, error=str(exc), error_kind="timeout")
        return _finish(env, defn)
    except client.McpUnavailable as exc:
        env.update(status=UNAVAILABLE, error=str(exc), error_kind="provider_unavailable")
        return _finish(env, defn)

    registry.cache_discovery(provider_id, snapshot)
    env.update(status=SUCCESS, result=snapshot, provenance=_provenance(defn, "discover", ""))
    return _finish(env, defn)


# -------------------------------------------------------------------- invoking


def call_tool(
    provider_id: str,
    tool: str,
    arguments: dict[str, Any] | None = None,
    *,
    requester: str = "",
    skill_id: str = "",
    mission_id: str = "",
    authorized_high_impact: bool = False,
    cancel_check: Callable[[], bool] | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    env, defn = _prepare(
        provider_id,
        "tool",
        tool,
        requester=requester,
        skill_id=skill_id,
        mission_id=mission_id,
        arguments=arguments,
    )
    if defn is None:
        return _finish(env, None)
    try:
        check_authority(
            defn,
            tool,
            requester=requester,
            skill_id=skill_id,
            authorized_high_impact=authorized_high_impact,
        )
    except McpDenied as exc:
        env.update(status=DENIED, error=str(exc), error_kind="permission_denied")
        return _finish(env, defn)

    if cancel_check is not None and cancel_check():
        env.update(status=CANCELLED, error="cancelled before invocation", error_kind="cancelled")
        return _finish(env, defn)

    payload = dict(arguments or {})
    try:
        _check_input_size(payload)
        schema = (registry.find_tool(provider_id, tool) or {}).get("input_schema") or {}
        if schema:
            # Model-generated arguments are validated against the provider's own
            # schema before anything is sent.
            validate_payload(payload, schema, label="arguments")
    except ContractError as exc:
        env.update(status=INVALID, error=str(exc), error_kind="schema")
        return _finish(env, defn)
    except ValueError as exc:
        env.update(status=INVALID, error=str(exc), error_kind="input_size")
        return _finish(env, defn)

    try:
        launch = registry.launch_definition(provider_id)
        raw = client.call_tool(launch, tool, payload, timeout=timeout, cancel_check=cancel_check)
    except client.McpCancelled as exc:
        env.update(
            status=CANCELLED,
            error=str(exc),
            error_kind="cancelled",
            provenance=_provenance(defn, "tool", tool, remote_state="unknown_after_cancel"),
        )
        return _finish(env, defn)
    except client.McpTimeout as exc:
        # ARIA stopped waiting. Whether the provider stopped is unknown, and is
        # reported as such rather than claimed as a cancellation.
        env.update(
            status=TIMEOUT,
            error=str(exc),
            error_kind="timeout",
            provenance=_provenance(defn, "tool", tool, remote_state="unknown_after_timeout"),
        )
        return _finish(env, defn)
    except client.McpUnavailable as exc:
        env.update(
            status=UNAVAILABLE,
            error=str(exc),
            error_kind="provider_unavailable",
            provenance=_provenance(defn, "tool", tool),
        )
        return _finish(env, defn)

    bounded, truncated = _bound_output(raw, defn.max_output_bytes)
    if raw.get("is_error"):
        env.update(
            status=FAILED,
            error=(raw.get("text") or "provider reported an error")[:2000],
            error_kind="tool_error",
            result=None,
            truncated=truncated,
            provenance=_provenance(defn, "tool", tool),
        )
        return _finish(env, defn)

    if cancel_check is not None and cancel_check():
        env.update(
            status=CANCELLED,
            error="cancelled after invocation completed",
            error_kind="cancelled",
            provenance=_provenance(defn, "tool", tool, remote_state="completed"),
        )
        return _finish(env, defn)

    env.update(
        status=SUCCESS,
        result=bounded,
        truncated=truncated,
        provenance=_provenance(defn, "tool", tool),
    )
    return _finish(env, defn)


def read_resource(
    provider_id: str,
    uri: str,
    *,
    requester: str = "",
    skill_id: str = "",
    mission_id: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    env, defn = _prepare(
        provider_id,
        "resource",
        uri,
        requester=requester,
        skill_id=skill_id,
        mission_id=mission_id,
        arguments={"uri": uri},
    )
    if defn is None:
        return _finish(env, None)
    try:
        check_authority(defn, requester=requester, skill_id=skill_id)
    except McpDenied as exc:
        env.update(status=DENIED, error=str(exc), error_kind="permission_denied")
        return _finish(env, defn)
    try:
        launch = registry.launch_definition(provider_id)
        raw = client.read_resource(launch, uri, timeout=timeout)
    except client.McpTimeout as exc:
        env.update(status=TIMEOUT, error=str(exc), error_kind="timeout")
        return _finish(env, defn)
    except client.McpUnavailable as exc:
        env.update(status=UNAVAILABLE, error=str(exc), error_kind="provider_unavailable")
        return _finish(env, defn)

    bounded, truncated = _bound_output(raw, defn.max_output_bytes)
    env.update(
        status=SUCCESS,
        result=bounded,
        truncated=truncated,
        provenance=_provenance(defn, "resource", uri, uri=uri),
    )
    return _finish(env, defn)


def get_prompt(
    provider_id: str,
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    requester: str = "",
    skill_id: str = "",
    timeout: float | None = None,
) -> dict[str, Any]:
    """Retrieve a provider prompt as content. It is never executed here."""
    env, defn = _prepare(
        provider_id,
        "prompt",
        name,
        requester=requester,
        skill_id=skill_id,
        mission_id="",
        arguments=arguments,
    )
    if defn is None:
        return _finish(env, None)
    try:
        check_authority(defn, requester=requester, skill_id=skill_id, for_execution=False)
    except McpDenied as exc:
        env.update(status=DENIED, error=str(exc), error_kind="permission_denied")
        return _finish(env, defn)
    try:
        launch = registry.launch_definition(provider_id)
        raw = client.get_prompt(launch, name, arguments, timeout=timeout)
    except client.McpTimeout as exc:
        env.update(status=TIMEOUT, error=str(exc), error_kind="timeout")
        return _finish(env, defn)
    except client.McpUnavailable as exc:
        env.update(status=UNAVAILABLE, error=str(exc), error_kind="provider_unavailable")
        return _finish(env, defn)

    bounded, truncated = _bound_output(raw, defn.max_output_bytes)
    env.update(
        status=SUCCESS,
        result=bounded,
        truncated=truncated,
        provenance=_provenance(defn, "prompt", name, prompt_state="content_not_executed"),
    )
    return _finish(env, defn)


def _check_input_size(payload: dict[str, Any]) -> None:
    try:
        size = len(json.dumps(payload, default=str))
    except (TypeError, ValueError) as exc:
        raise ValueError("arguments are not serialisable") from exc
    if size > defs.BOUNDS["max_input_bytes"]:
        raise ValueError(
            f"arguments exceed max_input_bytes ({size} > {defs.BOUNDS['max_input_bytes']})"
        )


def health(provider_id: str) -> dict[str, Any]:
    """Observable provider state, with no secret values in it."""
    from jarvis.mcp import secrets as mcp_secrets

    defn = registry.get(provider_id)
    row = store.get_provider(provider_id) or {}
    snapshot = registry.cached_discovery(provider_id) or {}
    return {
        "provider_id": provider_id,
        "known": defn is not None,
        "config": defn.to_dict() if defn else {},
        "env_keys": mcp_secrets.env_keys(provider_id),
        "trust": defn.trust if defn else (row.get("trust") or "unknown"),
        "enabled": defn.enabled if defn else bool(row.get("enabled")),
        "health": row.get("health") or "unknown",
        "last_error": row.get("last_error") or "",
        "last_seen": row.get("last_seen"),
        "invocations": row.get("invocations") or 0,
        "failures": row.get("failures") or 0,
        "capabilities": snapshot.get("capabilities") or {},
        "server_info": snapshot.get("server_info") or {},
        "tool_count": len(snapshot.get("tools") or []),
        "resource_count": len(snapshot.get("resources") or []),
        "prompt_count": len(snapshot.get("prompts") or []),
        "may_discover": defn.may_discover() if defn else False,
        "may_execute": defn.may_execute() if defn else False,
        "unavailable_reason": defn.unavailable_reason() if defn else "provider is not registered",
    }
