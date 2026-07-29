"""Mission Control bridge for Integrations."""

from __future__ import annotations

from typing import Any


def integrations_mission_panel() -> dict[str, Any]:
    from jarvis.integrations_product.engine import product_status
    from jarvis.integrations_product.health import recovery_status
    from jarvis.integrations_product.secrets_bus import storage_info
    from jarvis.integrations_product.status_bus import get_integrations_state
    from jarvis.integrations_product.usage import list_usage

    status = product_status()
    recovery = recovery_status()
    state = get_integrations_state()
    storage = storage_info()
    failures = [u for u in list_usage(15) if not u.get("ok")][:5]
    warnings = []
    if storage.get("world_readable"):
        warnings.append("Secret file may be world-readable — run chmod 600")
    if not storage.get("encrypted"):
        warnings.append("Secrets stored in plaintext jarvis.env")
    if failures:
        warnings.append(f"{len(failures)} recent connection failure(s)")

    return {
        "product": "Integrations",
        "state": state.get("state") or status.get("state") or "idle",
        "detail": state.get("detail") or "",
        "configured": status.get("configured") or 0,
        "available": status.get("available") or 0,
        "total": status.get("total") or 0,
        "healthy": recovery.get("ready"),
        "warnings": warnings,
        "failed": len(failures),
        "recent_failures": failures,
        "storage": {
            "encrypted": False,
            "backend": storage.get("backend"),
            "world_readable": storage.get("world_readable"),
        },
        "recovery": {
            "ready": recovery.get("ready"),
            "hint": recovery.get("hint"),
            "steps_done": sum(1 for s in (recovery.get("steps") or []) if s.get("done")),
            "steps_total": len(recovery.get("steps") or []),
        },
        "errors": [{"severity": "warning", "message": w} for w in warnings[:4]],
        "deep_links": {
            "home": "#integrations",
            "status": "/api/integrations/product",
            "recovery": "/api/integrations/product/recovery",
            "mission": "/api/integrations/product/mission",
            "diagnostics": "/api/integrations/product/diagnostics",
            "providers": "/api/integrations/product/providers",
        },
    }
