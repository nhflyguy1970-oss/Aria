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
    return os.getenv("JARVIS_CLOUD_INFERENCE", "0").lower() in ("1", "true", "yes", "on")


def _is_cloud_model(model: str) -> bool:
    lower = (model or "").strip().lower()
    return any(lower.startswith(prefix) for prefix in CLOUD_PREFIXES)


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
        return model_for("general")
    return model


def select_route(
    model: str,
    *,
    role: str = "general",
    messages: list[dict] | None = None,
    prefer_local: bool | None = None,
) -> InferenceRoute:
    """Choose inference backend and model for a request."""
    from jarvis.inference.gateway import litellm_available

    mode = gateway_mode()
    local_first = True if prefer_local is None else prefer_local
    if not local_first:
        local_first = not cloud_enabled()

    model = (model or "").strip()
    context_tokens = _estimate_context_tokens(messages or [])
    cloud_model = _is_cloud_model(model)

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
        vram_reason = ""

    if mode == "ollama":
        reason = vram_reason or "gateway=ollama"
        return InferenceRoute(backend="ollama", model=model, reason=reason, local=True)

    if cloud_model:
        if litellm_available():
            return InferenceRoute(
                backend="litellm",
                model=_litellm_model_name(model),
                reason="cloud model via litellm",
                local=False,
                cloud=True,
            )
        return InferenceRoute(
            backend="ollama",
            model=model,
            reason="cloud model requested but litellm offline",
            local=False,
            cloud=True,
        )

    reason = vram_reason or "local_default"

    if context_tokens > int(os.getenv("JARVIS_LOCAL_CTX_LIMIT", "12000")) and cloud_enabled():
        if litellm_available():
            cloud_default = os.getenv("JARVIS_CLOUD_MODEL", "gpt-4o-mini")
            return InferenceRoute(
                backend="litellm",
                model=cloud_default,
                reason="large_context_cloud_fallback",
                local=False,
                cloud=True,
            )

    if mode == "litellm" or (mode == "auto" and litellm_available() and os.getenv("JARVIS_ROUTE_VIA_LITELLM", "0") == "1"):
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
