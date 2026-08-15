"""Provider wizard — guided onboarding (validate only, no silent downloads)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


PROVIDERS = (
    "ollama",
    "litellm",
    "openai",
    "gemini",
    "openrouter",
    "huggingface",
)


def list_providers() -> list[dict[str, Any]]:
    return [
        {"id": "ollama", "label": "Ollama", "kind": "local", "default_url": os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")},
        {"id": "litellm", "label": "LiteLLM Gateway", "kind": "gateway", "default_url": os.getenv("JARVIS_LITELLM_URL", "http://127.0.0.1:4000")},
        {"id": "openai", "label": "OpenAI", "kind": "cloud", "env_key": "OPENAI_API_KEY"},
        {"id": "gemini", "label": "Google Gemini", "kind": "cloud", "env_key": "GEMINI_API_KEY"},
        {"id": "openrouter", "label": "OpenRouter", "kind": "cloud", "env_key": "OPENROUTER_API_KEY"},
        {"id": "huggingface", "label": "Hugging Face", "kind": "cloud", "env_key": "HF_TOKEN"},
    ]


def validate_provider(provider: str, *, url: str = "", api_key: str = "") -> dict[str, Any]:
    name = (provider or "").strip().lower()
    if name not in PROVIDERS:
        return {"ok": False, "error": f"unsupported provider: {provider}", "providers": list(PROVIDERS)}

    if name == "ollama":
        return _probe_ollama(url or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    if name == "litellm":
        return _probe_litellm(url or os.getenv("JARVIS_LITELLM_URL", "http://127.0.0.1:4000"))
    if name == "openai":
        from jarvis.integrations_product.secrets_bus import get_secret

        key = api_key or get_secret("openai_api_key")
        return _key_present("openai", key, hint="Save via Integrations or OPENAI_API_KEY")
    if name == "gemini":
        from jarvis.integrations_product.secrets_bus import get_secret

        key = api_key or get_secret("gemini_api_key")
        return _key_present("gemini", key, hint="Save via Integrations panel")
    if name == "openrouter":
        from jarvis.integrations_product.secrets_bus import get_secret

        key = api_key or get_secret("openrouter_api_key")
        return _key_present("openrouter", key, hint="Set OPENROUTER_API_KEY; route via LiteLLM")
    if name == "huggingface":
        from jarvis.integrations_product.secrets_bus import get_secret

        key = api_key or get_secret("hf_token")
        return _key_present("huggingface", key, hint="Save HF token in Integrations")
    return {"ok": False, "error": "unhandled"}


def _probe_ollama(url: str) -> dict[str, Any]:
    base = url.rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=0.5) as resp:
            data = json.loads(resp.read().decode())
        models = [m.get("name") for m in (data.get("models") or []) if m.get("name")]
        return {
            "ok": True,
            "provider": "ollama",
            "url": base,
            "models": models[:50],
            "model_count": len(models),
            "capabilities": ["chat", "embeddings", "vision_if_installed"],
            "message": f"Ollama reachable · {len(models)} model(s)",
        }
    except Exception as exc:
        return {"ok": False, "provider": "ollama", "url": base, "error": str(exc), "message": "Ollama not reachable"}


def _probe_litellm(url: str) -> dict[str, Any]:
    base = url.rstrip("/")
    try:
        req = urllib.request.Request(f"{base}/health/readiness", method="GET")
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            resp.read(256)
        return {
            "ok": True,
            "provider": "litellm",
            "url": base,
            "capabilities": ["gateway", "cloud_proxy"],
            "message": "LiteLLM readiness OK",
        }
    except Exception:
        try:
            with urllib.request.urlopen(f"{base}/v1/models", timeout=0.5) as resp:
                data = json.loads(resp.read().decode())
            models = [m.get("id") for m in (data.get("data") or []) if m.get("id")]
            return {
                "ok": True,
                "provider": "litellm",
                "url": base,
                "models": models[:40],
                "message": f"LiteLLM /v1/models OK · {len(models)}",
            }
        except Exception as exc:
            return {"ok": False, "provider": "litellm", "url": base, "error": str(exc)}


def _key_present(provider: str, key: str, *, hint: str) -> dict[str, Any]:
    ok = bool((key or "").strip())
    return {
        "ok": ok,
        "provider": provider,
        "key_configured": ok,
        "capabilities": ["cloud"],
        "message": "API key present" if ok else f"API key missing — {hint}",
        "next_step": "Open Integrations" if not ok else "Enable cloud routing via LiteLLM / JARVIS_CLOUD_INFERENCE",
        "integrations_deep_link": "integrations",
    }


def wizard_status() -> dict[str, Any]:
    results = {p["id"]: validate_provider(p["id"]) for p in list_providers()}
    return {
        "ok": True,
        "providers": list_providers(),
        "results": results,
        "terminology": {
            "provider": "Serves models (Ollama local, OpenAI cloud, …)",
            "gateway": "LiteLLM routes between providers",
            "model": "A concrete tag or cloud model id",
        },
    }
