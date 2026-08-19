"""MCP provider registry — configuration, trust, and deterministic tool identity.

Tools are addressed as `provider_id:tool_name`, so two providers exposing a
`search` tool cannot shadow one another, and a qualified name always says which
external authority is about to be involved.
"""

from __future__ import annotations

import threading
from dataclasses import replace as dc_replace
from typing import Any

from jarvis.mcp import definitions as defs
from jarvis.mcp import secrets, store
from jarvis.mcp.definitions import ProviderDefinition, validate

_PROVIDERS: dict[str, ProviderDefinition] = {}
_CACHE: dict[str, dict[str, Any]] = {}  # provider_id -> discovery snapshot
_lock = threading.RLock()


class ProviderRegistryError(RuntimeError):
    pass


class ProviderNotFound(ProviderRegistryError):
    pass


def reset() -> None:
    with _lock:
        _PROVIDERS.clear()
        _CACHE.clear()


def register(
    defn: ProviderDefinition, *, replace: bool = False, persist: bool = True
) -> ProviderDefinition:
    """Validate and register a provider. A new provider is never trusted by default."""
    validate(defn)
    with _lock:
        if defn.provider_id in _PROVIDERS and not replace:
            raise ProviderRegistryError(f"Provider {defn.provider_id} is already registered")
        _PROVIDERS[defn.provider_id] = defn
        _CACHE.pop(defn.provider_id, None)
    if persist:
        store.save_provider(
            defn.provider_id,
            defn.to_dict(),
            trust=defn.trust,
            enabled=defn.enabled,
        )
    return defn


def unregister(provider_id: str, *, persist: bool = True) -> bool:
    with _lock:
        existed = _PROVIDERS.pop(provider_id, None) is not None
        _CACHE.pop(provider_id, None)
    if persist:
        store.delete_provider(provider_id)
    return existed


def get(provider_id: str) -> ProviderDefinition | None:
    with _lock:
        return _PROVIDERS.get(provider_id)


def require(provider_id: str) -> ProviderDefinition:
    defn = get(provider_id)
    if not defn:
        raise ProviderNotFound(f"No such MCP provider: {provider_id}")
    return defn


def list_providers() -> list[ProviderDefinition]:
    with _lock:
        return [_PROVIDERS[k] for k in sorted(_PROVIDERS)]


def set_trust(provider_id: str, trust: str) -> ProviderDefinition:
    """Trust is an explicit operator decision, never inferred from discovery."""
    if trust not in defs.TRUST_LEVELS:
        raise ProviderRegistryError(f"Unknown trust level: {trust!r}")
    defn = require(provider_id)
    updated = dc_replace(defn, trust=trust)
    with _lock:
        _PROVIDERS[provider_id] = updated
    store.save_provider(provider_id, updated.to_dict(), trust=trust, enabled=updated.enabled)
    return updated


def set_enabled(provider_id: str, enabled: bool) -> ProviderDefinition:
    defn = require(provider_id)
    updated = dc_replace(defn, enabled=bool(enabled))
    with _lock:
        _PROVIDERS[provider_id] = updated
    store.save_provider(
        provider_id, updated.to_dict(), trust=updated.trust, enabled=updated.enabled
    )
    return updated


def launch_definition(provider_id: str) -> ProviderDefinition:
    """The definition used to actually start a provider, with secrets attached.

    Secrets are merged in here and nowhere else, so they exist only on the
    object handed to the transport and never on anything that gets serialised.
    """
    defn = require(provider_id)
    stored = secrets.get_provider_env(provider_id)
    if not stored:
        return defn
    merged = dict(defn.env) | stored
    return dc_replace(defn, env=tuple(sorted(merged.items())))


# ------------------------------------------------------------------ discovery


def cache_discovery(provider_id: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        _CACHE[provider_id] = snapshot
    return snapshot


def cached_discovery(provider_id: str) -> dict[str, Any] | None:
    with _lock:
        return _CACHE.get(provider_id)


def tools_for(provider_id: str) -> list[dict[str, Any]]:
    snapshot = cached_discovery(provider_id) or {}
    return list(snapshot.get("tools") or [])


def find_tool(provider_id: str, tool_name: str) -> dict[str, Any] | None:
    for tool in tools_for(provider_id):
        if tool.get("name") == tool_name:
            return tool
    return None


def qualified_tools() -> list[dict[str, Any]]:
    """Every known tool under its provider-qualified identity."""
    out = []
    for defn in list_providers():
        for tool in tools_for(defn.provider_id):
            name = tool.get("name") or ""
            out.append(
                {
                    "qualified_name": defs.qualified(defn.provider_id, name),
                    "provider_id": defn.provider_id,
                    "tool": name,
                    "description": tool.get("description") or "",
                    "input_schema": tool.get("input_schema") or {},
                    "impact": defn.impact_of(name),
                    "provider_trust": defn.trust,
                    "available": defn.may_execute() and defn.permits_tool(name),
                    "unavailable_reason": (
                        defn.unavailable_reason()
                        or (
                            "tool is not permitted by provider policy"
                            if not defn.permits_tool(name)
                            else ""
                        )
                    ),
                }
            )
    return sorted(out, key=lambda t: t["qualified_name"])


def load_persisted() -> list[str]:
    """Restore provider configuration written by an earlier process."""
    restored = []
    for row in store.list_providers():
        config = row.get("config") or {}
        try:
            defn = _from_config(
                config,
                trust=row.get("trust") or defs.UNTRUSTED,
                enabled=bool(row.get("enabled", 1)),
            )
        except defs.ProviderDefinitionError:
            # A configuration that no longer validates must not silently load.
            continue
        with _lock:
            _PROVIDERS[defn.provider_id] = defn
        restored.append(defn.provider_id)
    return restored


def _from_config(config: dict[str, Any], *, trust: str, enabled: bool) -> ProviderDefinition:
    return validate(
        ProviderDefinition(
            provider_id=config.get("provider_id", ""),
            name=config.get("name", ""),
            description=config.get("description", ""),
            version=config.get("version", "1.0.0"),
            transport=config.get("transport", defs.STDIO),
            command=tuple(config.get("command") or ()),
            cwd=config.get("cwd", ""),
            url=config.get("url", ""),
            allow_local=bool(config.get("allow_local")),
            trust=trust,
            enabled=enabled,
            impact=config.get("impact", defs.READ),
            tool_impacts=tuple((config.get("tool_impacts") or {}).items()),
            allowed_agents=tuple(config.get("allowed_agents") or ()),
            denied_agents=tuple(config.get("denied_agents") or ()),
            allowed_skills=tuple(config.get("allowed_skills") or ()),
            allowed_tools=tuple(config.get("allowed_tools") or ()),
            denied_tools=tuple(config.get("denied_tools") or ()),
            required_actions=tuple(config.get("required_actions") or ()),
            timeout_s=float(config.get("timeout_s", 30.0)),
            max_output_bytes=int(config.get("max_output_bytes", defs.BOUNDS["max_output_bytes"])),
            metadata=dict(config.get("metadata") or {}),
        )
    )
