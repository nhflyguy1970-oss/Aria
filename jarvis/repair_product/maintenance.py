"""Maintenance mode — suppress expected alerts during planned work."""

from __future__ import annotations

import time
from typing import Any

from jarvis.repair_product import store
from jarvis.repair_product.terminology import DISCLAIMER

KNOWN_REASONS = (
    "updating_aria",
    "installing_models",
    "rebuilding_indexes",
    "large_ocr_import",
    "mass_document_import",
    "training",
    "git_operations",
    "bulk_file_movement",
    "other",
)


def status() -> dict[str, Any]:
    data = store.maintenance_state()
    active = bool(data.get("enabled"))
    return {
        "ok": True,
        "enabled": active,
        "reason": data.get("reason") or "",
        "note": data.get("note") or "",
        "started_at": data.get("started_at"),
        "suppress_alerts": active,
        "delay_recommendations": active,
        "known_reasons": list(KNOWN_REASONS),
        "disclaimer": DISCLAIMER,
    }


def enable(*, reason: str = "other", note: str = "", actor: str = "jeff") -> dict[str, Any]:
    reason = (reason or "other").strip().lower().replace(" ", "_")
    if reason not in KNOWN_REASONS:
        reason = "other"
    payload = {
        "enabled": True,
        "reason": reason,
        "note": note,
        "actor": actor,
        "started_at": time.time(),
    }
    store.save_maintenance_state(payload)
    return {"ok": True, **status(), "message": f"Maintenance mode enabled ({reason}). Expected alerts suppressed."}


def disable(*, actor: str = "jeff", run_verification: bool = True) -> dict[str, Any]:
    prev = store.maintenance_state()
    store.save_maintenance_state(
        {
            "enabled": False,
            "reason": "",
            "note": "",
            "actor": actor,
            "ended_at": time.time(),
            "previous": prev,
        }
    )
    verification = None
    if run_verification:
        from jarvis.repair_product.engine import scan_issues

        verification = scan_issues(force=True)
    return {
        "ok": True,
        **status(),
        "message": "Maintenance mode ended." + (" Full health verification completed." if run_verification else ""),
        "verification": verification,
    }


def should_suppress_recommendations() -> bool:
    return bool(store.maintenance_state().get("enabled"))
