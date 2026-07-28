"""Voice commands for Gallery — confirm destructive ops."""

from __future__ import annotations

import re
from typing import Any


def handle_voice_command(text: str, *, assistant=None) -> dict[str, Any]:
    lower = (text or "").strip().lower()
    if not lower:
        return {"ok": False, "message": "Empty voice command"}

    if re.search(r"\b(buy|purchase|pay|upload to cloud|post to)\b", lower):
        return {"ok": False, "blocked": True, "message": "Voice cannot perform that action"}

    if "show last" in lower or "last image" in lower:
        from jarvis.gallery_product.library import list_images

        imgs = (list_images(limit=1).get("images") or [])
        if not imgs:
            return {"ok": False, "message": "No images in Gallery"}
        return {"ok": True, "action": "show", "name": imgs[0]["name"], "open_view": "gallery"}

    if "describe" in lower:
        return {"ok": True, "action": "describe_selected", "message": "Describe requires a selected image", "open_view": "gallery"}

    if "upscale" in lower:
        return {"ok": True, "action": "upscale_selected", "message": "Upscale selected image", "open_view": "gallery"}

    if "variation" in lower or "generate another" in lower:
        return {"ok": True, "action": "variation_selected", "open_view": "gallery"}

    if re.search(r"\b(delete|trash|remove)\b", lower):
        return {
            "ok": False,
            "needs_confirm": True,
            "action": "soft_delete_selected",
            "message": "Confirm delete: say confirm delete or use Gallery Trash",
        }

    return {"ok": False, "message": f"Unrecognized Gallery voice command: {text[:80]}"}
