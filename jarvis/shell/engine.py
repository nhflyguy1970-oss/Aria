"""Shell engine."""

from __future__ import annotations

from typing import Any

from jarvis.shell.design_tokens import DESIGN_TOKENS
from jarvis.shell.hotkeys import list_hotkeys, validate_registry
from jarvis.shell.product_home import checklist_payload
from jarvis.shell.terminology import BOUNDARIES, MENTAL_MODEL, TERMINOLOGY


def product_status() -> dict[str, Any]:
    errs = validate_registry()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "design_system": TERMINOLOGY["design_system"],
        "theme_default": DESIGN_TOKENS["theme_default"],
        "design_version": DESIGN_TOKENS["version"],
        "hotkey_count": len(list_hotkeys()),
        "hotkey_errors": errs,
        "healthy": len(errs) == 0,
        "boundaries": BOUNDARIES,
        "mental_model": MENTAL_MODEL,
        "terminology": TERMINOLOGY,
        "product_home": checklist_payload(),
    }
