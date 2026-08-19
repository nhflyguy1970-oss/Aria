"""MCP provider definitions — the configuration contract for an external tool source.

ARIA already exposes itself *as* an MCP server through jarvis.jarvis_mcp. This
package is the other direction: ARIA as a client, consuming external providers.
The protocol itself comes from the official `mcp` SDK; nothing here reimplements
it.

A provider is an authority boundary. Everything it says about itself — its tool
descriptions, its claimed safety, its prompts — is untrusted external data.
ARIA's own policy decides what may actually run.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Risk uses the same scale as skills, so one vocabulary covers the whole stack.
from jarvis.skills.definitions import (
    HIGH_IMPACT,
    IMPACTS,
    LOW_IMPACT,
    MODIFY,
    READ,
    impact_rank,
    max_impact,
)

SCHEMA_VERSION = 1

# Transports. Only those the installed SDK actually provides are usable; the
# rest are named so an attempt reports "unsupported" rather than failing oddly.
STDIO = "stdio"
HTTP = "http"
SSE = "sse"
WEBSOCKET = "websocket"
TRANSPORTS = (STDIO, HTTP, SSE, WEBSOCKET)
SUPPORTED_TRANSPORTS = (STDIO, HTTP, SSE)

# Trust. A newly discovered provider is never trusted by default.
TRUSTED = "trusted"
CONFIGURED = "configured"
UNTRUSTED = "untrusted"
DISABLED = "disabled"
UNAVAILABLE = "unavailable"
TRUST_LEVELS = (TRUSTED, CONFIGURED, UNTRUSTED, DISABLED, UNAVAILABLE)
# Only these may execute anything. "configured" can discover but not invoke.
EXECUTABLE_TRUST = (TRUSTED,)
DISCOVERABLE_TRUST = (TRUSTED, CONFIGURED)

# Registry gate actions, so MCP authority lives in ARIA's one permission system.
MCP_DISCOVER = "mcp_discover"
MCP_INVOKE = "mcp_invoke"
MCP_HIGH_IMPACT_GATE = "mcp_invoke_high_impact"

_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
_TOOL_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,128}$")

# Executables a stdio provider may be launched with. An argv[0] outside this
# list is refused: a provider definition must never become a way to run an
# arbitrary program.
ALLOWED_COMMANDS = (
    "python",
    "python3",
    "node",
    "npx",
    "uvx",
    "deno",
    "bun",
)

BOUNDS = {
    "connect_timeout_s": 20.0,
    "init_timeout_s": 20.0,
    "call_timeout_s": 30.0,
    "resource_timeout_s": 30.0,
    "max_output_bytes": 262144,
    "max_input_bytes": 65536,
    "process_lifetime_s": 120.0,
    "max_concurrent": 4,
    "max_retries": 2,
    "max_reconnects": 2,
}


class ProviderDefinitionError(ValueError):
    """A provider configuration that must never be registered."""


def qualified(provider_id: str, tool_name: str) -> str:
    """Provider-qualified identity, so two providers cannot shadow each other."""
    return f"{provider_id}:{tool_name}"


def split_qualified(name: str) -> tuple[str, str]:
    provider_id, _, tool = (name or "").partition(":")
    if not provider_id or not tool:
        raise ProviderDefinitionError(
            f"Expected a provider-qualified name like 'provider:tool', got {name!r}"
        )
    return provider_id, tool


@dataclass(frozen=True)
class ProviderDefinition:
    """Immutable provider configuration.

    Frozen so a live session cannot rewrite the trust level, command or
    permissions of the provider it is talking to.
    """

    provider_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    transport: str = STDIO
    # stdio
    command: tuple[str, ...] = ()
    cwd: str = ""
    env: tuple[tuple[str, str], ...] = ()
    # network
    url: str = ""
    allow_local: bool = False
    # policy
    trust: str = UNTRUSTED
    enabled: bool = True
    impact: str = READ
    tool_impacts: tuple[tuple[str, str], ...] = ()
    allowed_agents: tuple[str, ...] = ()
    denied_agents: tuple[str, ...] = ()
    allowed_skills: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    denied_tools: tuple[str, ...] = ()
    required_actions: tuple[str, ...] = ()
    timeout_s: float = 30.0
    max_output_bytes: int = BOUNDS["max_output_bytes"]
    schema_version: int = SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    # -- policy helpers -------------------------------------------------

    def impact_of(self, tool_name: str) -> str:
        """A tool is at least as risky as its provider says, and never less."""
        declared = dict(self.tool_impacts).get(tool_name)
        return max_impact(self.impact, declared or READ)

    def gate_action(self, tool_name: str = "") -> str:
        risk = self.impact_of(tool_name) if tool_name else self.impact
        return MCP_HIGH_IMPACT_GATE if risk == HIGH_IMPACT else MCP_INVOKE

    def permits_agent(self, agent_id: str) -> bool:
        name = (agent_id or "").strip()
        if not name:
            return False
        if name in self.denied_agents:
            return False
        if not self.allowed_agents:
            return False  # a provider grants nothing until an agent is named
        return name in self.allowed_agents

    def permits_skill(self, skill_id: str) -> bool:
        if not skill_id:
            return True
        if not self.allowed_skills:
            return True
        return skill_id in self.allowed_skills

    def permits_tool(self, tool_name: str) -> bool:
        name = (tool_name or "").strip()
        if not name:
            return False
        if name in self.denied_tools:
            return False
        if not self.allowed_tools:
            return True
        return name in self.allowed_tools

    def may_discover(self) -> bool:
        return self.enabled and self.trust in DISCOVERABLE_TRUST

    def may_execute(self) -> bool:
        return self.enabled and self.trust in EXECUTABLE_TRUST

    def unavailable_reason(self) -> str:
        """Say plainly why a provider cannot be used."""
        if not self.enabled:
            return "provider is disabled"
        if self.trust == UNAVAILABLE:
            return "provider is marked unavailable"
        if self.trust == DISABLED:
            return "provider trust is disabled"
        if self.trust == UNTRUSTED:
            return "provider is untrusted; it must be reviewed and trusted before use"
        if self.trust == CONFIGURED:
            return "provider is configured for discovery only, not execution"
        return ""

    def to_dict(self, *, include_env: bool = False) -> dict[str, Any]:
        """Never emits environment values; they can carry credentials."""
        data = {
            "provider_id": self.provider_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "transport": self.transport,
            "command": list(self.command),
            "cwd": self.cwd,
            "url": self.url,
            "allow_local": self.allow_local,
            "trust": self.trust,
            "enabled": self.enabled,
            "impact": self.impact,
            "tool_impacts": {k: v for k, v in self.tool_impacts},
            "allowed_agents": list(self.allowed_agents),
            "denied_agents": list(self.denied_agents),
            "allowed_skills": list(self.allowed_skills),
            "allowed_tools": list(self.allowed_tools),
            "denied_tools": list(self.denied_tools),
            "required_actions": list(self.required_actions),
            "timeout_s": self.timeout_s,
            "max_output_bytes": self.max_output_bytes,
            "schema_version": self.schema_version,
            "metadata": dict(self.metadata),
            "may_discover": self.may_discover(),
            "may_execute": self.may_execute(),
            "unavailable_reason": self.unavailable_reason(),
        }
        # Environment names only, never values, and only when asked.
        data["env_keys"] = [k for k, _ in self.env] if include_env else []
        return data


def validate(defn: ProviderDefinition) -> ProviderDefinition:
    """Reject a provider before it can be registered, connected or launched."""
    if not isinstance(defn, ProviderDefinition):
        raise ProviderDefinitionError("Not a ProviderDefinition")
    if not _ID_RE.match(defn.provider_id or ""):
        raise ProviderDefinitionError(
            f"Invalid provider_id {defn.provider_id!r}: lowercase, digits, underscores, 3-64 chars"
        )
    if not (defn.name or "").strip():
        raise ProviderDefinitionError(f"{defn.provider_id}: name is required")
    if defn.transport not in TRANSPORTS:
        raise ProviderDefinitionError(f"{defn.provider_id}: unknown transport {defn.transport!r}")
    if defn.transport not in SUPPORTED_TRANSPORTS:
        raise ProviderDefinitionError(
            f"{defn.provider_id}: transport {defn.transport!r} is not supported by the "
            f"installed MCP SDK (supported: {', '.join(SUPPORTED_TRANSPORTS)})"
        )
    if defn.trust not in TRUST_LEVELS:
        raise ProviderDefinitionError(f"{defn.provider_id}: unknown trust {defn.trust!r}")
    if defn.impact not in IMPACTS:
        raise ProviderDefinitionError(f"{defn.provider_id}: unknown impact {defn.impact!r}")
    for tool, risk in defn.tool_impacts:
        if not _TOOL_RE.match(tool or ""):
            raise ProviderDefinitionError(f"{defn.provider_id}: invalid tool name {tool!r}")
        if risk not in IMPACTS:
            raise ProviderDefinitionError(
                f"{defn.provider_id}: unknown impact {risk!r} for tool {tool!r}"
            )
    if defn.schema_version != SCHEMA_VERSION:
        raise ProviderDefinitionError(
            f"{defn.provider_id}: schema_version {defn.schema_version} != {SCHEMA_VERSION}"
        )
    if defn.timeout_s <= 0:
        raise ProviderDefinitionError(f"{defn.provider_id}: timeout_s must be positive")
    if defn.max_output_bytes <= 0:
        raise ProviderDefinitionError(f"{defn.provider_id}: max_output_bytes must be positive")

    overlap = set(defn.allowed_agents) & set(defn.denied_agents)
    if overlap:
        raise ProviderDefinitionError(
            f"{defn.provider_id}: agent(s) both allowed and denied: {sorted(overlap)}"
        )
    tool_overlap = set(defn.allowed_tools) & set(defn.denied_tools)
    if tool_overlap:
        raise ProviderDefinitionError(
            f"{defn.provider_id}: tool(s) both allowed and denied: {sorted(tool_overlap)}"
        )

    if defn.transport == STDIO:
        _validate_command(defn)
    else:
        _validate_url(defn)
    return defn


def _validate_command(defn: ProviderDefinition) -> None:
    if not defn.command:
        raise ProviderDefinitionError(f"{defn.provider_id}: stdio provider needs a command")
    if not all(isinstance(part, str) for part in defn.command):
        raise ProviderDefinitionError(f"{defn.provider_id}: command must be a list of strings")
    binary = Path(defn.command[0]).name
    if binary not in ALLOWED_COMMANDS:
        raise ProviderDefinitionError(
            f"{defn.provider_id}: command {binary!r} is not an approved MCP launcher "
            f"(allowed: {', '.join(ALLOWED_COMMANDS)})"
        )
    # An absolute path must actually exist; a bare name must be resolvable.
    first = defn.command[0]
    if "/" in first:
        if not Path(first).is_file():
            raise ProviderDefinitionError(f"{defn.provider_id}: no such executable: {first}")
    elif shutil.which(first) is None:
        raise ProviderDefinitionError(f"{defn.provider_id}: executable not found on PATH: {first}")
    if defn.cwd:
        raw = defn.cwd
        if ".." in Path(raw).parts:
            raise ProviderDefinitionError(f"{defn.provider_id}: cwd must not contain '..': {raw}")
        root = Path(raw)
        if not root.is_absolute():
            raise ProviderDefinitionError(f"{defn.provider_id}: cwd must be absolute: {raw}")
        if root.resolve() != root:
            raise ProviderDefinitionError(
                f"{defn.provider_id}: cwd must be a resolved path: {raw} -> {root.resolve()}"
            )
        if not root.is_dir():
            raise ProviderDefinitionError(f"{defn.provider_id}: cwd is not a directory: {raw}")


def _validate_url(defn: ProviderDefinition) -> None:
    if not defn.url:
        raise ProviderDefinitionError(f"{defn.provider_id}: {defn.transport} provider needs a url")
    from jarvis.computer_use.actions import NavigationBlocked, check_url

    try:
        # Reuse the browser layer's SSRF policy rather than writing a second one.
        check_url(defn.url, allow_local=defn.allow_local)
    except NavigationBlocked as exc:
        raise ProviderDefinitionError(f"{defn.provider_id}: {exc}") from exc


__all__ = [
    "ALLOWED_COMMANDS",
    "BOUNDS",
    "CONFIGURED",
    "DISABLED",
    "DISCOVERABLE_TRUST",
    "EXECUTABLE_TRUST",
    "HIGH_IMPACT",
    "HTTP",
    "IMPACTS",
    "LOW_IMPACT",
    "MCP_DISCOVER",
    "MCP_HIGH_IMPACT_GATE",
    "MCP_INVOKE",
    "MODIFY",
    "READ",
    "SCHEMA_VERSION",
    "SSE",
    "STDIO",
    "SUPPORTED_TRANSPORTS",
    "TRANSPORTS",
    "TRUSTED",
    "TRUST_LEVELS",
    "UNAVAILABLE",
    "UNTRUSTED",
    "WEBSOCKET",
    "ProviderDefinition",
    "ProviderDefinitionError",
    "impact_rank",
    "max_impact",
    "qualified",
    "split_qualified",
    "validate",
]
