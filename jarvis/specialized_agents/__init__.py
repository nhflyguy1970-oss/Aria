"""Specialized agents — declarative expert roles ARIA can discover and invoke.

Layered on existing ARIA infrastructure: actions come from the action registry,
models from jarvis.config.MODELS, persistence and long-running execution from
the mission system, and research from the deep research engine.
"""

from jarvis.specialized_agents.definitions import (
    BUILTIN_AGENTS,
    FALLBACK_AGENT_ID,
    SCHEMA_VERSION,
    AgentDefinition,
    AgentDefinitionError,
    validate,
)
from jarvis.specialized_agents.invoke import (
    ContractError,
    PermissionDenied,
    check_permission,
    invoke,
    resolve_model,
    select_and_invoke,
)
from jarvis.specialized_agents.registry import (
    capabilities,
    detect_capabilities,
    find_by_capability,
    get,
    list_agents,
    register,
    reset,
    select,
    set_enabled,
    unregister,
)

__all__ = [
    "BUILTIN_AGENTS",
    "FALLBACK_AGENT_ID",
    "SCHEMA_VERSION",
    "AgentDefinition",
    "AgentDefinitionError",
    "ContractError",
    "PermissionDenied",
    "capabilities",
    "check_permission",
    "detect_capabilities",
    "find_by_capability",
    "get",
    "invoke",
    "list_agents",
    "register",
    "reset",
    "resolve_model",
    "select",
    "select_and_invoke",
    "set_enabled",
    "unregister",
    "validate",
]
