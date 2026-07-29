"""Product bridges — Integrations supplies credentials/health; products own behavior."""

from __future__ import annotations

from typing import Any


def voice_bridge() -> dict[str, Any]:
    from jarvis.integrations_product.providers import enrich_provider, get_provider_def
    from jarvis.integrations_product.secrets_bus import is_set

    gemini = enrich_provider(get_provider_def("gemini") or {"id": "gemini"})
    openai = enrich_provider(get_provider_def("openai") or {"id": "openai"})
    return {
        "ok": True,
        "product": "Voice",
        "role": "credentials_for",
        "cloud_live": {
            "gemini_key_set": is_set("gemini_api_key"),
            "openai_key_set": is_set("openai_api_key"),
            "gemini": gemini,
            "openai": openai,
        },
        "note": "Voice owns Cloud Live behavior. Integrations owns keys and health.",
    }


def models_bridge() -> dict[str, Any]:
    from jarvis.integrations_product.providers import provider_matrix

    cloud = [p for p in provider_matrix() if p.get("owner_product") == "Models" or p["id"] in ("openai", "gemini", "openrouter", "anthropic", "ollama", "litellm")]
    return {
        "ok": True,
        "product": "Models",
        "role": "credentials_for",
        "providers": cloud,
        "note": "Models owns inference. Integrations validates keys and gateway health.",
    }


def vision_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "Vision",
        "role": "credentials_for",
        "note": "Vision uses local models by default; cloud vision keys would register here later.",
    }


def browser_bridge() -> dict[str, Any]:
    from jarvis.integrations_product.providers import enrich_provider, get_provider_def

    return {
        "ok": True,
        "product": "Browser",
        "role": "credentials_for",
        "searxng": enrich_provider(get_provider_def("searxng") or {"id": "searxng"}),
        "note": "Browser owns the agent; Integrations tracks SearXNG URL health.",
    }


def automation_bridge() -> dict[str, Any]:
    from jarvis.integrations_product.providers import enrich_provider, get_provider_def

    return {
        "ok": True,
        "product": "Automation",
        "role": "visibility",
        "inbound_webhook": enrich_provider(get_provider_def("automation_webhook") or {"id": "automation_webhook"}),
        "note": "Automation owns webhook execution; Integrations shows registry visibility.",
    }


def planner_bridge() -> dict[str, Any]:
    return {"ok": True, "product": "Planner", "role": "future", "note": "Future calendar/planner cloud providers register credentials here."}


def calendar_bridge() -> dict[str, Any]:
    return {"ok": True, "product": "Calendar", "role": "future", "note": "Future calendar OAuth/providers use Integrations secrets bus."}


def engineering_bridge() -> dict[str, Any]:
    from jarvis.integrations_product.providers import enrich_provider, get_provider_def
    from jarvis.integrations_product.secrets_bus import is_set

    return {
        "ok": True,
        "product": "Engineering",
        "role": "credentials_for",
        "meshy": enrich_provider(get_provider_def("meshy") or {"id": "meshy"}),
        "meshy_key_set": is_set("meshy_api_key"),
        "note": "Engineering owns Meshy generation; Integrations owns the key and test.",
    }
