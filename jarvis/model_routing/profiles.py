"""Model profiles — what each model can actually do, and how we know.

Capabilities come from the provider wherever the provider will tell us: Ollama
advertises real capability tokens and a real context length on /api/show. Where
it will not, the profile says UNKNOWN and records that it is a guess, rather
than inventing a capability ARIA cannot stand behind.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field, replace
from typing import Any

from jarvis.model_routing import capabilities as caps

log = logging.getLogger("jarvis.model_routing.profiles")

OLLAMA = "ollama"
PROVIDERS = (OLLAMA,)

# Latency classes, ordered fastest first.
FAST = "fast"
MEDIUM = "medium"
SLOW = "slow"
LATENCY_CLASSES = (FAST, MEDIUM, SLOW)

DISCOVERY_TTL_S = 300.0
SHOW_TIMEOUT_S = 10.0

# Strength hints keyed by model-name substring. These are preferences, never
# hard requirements: getting one wrong picks a less suitable model, it does not
# produce an invalid result. Hard requirements come from provider evidence only.
_CODING_HINTS = ("coder", "codellama", "devstral", "starcoder", "codegemma")
_REASONING_HINTS = ("deepseek-r1", "thinking", "qwq", "gpt-oss")

_SMALL_PARAM_CEILING = 4.0  # billions; below this a model is treated as fast
_LARGE_PARAM_FLOOR = 13.0  # billions; above this a model is treated as slow/high quality


@dataclass(frozen=True)
class ModelProfile:
    """An immutable statement of what a model can do and how we know it."""

    provider: str
    model_id: str
    display_name: str = ""
    enabled: bool = True
    capabilities: dict[str, str] = field(default_factory=dict)
    capability_evidence: dict[str, str] = field(default_factory=dict)
    context_window: int = 0
    max_output_tokens: int = 0
    parameter_size_b: float = 0.0
    size_bytes: int = 0
    family: str = ""
    latency_class: str = MEDIUM
    coding_strength: float = 0.5
    reasoning_strength: float = 0.5
    research_strength: float = 0.5
    general_strength: float = 0.5
    preferred_roles: tuple[str, ...] = ()
    prohibited_roles: tuple[str, ...] = ()
    priority: int = 0
    fallback_group: str = "default"
    timeout_s: float = 120.0
    discovered_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.provider}:{self.model_id}"

    def supports(self, capability: str) -> str:
        """Tri-state support for a capability."""
        return self.capabilities.get(capability, caps.UNKNOWN)

    def satisfies(self, capability: str) -> bool:
        return caps.satisfies(self.supports(capability), capability)

    def evidence_for(self, capability: str) -> str:
        return self.capability_evidence.get(capability, "not_established")

    def is_local(self) -> bool:
        # Everything ARIA currently routes to runs on this machine.
        return self.provider == OLLAMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model_id": self.model_id,
            "key": self.key,
            "display_name": self.display_name or self.model_id,
            "enabled": self.enabled,
            "capabilities": dict(self.capabilities),
            "capability_evidence": dict(self.capability_evidence),
            "context_window": self.context_window,
            "max_output_tokens": self.max_output_tokens,
            "parameter_size_b": self.parameter_size_b,
            "family": self.family,
            "latency_class": self.latency_class,
            "coding_strength": self.coding_strength,
            "reasoning_strength": self.reasoning_strength,
            "research_strength": self.research_strength,
            "general_strength": self.general_strength,
            "preferred_roles": list(self.preferred_roles),
            "prohibited_roles": list(self.prohibited_roles),
            "priority": self.priority,
            "fallback_group": self.fallback_group,
            "local": self.is_local(),
            "discovered_at": self.discovered_at,
            "metadata": dict(self.metadata),
        }


# --------------------------------------------------------------- discovery

_lock = threading.RLock()
_profiles: dict[str, ModelProfile] = {}
_discovered_at: float = 0.0
_overrides: dict[str, dict[str, Any]] = {}


def reset() -> None:
    """Drop the cache. Used by tests and after a capability change."""
    global _discovered_at
    with _lock:
        _profiles.clear()
        _overrides.clear()
        _discovered_at = 0.0


def _parse_params(text: str) -> float:
    raw = (text or "").strip().upper().rstrip("B")
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _latency_for(params_b: float) -> str:
    if params_b and params_b <= _SMALL_PARAM_CEILING:
        return FAST
    if params_b and params_b >= _LARGE_PARAM_FLOOR:
        return SLOW
    return MEDIUM


def _strength(name: str, hints: tuple[str, ...], params_b: float) -> float:
    """A preference score in [0,1]. Specialisation counts more than size."""
    lowered = name.lower()
    base = 0.35
    if any(h in lowered for h in hints):
        base = 0.85
    # Bigger models are generally stronger, but this only breaks ties.
    if params_b >= 20:
        base += 0.10
    elif params_b >= 12:
        base += 0.06
    elif params_b <= 2:
        base -= 0.10
    return round(max(0.0, min(1.0, base)), 3)


def _capabilities_from_show(model_id: str, show: dict[str, Any]) -> tuple[dict, dict, int]:
    """Turn provider metadata into tri-state capabilities plus their evidence."""
    capabilities: dict[str, str] = {}
    evidence: dict[str, str] = {}

    advertised = [str(c).strip().lower() for c in (show.get("capabilities") or [])]
    for token in advertised:
        mapped = caps.PROVIDER_CAPABILITY_TOKENS.get(token)
        if mapped:
            capabilities[mapped] = caps.SUPPORTED
            evidence[mapped] = f"provider_advertised:{token}"

    # A provider that lists its capabilities and omits one is saying it is not
    # there. Only then is UNSUPPORTED justified.
    if advertised:
        for token, mapped in caps.PROVIDER_CAPABILITY_TOKENS.items():
            if token not in advertised and mapped not in capabilities:
                capabilities[mapped] = caps.UNSUPPORTED
                evidence[mapped] = "provider_listed_capabilities_without_it"

    context_window = 0
    for key, value in (show.get("model_info") or {}).items():
        if str(key).endswith(".context_length"):
            try:
                context_window = int(value)
            except (TypeError, ValueError):
                context_window = 0
            break

    if context_window:
        state = (
            caps.SUPPORTED if context_window >= caps.LONG_CONTEXT_THRESHOLD else caps.UNSUPPORTED
        )
        capabilities[caps.LONG_CONTEXT] = state
        evidence[caps.LONG_CONTEXT] = f"provider_context_length:{context_window}"

    # Ollama constrains decoding to a schema with its `format` parameter, so
    # structured output is a property of the provider rather than a guess about
    # the model. Embedding-only models cannot chat, so they are excluded.
    if "embedding" not in advertised:
        capabilities[caps.STRUCTURED_OUTPUT] = caps.SUPPORTED
        evidence[caps.STRUCTURED_OUTPUT] = "provider_feature:ollama_format"
    else:
        capabilities[caps.STRUCTURED_OUTPUT] = caps.UNSUPPORTED
        evidence[caps.STRUCTURED_OUTPUT] = "embedding_model_cannot_chat"

    return capabilities, evidence, context_window


def build_profile(model_id: str, tag: dict[str, Any], show: dict[str, Any]) -> ModelProfile:
    details = tag.get("details") or {}
    params_b = _parse_params(details.get("parameter_size", ""))
    capabilities, evidence, context_window = _capabilities_from_show(model_id, show)

    # Inferred strengths are preferences, never hard requirements, so they are
    # recorded as UNKNOWN capabilities with an explicit "inferred" evidence tag.
    lowered = model_id.lower()
    for capability, hints in (
        (caps.CODING, _CODING_HINTS),
        (caps.REASONING, _REASONING_HINTS),
    ):
        if capability not in capabilities or capabilities[capability] == caps.UNSUPPORTED:
            if any(h in lowered for h in hints):
                capabilities[capability] = caps.UNKNOWN
                evidence[capability] = "inferred_from_model_name"

    for capability in (caps.RESEARCH, caps.SUMMARIZATION, caps.EXTRACTION):
        capabilities.setdefault(capability, caps.UNKNOWN)
        evidence.setdefault(capability, "inferred_general_language_ability")

    latency = _latency_for(params_b)
    capabilities[caps.FAST_RESPONSE] = caps.SUPPORTED if latency == FAST else caps.UNSUPPORTED
    evidence[caps.FAST_RESPONSE] = f"parameter_size:{params_b or 'unknown'}B"
    capabilities[caps.HIGH_QUALITY] = caps.SUPPORTED if params_b >= 12 else caps.UNKNOWN
    evidence[caps.HIGH_QUALITY] = f"parameter_size:{params_b or 'unknown'}B"
    capabilities[caps.LOCAL_ONLY] = caps.SUPPORTED
    evidence[caps.LOCAL_ONLY] = "provider_runs_on_this_machine:ollama"

    return ModelProfile(
        provider=OLLAMA,
        model_id=model_id,
        display_name=model_id,
        capabilities=capabilities,
        capability_evidence=evidence,
        context_window=context_window,
        parameter_size_b=params_b,
        size_bytes=int(tag.get("size") or 0),
        family=str(details.get("family") or ""),
        latency_class=latency,
        coding_strength=_strength(model_id, _CODING_HINTS, params_b),
        reasoning_strength=_strength(model_id, _REASONING_HINTS, params_b),
        research_strength=_strength(model_id, (), params_b),
        general_strength=_strength(model_id, (), params_b),
        discovered_at=time.time(),
    )


def _ollama_tags(timeout: float) -> list[dict[str, Any]]:
    import json
    import urllib.request

    from jarvis.ollama_health import ollama_host

    url = f"{ollama_host()}/api/tags"
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response).get("models") or []


def _ollama_show(model_id: str, timeout: float) -> dict[str, Any]:
    import json
    import urllib.request

    from jarvis.ollama_health import ollama_host

    url = f"{ollama_host()}/api/show"
    payload = json.dumps({"model": model_id}).encode()
    request = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def discover(*, force: bool = False, timeout: float = SHOW_TIMEOUT_S) -> list[ModelProfile]:
    """Ask the provider what it has and what each model can do.

    Bounded and metadata-only: this never loads a model to find out.
    """
    global _discovered_at
    with _lock:
        fresh = (time.time() - _discovered_at) < DISCOVERY_TTL_S
        if _profiles and fresh and not force:
            return sorted(_profiles.values(), key=lambda p: p.model_id)

    try:
        tags = _ollama_tags(timeout)
    except Exception as exc:  # noqa: BLE001 - a provider outage must not raise here
        log.warning("model discovery failed: %s", exc)
        with _lock:
            return sorted(_profiles.values(), key=lambda p: p.model_id)

    built: dict[str, ModelProfile] = {}
    for tag in tags:
        model_id = str(tag.get("name") or "").strip()
        if not model_id:
            continue
        try:
            show = _ollama_show(model_id, timeout)
        except Exception as exc:  # noqa: BLE001 - one bad model must not stop discovery
            log.info("capability discovery failed for %s: %s", model_id, exc)
            show = {}
        profile = build_profile(model_id, tag, show)
        built[profile.key] = _apply_override(profile)

    with _lock:
        _profiles.clear()
        _profiles.update(built)
        _discovered_at = time.time()
        return sorted(_profiles.values(), key=lambda p: p.model_id)


def _apply_override(profile: ModelProfile) -> ModelProfile:
    override = _overrides.get(profile.key) or _overrides.get(profile.model_id)
    if not override:
        return profile
    capabilities = dict(profile.capabilities)
    evidence = dict(profile.capability_evidence)
    for capability, state in (override.get("capabilities") or {}).items():
        capabilities[capability] = state
        evidence[capability] = "administrator_configured"
    return replace(
        profile,
        capabilities=capabilities,
        capability_evidence=evidence,
        enabled=bool(override.get("enabled", profile.enabled)),
        priority=int(override.get("priority", profile.priority)),
        prohibited_roles=tuple(override.get("prohibited_roles", profile.prohibited_roles)),
    )


def set_override(model_key: str, override: dict[str, Any]) -> None:
    """Administrator statement about a model. Also invalidates the cache.

    Stale capability data must never route an incompatible task, so any change
    forces rediscovery rather than patching a cached profile in place.
    """
    global _discovered_at
    with _lock:
        _overrides[model_key] = dict(override or {})
        _discovered_at = 0.0
        _profiles.clear()


def clear_override(model_key: str) -> bool:
    global _discovered_at
    with _lock:
        existed = _overrides.pop(model_key, None) is not None
        _discovered_at = 0.0
        _profiles.clear()
    return existed


def all_profiles(*, force: bool = False) -> list[ModelProfile]:
    return discover(force=force)


def get_profile(model_id: str, *, provider: str = OLLAMA) -> ModelProfile | None:
    for profile in discover():
        if profile.model_id == model_id or profile.key == model_id:
            return profile
    with _lock:
        return _profiles.get(f"{provider}:{model_id}")


def register_profile(profile: ModelProfile) -> ModelProfile:
    """Insert a profile directly. Used by tests and by non-discovered models."""
    global _discovered_at
    with _lock:
        _profiles[profile.key] = profile
        if not _discovered_at:
            _discovered_at = time.time()
    return profile
