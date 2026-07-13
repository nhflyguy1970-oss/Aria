"""Aria Core — Services (delegates to jarvis.services)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("services")


def list_managed_services() -> list[str]:
    try:
        from jarvis import services as svc

        catalog = getattr(svc, "SERVICES", None) or getattr(svc, "SERVICE_IDS", None)
        if isinstance(catalog, dict):
            return sorted(str(k) for k in catalog.keys())
        if isinstance(catalog, (list, tuple, set)):
            return sorted(str(x) for x in catalog)
    except Exception:
        pass
    return ["ollama", "comfyui", "homeassistant"]


def services_module() -> Any:
    from jarvis import services

    return services
