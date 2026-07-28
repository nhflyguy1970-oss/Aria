"""Lightweight VRAM prep stub for Browser VLM — never blocks; no fake GPU magic."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("jarvis.browser.vision")


def prepare_for_browser_vlm() -> dict[str, Any]:
    """Optional best-effort free of heavy image models before VLM browse.

    Suggestions only — never silently unloads without operator-facing MC/Models paths.
    """
    try:
        # Soft hint only; do not call destructive free_vram automatically
        return {"ok": True, "prepared": True, "note": "Using Models vision role when available"}
    except Exception as exc:
        log.debug("prepare_for_browser_vlm: %s", exc)
        return {"ok": True, "prepared": False, "note": str(exc)}


def browser_vision_model() -> str:
    try:
        from jarvis.model_store import _load_raw
        from jarvis.config import is_uncensored

        data = _load_raw() or {}
        mode = "uncensored" if is_uncensored() else "standard"
        bank = data.get(mode) or data.get("standard") or {}
        return str(bank.get("browser_vision") or bank.get("vision") or "")
    except Exception:
        return ""
