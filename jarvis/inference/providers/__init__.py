"""Native cloud provider adapters behind ARIA's inference gateway.

ARIA model ids name the provider: ``openai/<model>``, ``anthropic/<model>``,
``google/<model>`` (``gemini/<model>`` is accepted as an alias). No model name
is built in; what an account can use comes from ``discover()``, cached in
``data/cloud_models.json`` together with the capabilities the provider reports.

All three adapters bill the provider's *API* account. A ChatGPT, Claude or
Google subscription does not authorize API inference, and these adapters never
use a CLI's cached subscription login; subscription-backed coding CLIs are a
separate integration (Phase 5) with their own billing mode.
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.inference.providers.anthropic_messages import AnthropicMessages
from jarvis.inference.providers.base import ModelInfo, ProviderAdapter, circuit_open, circuit_status
from jarvis.inference.providers.gemini import GeminiAPI
from jarvis.inference.providers.openai_responses import OpenAIResponses

DISCOVERY_FILE = DATA_DIR / "cloud_models.json"
ADAPTER_CLASSES = {"openai": OpenAIResponses, "anthropic": AnthropicMessages, "google": GeminiAPI}
BILLING = {
    "openai": "api",
    "anthropic": "api",
    "google": "api",
    # Phase 5 (not integrated): "codex_cli", "claude_code", "agy" — subscription
    # or API depending on how each CLI is signed in; never inferred.
}

_instances: dict[str, ProviderAdapter] = {}
_lock = threading.Lock()


def adapter_for(provider: str) -> ProviderAdapter | None:
    cls = ADAPTER_CLASSES.get(provider)
    if cls is None:
        return None
    with _lock:
        if provider not in _instances:
            _instances[provider] = cls()
        return _instances[provider]


def split_model(aria_model: str) -> tuple[str, str]:
    """``anthropic/claude-x`` → ("anthropic", "claude-x"); local ids → ("ollama", id)."""
    from jarvis.inference.boundary import provider_of

    provider = provider_of(aria_model)
    if provider == "ollama":
        return "ollama", aria_model
    name = aria_model
    for prefix in ("openai/", "anthropic/", "google/", "gemini/"):
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
            break
    return provider, name


def has_credentials(provider: str) -> bool:
    adapter = adapter_for(provider)
    return bool(adapter) and adapter.credential_status().get("state") == "credentials_present"


# ------------------------------------------------------------------ discovery cache


def _load_cache() -> dict[str, Any]:
    try:
        return json.loads(DISCOVERY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def discover(provider: str) -> dict[str, Any]:
    """Ask the provider what this account can use (free; still outbound traffic,
    so it obeys cloud-disable, offline mode and the provider allowlist)."""
    from jarvis.live_data_guard import assert_live_write_allowed

    adapter = adapter_for(provider)
    if adapter is None:
        raise ValueError(f"unknown provider {provider!r}")
    models = adapter.discover()
    cache = _load_cache()
    cache[provider] = {
        "at": time.time(),
        "models": [
            {
                "id": m.id,
                "aria_id": m.aria_id,
                "capabilities": sorted(m.capabilities),
                "context_window": m.context_window,
                "max_output_tokens": m.max_output_tokens,
                "display_name": m.display_name,
            }
            for m in models
        ],
    }
    assert_live_write_allowed(DISCOVERY_FILE)
    DISCOVERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERY_FILE.write_text(json.dumps(cache, indent=1), encoding="utf-8")
    return cache[provider]


def discovered_model(aria_model: str) -> dict[str, Any] | None:
    provider, name = split_model(aria_model)
    for m in (_load_cache().get(provider) or {}).get("models") or []:
        if m.get("id") == name:
            return m
    return None


def discovered_capabilities(aria_model: str) -> frozenset[str] | None:
    model = discovered_model(aria_model)
    if not model or not model.get("capabilities"):
        return None
    return frozenset(model["capabilities"])


def status() -> dict[str, Any]:
    """Per-provider credential state, billing, discovery and circuit — no network."""
    cache = _load_cache()
    out = {}
    for provider in ADAPTER_CLASSES:
        adapter = adapter_for(provider)
        disc = cache.get(provider) or {}
        out[provider] = {
            "label": adapter.label,
            "billing": BILLING[provider],
            "credentials": adapter.credential_status(),
            "discovered_models": len(disc.get("models") or []),
            "discovered_at": disc.get("at"),
            "circuit_open": circuit_open(provider),
        }
    out["_circuits"] = circuit_status()
    return out


__all__ = [
    "ADAPTER_CLASSES",
    "BILLING",
    "ModelInfo",
    "ProviderAdapter",
    "adapter_for",
    "discover",
    "discovered_capabilities",
    "discovered_model",
    "has_credentials",
    "split_model",
    "status",
]
