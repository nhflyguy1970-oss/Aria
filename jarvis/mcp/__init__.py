"""ARIA's MCP client ecosystem — external tools, resources and prompts.

ARIA already speaks MCP as a *server* (jarvis.jarvis_mcp). This package is the
client half: discovering, configuring and safely using external MCP providers.
The protocol comes from the official `mcp` SDK; ARIA supplies the trust model,
the permission enforcement, the bounds and the audit trail.
"""

from jarvis.mcp.client import McpProtocolError, McpTimeout, McpUnavailable
from jarvis.mcp.definitions import (
    ALLOWED_COMMANDS,
    BOUNDS,
    CONFIGURED,
    DISABLED,
    HIGH_IMPACT,
    HTTP,
    LOW_IMPACT,
    MCP_DISCOVER,
    MCP_HIGH_IMPACT_GATE,
    MCP_INVOKE,
    MODIFY,
    READ,
    SSE,
    STDIO,
    SUPPORTED_TRANSPORTS,
    TRANSPORTS,
    TRUST_LEVELS,
    TRUSTED,
    UNTRUSTED,
    ProviderDefinition,
    ProviderDefinitionError,
    qualified,
    split_qualified,
    validate,
)
from jarvis.mcp.definitions import (
    UNAVAILABLE as TRUST_UNAVAILABLE,
)
from jarvis.mcp.engine import (
    CANCELLED,
    DENIED,
    FAILED,
    INVALID,
    PARTIAL,
    STATUSES,
    SUCCESS,
    TIMEOUT,
    UNAVAILABLE,
    McpDenied,
    call_tool,
    check_authority,
    discover,
    get_prompt,
    health,
    read_resource,
)
from jarvis.mcp.evidence_bridge import record_resource_evidence
from jarvis.mcp.registry import (
    ProviderNotFound,
    ProviderRegistryError,
    cached_discovery,
    find_tool,
    get,
    list_providers,
    load_persisted,
    qualified_tools,
    register,
    require,
    reset,
    set_enabled,
    set_trust,
    tools_for,
    unregister,
)
from jarvis.mcp.skills_bridge import load_mcp_skills
from jarvis.mcp.store import history

_skills_loaded = False


def ensure_mcp_skills_loaded() -> None:
    """Register the MCP skills, checking they are actually still there.

    A flag alone is not enough: the skill registry can be reset independently,
    and a stale flag then leaves the MCP skills silently unavailable.
    """
    global _skills_loaded
    from jarvis.skills import registry as skill_registry

    if _skills_loaded and skill_registry.get("mcp_tool_call"):
        return
    load_mcp_skills(replace=True)
    # Provider configuration is durable, but nothing restored it into a fresh
    # process, so a configured provider silently vanished on every restart.
    try:
        load_persisted()
    except Exception:  # noqa: BLE001 - a bad stored row must not block the layer
        import logging

        logging.getLogger("jarvis.mcp").warning("could not load persisted providers", exc_info=True)
    _skills_loaded = True


__all__ = [
    "ALLOWED_COMMANDS",
    "BOUNDS",
    "CANCELLED",
    "CONFIGURED",
    "DENIED",
    "DISABLED",
    "FAILED",
    "HIGH_IMPACT",
    "HTTP",
    "INVALID",
    "LOW_IMPACT",
    "MCP_DISCOVER",
    "MCP_HIGH_IMPACT_GATE",
    "MCP_INVOKE",
    "MODIFY",
    "McpDenied",
    "McpProtocolError",
    "McpTimeout",
    "McpUnavailable",
    "PARTIAL",
    "ProviderDefinition",
    "ProviderDefinitionError",
    "ProviderNotFound",
    "ProviderRegistryError",
    "READ",
    "SSE",
    "STDIO",
    "STATUSES",
    "SUCCESS",
    "SUPPORTED_TRANSPORTS",
    "TIMEOUT",
    "TRANSPORTS",
    "TRUSTED",
    "TRUST_LEVELS",
    "TRUST_UNAVAILABLE",
    "UNAVAILABLE",
    "UNTRUSTED",
    "cached_discovery",
    "call_tool",
    "check_authority",
    "discover",
    "ensure_mcp_skills_loaded",
    "find_tool",
    "get",
    "get_prompt",
    "health",
    "history",
    "list_providers",
    "load_mcp_skills",
    "load_persisted",
    "qualified",
    "qualified_tools",
    "read_resource",
    "record_resource_evidence",
    "register",
    "require",
    "reset",
    "set_enabled",
    "set_trust",
    "split_qualified",
    "tools_for",
    "unregister",
    "validate",
]
