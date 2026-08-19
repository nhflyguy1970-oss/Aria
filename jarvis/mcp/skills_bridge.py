"""Skills that reach external MCP providers.

The permission chain stays intact: the skill declares the MCP gate action, the
executor checks the agent holds it, and the MCP engine independently re-checks
the provider's own policy with the same requester. A skill cannot widen what
its caller may do, and MCP cannot become a way around that.
"""

from __future__ import annotations

from typing import Any

from jarvis.mcp import definitions as mcp_defs
from jarvis.mcp import engine as mcp_engine
from jarvis.skills import registry as skill_registry
from jarvis.skills.definitions import LOW_IMPACT, READ, RESEARCH, SkillDefinition
from jarvis.skills.executor import SkillContext, SkillDenied

MCP_TOOL_SKILL = SkillDefinition(
    skill_id="mcp_tool_call",
    name="Call MCP Tool",
    description="Invoke an authorized tool on a trusted MCP provider and return its result.",
    purpose="Give skills and agents one governed route to external tools.",
    version="1.0.0",
    category=RESEARCH,
    tags=("mcp", "tool", "external"),
    capabilities=("external_tools", "mcp"),
    required_actions=(),
    required_permissions=(mcp_defs.MCP_INVOKE,),
    impact=LOW_IMPACT,
    input_schema={
        "type": "object",
        "properties": {
            "provider_id": {"type": "string"},
            "tool": {"type": "string"},
            "arguments": {"type": "object"},
        },
        "required": ["provider_id", "tool"],
    },
    output_schema={"type": "object", "properties": {"status": {"type": "string"}}},
    side_effects=("runs an operation on an external provider",),
)


def _mcp_tool_call(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    ctx.checkpoint()
    envelope = mcp_engine.call_tool(
        params["provider_id"],
        params["tool"],
        params.get("arguments") or {},
        requester=ctx.requester,
        skill_id=ctx.definition.skill_id,
        mission_id=ctx.mission_id,
        cancel_check=ctx.cancel_check,
    )
    if envelope["status"] == mcp_engine.DENIED:
        # Denial propagates; a skill must not convert it into a soft failure.
        raise SkillDenied(envelope["error"] or "MCP tool denied")
    if envelope["status"] != mcp_engine.SUCCESS:
        raise RuntimeError(
            f"MCP tool {envelope['provider_id']}:{envelope['target']} "
            f"{envelope['status']}: {envelope.get('error')}"
        )
    ctx.record_side_effect(f"mcp tool {envelope['provider_id']}:{envelope['target']}")
    return {
        "status": envelope["status"],
        "provider_id": envelope["provider_id"],
        "tool": envelope["target"],
        "result": envelope["result"],
        "truncated": envelope["truncated"],
        "provenance": envelope["provenance"],
    }


MCP_RESOURCE_SKILL = SkillDefinition(
    skill_id="mcp_fetch_resource",
    name="Fetch MCP Resource",
    description="Retrieve a resource from a trusted MCP provider, preserving provenance.",
    purpose="Bring external reference material in as evidence-grade, unverified content.",
    version="1.0.0",
    category=RESEARCH,
    tags=("mcp", "resource", "external"),
    capabilities=("external_tools", "mcp", "research"),
    required_actions=(),
    required_permissions=(mcp_defs.MCP_INVOKE,),
    impact=READ,
    input_schema={
        "type": "object",
        "properties": {"provider_id": {"type": "string"}, "uri": {"type": "string"}},
        "required": ["provider_id", "uri"],
    },
    output_schema={"type": "object", "properties": {"uri": {"type": "string"}}},
)


def _mcp_fetch_resource(ctx: SkillContext, params: dict[str, Any]) -> dict[str, Any]:
    ctx.checkpoint()
    envelope = mcp_engine.read_resource(
        params["provider_id"],
        params["uri"],
        requester=ctx.requester,
        skill_id=ctx.definition.skill_id,
        mission_id=ctx.mission_id,
    )
    if envelope["status"] == mcp_engine.DENIED:
        raise SkillDenied(envelope["error"] or "MCP resource denied")
    if envelope["status"] != mcp_engine.SUCCESS:
        raise RuntimeError(
            f"MCP resource {envelope['provider_id']} {envelope['status']}: {envelope.get('error')}"
        )
    contents = (envelope["result"] or {}).get("contents") or []
    text = "\n".join(c.get("text") or "" for c in contents).strip()
    return {
        "uri": params["uri"],
        "provider_id": envelope["provider_id"],
        "text": text,
        # Retrieved is not verified. Anything downstream must treat it as a
        # claim from an external party until the evidence layer says otherwise.
        "verification": "none",
        "provenance": envelope["provenance"],
    }


CATALOG = (
    (MCP_TOOL_SKILL, _mcp_tool_call),
    (MCP_RESOURCE_SKILL, _mcp_fetch_resource),
)


def load_mcp_skills(*, replace: bool = True) -> list[str]:
    loaded = []
    for defn, impl in CATALOG:
        skill_registry.register(defn, impl, replace=replace)
        loaded.append(defn.ref())
    return loaded
