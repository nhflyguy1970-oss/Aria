"""Model selection policy — role → policy inputs → model.

The registry (`model_store`) defines configured models per role.
This module decides which model is actually selected given hardware, health,
benchmark policy, personalization, and cloud settings.

No model names should appear outside registry + policy layers.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any

from jarvis.model_store import FALLBACK_PRIORITY, canonical_role, model_for

# Roles that never select a chat LLM.
NON_LLM_ROLES = frozenset(
    {
        "memory",
        "runtime",
        "mission_control",
        "speech",
        "stt",
        "tts",
        "greeting",
        "reference",
        "embedding",
        "image",
        "image_generation",
    }
)


@dataclass(frozen=True)
class PolicyContext:
    context_tokens: int = 0
    latency_preference: str = "balanced"  # fast | balanced | quality
    power_saving: bool = False
    cloud_enabled: bool = False
    user_model_override: str = ""
    require_tools: bool = False
    require_vision: bool = False
    require_reasoning: bool = False
    require_coding: bool = False
    profile: str = "desktop"  # desktop | laptop

    @classmethod
    def from_env(
        cls,
        *,
        context_tokens: int = 0,
        user_model_override: str = "",
        require_tools: bool = False,
        require_vision: bool = False,
        require_reasoning: bool = False,
        require_coding: bool = False,
    ) -> PolicyContext:
        latency = os.getenv("JARVIS_LATENCY_PREFERENCE", "balanced").strip().lower()
        power = os.getenv("JARVIS_POWER_SAVING", "0").strip().lower() in ("1", "true", "yes")
        cloud = os.getenv("JARVIS_CLOUD_INFERENCE", "0").strip().lower() in ("1", "true", "yes")
        profile = os.getenv("JARVIS_DEVICE_PROFILE", "desktop").strip().lower()
        return cls(
            context_tokens=context_tokens,
            latency_preference=latency if latency in ("fast", "balanced", "quality") else "balanced",
            power_saving=power,
            cloud_enabled=cloud,
            user_model_override=(user_model_override or "").strip(),
            require_tools=require_tools,
            require_vision=require_vision,
            require_reasoning=require_reasoning,
            require_coding=require_coding,
            profile=profile if profile in ("desktop", "laptop") else "desktop",
        )


@dataclass
class ModelSelection:
    role: str
    configured_model: str | None = None
    selected_model: str | None = None
    provider: str = "ollama"
    execution_path: str = "local"
    policy_reason: str = "registry_default"
    fallback_active: bool = False
    fallback_model: str | None = None
    policy_inputs: dict[str, Any] = field(default_factory=dict)
    overlay: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _model_available(name: str) -> bool:
    if not (name or "").strip():
        return False
    try:
        from jarvis.ollama_health import model_available

        return bool(model_available(name))
    except Exception:
        return True


def _installed_models() -> list[str]:
    try:
        from jarvis.model_store import _installed

        return _installed()
    except Exception:
        return []


def _pick_installed(candidates: list[str]) -> str | None:
    installed = _installed_models()
    lower = {m.lower(): m for m in installed}
    for candidate in candidates:
        key = (candidate or "").lower()
        if key in lower:
            return lower[key]
        base = key.split(":")[0]
        for name in installed:
            if name.lower().startswith(base):
                return name
    return None


def _low_vram() -> bool:
    try:
        from jarvis.gpu import is_low_vram

        return is_low_vram()
    except Exception:
        return False


def _cloud_model_for_role(role: str) -> str | None:
    if not PolicyContext.from_env().cloud_enabled:
        return None
    env = (os.getenv("JARVIS_CLOUD_MODEL") or os.getenv("JARVIS_CLOUD_FALLBACK_MODEL") or "").strip()
    if env:
        return env
    if role in ("coding", "debugging"):
        return (os.getenv("JARVIS_CLOUD_CODER_MODEL") or "gpt-4o-mini").strip() or None
    return "gpt-4o-mini"


def _benchmark_overlay(model: str, role: str) -> dict[str, Any]:
    from jarvis.inference.execution_policy import apply_policy_to_route

    return apply_policy_to_route(model=model, role=canonical_role(role))


def select_model_for_role(
    role: str,
    *,
    context: PolicyContext | None = None,
    configured_override: str | None = None,
) -> ModelSelection:
    """Central policy: role → configured candidates → selected model."""
    canonical = canonical_role(role)
    ctx = context or PolicyContext.from_env()

    if canonical in NON_LLM_ROLES or role in NON_LLM_ROLES:
        selection = ModelSelection(
            role=canonical,
            configured_model=None,
            selected_model=None,
            provider="none",
            execution_path="bypass",
            policy_reason="non_llm_role",
            policy_inputs=_policy_inputs(ctx),
        )
        _maybe_record_trace(selection)
        return selection

    configured = (configured_override or ctx.user_model_override or model_for(canonical)).strip()
    selected = configured
    reason = "registry_default"
    fallback_active = False
    fallback_model: str | None = None
    provider = "ollama"
    execution_path = "local_gpu"

    # Personalization (learned preference) when no explicit override.
    if not ctx.user_model_override:
        try:
            from jarvis.personalization.store import preferred_model

            pref = preferred_model(canonical, fallback="")
            if pref and _model_available(pref):
                selected = pref
                reason = "user_preference_learned"
        except Exception:
            pass

    overlay = _benchmark_overlay(selected, canonical)
    if overlay.get("model") and overlay.get("source") == "benchmark":
        selected = str(overlay["model"])
        reason = str(overlay.get("reason") or "benchmark_policy")
        fallback_model = overlay.get("fallback_model")
        hw = str(overlay.get("hardware") or "cpu")
        execution_path = "local_gpu" if hw not in ("cpu", "") else "cpu"

    # Hardware / latency / power-saving adjustments.
    if ctx.power_saving or ctx.latency_preference == "fast" or _low_vram():
        if any(tok in (selected or "").lower() for tok in ("14b", "13b", "12b", "16b")):
            candidates = list(FALLBACK_PRIORITY.get(canonical, []))
            smaller = _pick_installed(candidates)
            if smaller and smaller != selected:
                fallback_model = selected
                selected = smaller
                fallback_active = True
                reason = "vram_or_latency_fallback"
                execution_path = "local_gpu" if _low_vram() else execution_path

    if not _model_available(selected):
        candidates = list(FALLBACK_PRIORITY.get(canonical, []))
        alt = _pick_installed(candidates)
        if alt:
            fallback_model = selected
            selected = alt
            fallback_active = True
            reason = "model_unavailable_fallback"

    # Large context → cloud when enabled.
    if ctx.cloud_enabled and ctx.context_tokens > 12000:
        cloud = _cloud_model_for_role(canonical)
        if cloud:
            fallback_model = selected
            selected = cloud
            provider = "cloud"
            execution_path = "cloud"
            fallback_active = True
            reason = "large_context_cloud"

    selection = ModelSelection(
        role=canonical,
        configured_model=configured,
        selected_model=selected,
        provider=provider,
        execution_path=execution_path,
        policy_reason=reason,
        fallback_active=fallback_active,
        fallback_model=fallback_model,
        policy_inputs=_policy_inputs(ctx),
        overlay=overlay,
    )
    _maybe_record_trace(selection)
    return selection


def _policy_inputs(ctx: PolicyContext) -> dict[str, Any]:
    inputs: dict[str, Any] = {
        "context_tokens": ctx.context_tokens,
        "latency_preference": ctx.latency_preference,
        "power_saving": ctx.power_saving,
        "cloud_enabled": ctx.cloud_enabled,
        "profile": ctx.profile,
        "low_vram": _low_vram(),
    }
    try:
        from jarvis.gpu import detect_gpu

        gpu = detect_gpu()
        inputs["vram_gb"] = gpu.get("vram_gb")
        inputs["compute_vendor"] = gpu.get("compute_vendor") or gpu.get("vendor")
    except Exception:
        pass
    return inputs


def resolve_selected_model(
    role: str,
    *,
    context: PolicyContext | None = None,
    user_model_override: str = "",
    context_tokens: int = 0,
) -> str | None:
    """Convenience: return selected model string for a role."""
    ctx = context or PolicyContext.from_env(
        context_tokens=context_tokens,
        user_model_override=user_model_override,
    )
    return select_model_for_role(role, context=ctx).selected_model


def _maybe_record_trace(selection: ModelSelection) -> None:
    try:
        from jarvis.routing_trace import record_model_selection

        record_model_selection(
            role=selection.role,
            configured_model=selection.configured_model,
            selected_model=selection.selected_model,
            policy={
                "policy_reason": selection.policy_reason,
                "execution_path": selection.execution_path,
                "fallback_active": selection.fallback_active,
                "fallback_model": selection.fallback_model,
                "provider": selection.provider,
                "policy_inputs": selection.policy_inputs,
                "overlay": selection.overlay,
            },
            provider=selection.provider,
        )
    except Exception:
        pass
