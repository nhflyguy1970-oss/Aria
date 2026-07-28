"""Models Home snapshot — single destination payload."""

from __future__ import annotations

from typing import Any

from jarvis.model_store import (
    CANONICAL_ROLES,
    ROLE_LABELS,
    get_all_settings,
    get_missing_models,
)


PRIMARY_ROLES = ("conversation", "coding", "vision", "image", "embedding")
ADVANCED_ROLES = tuple(r for r in CANONICAL_ROLES if r not in PRIMARY_ROLES)


def models_home_snapshot() -> dict[str, Any]:
    settings = get_all_settings()
    active = settings.get("active") or {}
    from jarvis.models_product.catalog import build_catalog, build_model_card
    from jarvis.models_product.vram_advisor import advise_vram
    from jarvis.models_product.providers import wizard_status
    from jarvis.models_product.recommender import recommend_stacks
    from jarvis.models_product.pull_manager import get_pull_state
    from jarvis.models_product.switch import describe_switch_contract
    from jarvis.models_product.packs import list_packs

    free = None
    try:
        from jarvis.gpu import free_vram_mb

        free = round(float(free_vram_mb() or 0) / 1024.0, 2)
    except Exception:
        pass

    loaded = []
    try:
        from jarvis.resource_router import ollama_loaded_models

        loaded = ollama_loaded_models() or []
    except Exception:
        loaded = []

    role_cards = {}
    for role in CANONICAL_ROLES:
        tag = active.get(role) or active.get({"conversation": "general", "coding": "coder", "embedding": "embed"}.get(role, ""), "")
        if tag:
            role_cards[role] = build_model_card(tag, installed=settings.get("installed") or [], free_vram_gb=free)

    health = {
        "ollama_running": bool(settings.get("ollama_running") or settings.get("installed")),
        "loaded_count": len(loaded),
        "free_vram_gb": free,
        "missing": get_missing_models(),
        "provider_summary": "Ollama local · LiteLLM optional · cloud via Integrations",
    }

    # Lightweight provider ping
    try:
        from jarvis.models_product.providers import validate_provider

        health["ollama"] = validate_provider("ollama")
    except Exception as exc:
        health["ollama"] = {"ok": False, "error": str(exc)}

    catalog = build_catalog(installed_only=False, sort="installed")
    return {
        "ok": True,
        "product": "models",
        "title": "Models",
        "philosophy": "Models configures. Mission Control monitors.",
        "boundaries": {
            "owns": [
                "role_assignments",
                "model_registry",
                "provider_configuration",
                "routing_configuration",
                "presets",
                "catalog",
                "recommendations",
                "model_selection",
            ],
            "does_not_own": [
                "provider_health_ops",
                "warm_unload",
                "recovery",
                "vram_health_console",
            ],
            "mission_control_deep_link": "mc:inference",
            "integrations_deep_link": "integrations",
        },
        "terminology": {
            "provider": "Runtime that serves models (Ollama, LiteLLM, OpenAI, …)",
            "gateway": "Routing layer between providers",
            "model": "Concrete weights tag or cloud id",
            "role": "Job slot Aria fills with a model",
            "profile": "standard vs uncensored banks",
            "runtime": "What is loaded/warm right now",
            "registry": "Persistent role→model map",
            "policy": "Optional permission pack",
        },
        "settings": settings,
        "roles": {
            "primary": [{"id": r, "label": ROLE_LABELS.get(r, r), "model": active.get(r)} for r in PRIMARY_ROLES],
            "advanced": [{"id": r, "label": ROLE_LABELS.get(r, r), "model": active.get(r)} for r in ADVANCED_ROLES],
            "cards": role_cards,
        },
        "health": health,
        "loaded_models": loaded,
        "catalog": catalog,
        "pull": get_pull_state(),
        "providers": wizard_status(),
        "recommendations": recommend_stacks(),
        "packs": list_packs(),
        "switch_contract": describe_switch_contract(),
        "vram_sample": advise_vram(active.get("conversation") or "qwen2.5:7b"),
        "first_run": {
            "needed": not (settings.get("installed") or []),
            "steps": [
                "Detect hardware",
                "Review recommended stack",
                "Pull missing models",
                "Verify readiness",
            ],
        },
    }


def export_config() -> dict[str, Any]:
    settings = get_all_settings()
    return {
        "ok": True,
        "version": 1,
        "product": "models",
        "mode": settings.get("mode"),
        "standard": settings.get("standard"),
        "uncensored": settings.get("uncensored"),
        "exported_at": __import__("time").time(),
    }


def import_config(payload: dict[str, Any], *, mode: str = "") -> dict[str, Any]:
    from jarvis.models_product.switch import apply_model_change, ModelChangeRequest

    mode_key = mode or payload.get("mode") or "standard"
    roles = payload.get(mode_key) or payload.get("roles") or payload.get("standard") or {}
    return apply_model_change(ModelChangeRequest(scope="role_default", roles=dict(roles), mode=mode_key, reason="import"))
