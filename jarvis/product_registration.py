"""Fail-loud product / route registration — measured, never silent."""

from __future__ import annotations

import logging
import os
import traceback
from typing import Any, Callable

_log = logging.getLogger("jarvis.product_registration")

# Process-global registration ledger (reset only on process restart)
_REGISTERED: list[str] = []
_FAILED: list[dict[str, str]] = []

REQUIRED_PRODUCTS: frozenset[str] = frozenset(
    {
        "gallery_product",
        "image_generation",
        "video_generation",
        "voice_product",
        "vision_product",
        "search_product",
        "settings_product",
        "certification_product",
        "dashboard_product",
        "layouts_product",
        "notifications_product",
        "health_product",
        "repair_product",
        "integrity_product",
        "shell",
        "calendar",
        "provider_health",
        "activity_inbox",
    }
)


def reset_for_tests() -> None:
    _REGISTERED.clear()
    _FAILED.clear()


def registration_status() -> dict[str, Any]:
    missing = sorted(REQUIRED_PRODUCTS.difference(_REGISTERED))
    return {
        "ok": len(_FAILED) == 0 and not missing,
        "registered": list(_REGISTERED),
        "failed": list(_FAILED),
        "required": sorted(REQUIRED_PRODUCTS),
        "missing_required": missing,
        "strict": _strict(),
    }


def _strict() -> bool:
    return os.getenv("JARVIS_PRODUCT_REGISTER_STRICT", "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def register(
    name: str,
    fn: Callable[..., Any],
    *args: Any,
    required: bool = False,
    **kwargs: Any,
) -> bool:
    """
    Call a product/route registrar. On failure: log + record (never silent).

    If required=True or JARVIS_PRODUCT_REGISTER_STRICT=1, re-raise.
    Returns True on success, False on soft failure.
    """
    try:
        fn(*args, **kwargs)
        _REGISTERED.append(name)
        _log.info("Registered product routes: %s", name)
        return True
    except Exception as exc:
        entry = {
            "name": name,
            "error": str(exc),
            "type": type(exc).__name__,
            "traceback": traceback.format_exc()[-2000:],
        }
        _FAILED.append(entry)
        _log.exception("Product route registration FAILED: %s — %s", name, exc)
        if required or name in REQUIRED_PRODUCTS or _strict():
            raise
        return False
