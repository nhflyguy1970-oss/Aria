"""Inference routing policy — local-first, GPU-aware, optional cloud."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

CLOUD_PREFIXES = (
    "openai/",
    "gpt-",
    "anthropic/",
    "claude-",
    "gemini/",
    "google/",
)


@dataclass(frozen=True)
class InferenceRoute:
    backend: str  # ollama | litellm
    model: str
    reason: str
    local: bool = True
    cloud: bool = False


def gateway_mode() -> str:
    """auto | ollama | litellm — default auto (local-first)."""
    return os.getenv("JARVIS_INFERENCE_GATEWAY", "auto").strip().lower() or "auto"


def cloud_enabled() -> bool:
    from jarvis.inference.boundary import cloud_enabled as _enabled

    return _enabled()


def _is_cloud_model(model: str) -> bool:
    from jarvis.inference.boundary import is_cloud_model

    return is_cloud_model(model)


def _litellm_model_name(model: str) -> str:
    """Map Aria model id to LiteLLM model name."""
    name = (model or "").strip()
    if not name:
        return name
    if _is_cloud_model(name):
        return name
    if name.startswith("ollama/"):
        return name
    return f"ollama/{name}"


def _estimate_context_tokens(messages: list[dict]) -> int:
    total = 0
    for msg in messages or []:
        content = msg.get("content") or ""
        if isinstance(content, str):
            total += max(1, len(content) // 4)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("text"):
                    total += max(1, len(str(part["text"])) // 4)
    return total


def _low_vram() -> bool:
    try:
        from jarvis.gpu import is_low_vram

        return is_low_vram(10240)
    except Exception:
        return False


def _smaller_model(model: str, role: str) -> str:
    """Suggest a smaller local model when VRAM is tight."""
    from jarvis.model_store import model_for

    if role == "coder":
        return model_for("coder")
    if role == "vision":
        return model_for("vision")
    if "14b" in model or "13b" in model or "12b" in model:
        return model_for("conversation")
    return model


def select_route(
    model: str,
    *,
    role: str = "general",
    messages: list[dict] | None = None,
    prefer_local: bool | None = None,
    lock_model: bool = False,
) -> InferenceRoute:
    """Choose inference backend and model for a request.

    When ``lock_model`` is True (benchmark policy winner), personalization and
    low-VRAM swaps must not replace the measured model. Hardware options remain
    the caller's responsibility (gateway).
    """
    from jarvis.inference.gateway import litellm_available

    mode = gateway_mode()
    local_first = True if prefer_local is None else prefer_local
    if not local_first:
        local_first = not cloud_enabled()

    model = (model or "").strip()
    context_tokens = _estimate_context_tokens(messages or [])
    cloud_model = _is_cloud_model(model)
    vram_reason = ""

    if not lock_model:
        try:
            from jarvis.personalization.store import preferred_model

            pref = preferred_model(role, fallback="")
            if pref and not cloud_model and gateway_mode() != "litellm":
                model = pref
        except Exception:
            pass

        if _low_vram() and not cloud_model:
            adjusted = _smaller_model(model, role)
            if adjusted != model:
                model = adjusted
                vram_reason = "low_vram_smaller_model"
            else:
                vram_reason = "low_vram"
    else:
        vram_reason = "benchmark_locked"

    if cloud_model:
        # An explicit cloud model is a request, not an authorisation: the
        # cloud-disable switch, offline mode and the provider allowlist all
        # apply. A refused or unreachable cloud target is answered by an
        # installed local model for the role — never by handing the cloud
        # model id to Ollama.
        from jarvis.inference.boundary import cloud_refusal, local_fallback

        refusal = cloud_refusal(model)
        if refusal:
            return InferenceRoute(
                backend="ollama",
                model=local_fallback(role),
                reason=f"cloud_refused: {refusal}",
                local=True,
            )
        if mode != "ollama":
            from jarvis.inference.providers import has_credentials, split_model

            provider, _native = split_model(model)
            if has_credentials(provider):
                # Native adapter: the gateway still requires an owner
                # authorization, a price and budget before anything is sent.
                return InferenceRoute(
                    backend="native",
                    model=model,
                    reason=f"cloud model via native {provider} adapter",
                    local=False,
                    cloud=True,
                )
        if mode != "ollama" and litellm_available():
            return InferenceRoute(
                backend="litellm",
                model=_litellm_model_name(model),
                reason="cloud model via litellm",
                local=False,
                cloud=True,
            )
        return InferenceRoute(
            backend="ollama",
            model=local_fallback(role),
            reason="cloud_gateway_unavailable_local_fallback",
            local=True,
        )

    if mode == "ollama":
        reason = vram_reason or "gateway=ollama"
        return InferenceRoute(backend="ollama", model=model, reason=reason, local=True)

    reason = vram_reason or "local_default"

    # Operator opt-in only: otherwise the default conversation stays local.
    if not lock_model and mode != "ollama":
        from jarvis.inference.provider_routing import choose, routing_config

        if routing_config().get("auto_escalate"):
            decision = choose(role, context_tokens=context_tokens, include_cloud=True)
            if decision.chosen is not None and decision.chosen.locality == "cloud":
                return InferenceRoute(
                    backend="native",
                    model=decision.chosen.model,
                    reason="auto: "
                    + next((e for e in decision.explanation if e.startswith("chose ")), "ranked best"),
                    local=False,
                    cloud=True,
                )

    # Large-context escalation needs an operator-named cloud model; ARIA does
    # not hardcode one (names change; availability is per account).
    cloud_default = os.getenv("JARVIS_CLOUD_MODEL", "").strip()
    if (
        cloud_default
        and context_tokens > int(os.getenv("JARVIS_LOCAL_CTX_LIMIT", "12000"))
        and cloud_enabled()
    ):
        from jarvis.inference.boundary import cloud_refusal

        if not cloud_refusal(cloud_default) and litellm_available():
            return InferenceRoute(
                backend="litellm",
                model=cloud_default,
                reason="large_context_cloud_fallback",
                local=False,
                cloud=True,
            )

    if mode == "litellm" or (
        mode == "auto" and litellm_available() and os.getenv("JARVIS_ROUTE_VIA_LITELLM", "0") == "1"
    ):
        return InferenceRoute(
            backend="litellm",
            model=_litellm_model_name(model),
            reason="litellm_gateway",
            local=True,
        )

    return InferenceRoute(backend="ollama", model=model, reason=reason, local=True)


def route_summary() -> dict[str, Any]:
    from jarvis.inference.gateway import litellm_available

    return {
        "gateway_mode": gateway_mode(),
        "cloud_enabled": cloud_enabled(),
        "litellm_available": litellm_available(),
        "local_first": not cloud_enabled() or gateway_mode() != "litellm",
        "low_vram": _low_vram(),
    }
