"""Vision → Coding workflow — screenshot → likely files → Coding proposal.

Never bypasses Coding propose→apply.
"""

from __future__ import annotations

from typing import Any


def vision_to_coding(
    assistant: Any,
    *,
    hint: str = "",
    use_live_screenshot: bool = True,
    image_path: str = "",
) -> dict[str, Any]:
    path = image_path
    if use_live_screenshot and not path:
        from jarvis.browser_agent import screenshot

        shot = screenshot(label="v2c", reason="vision_to_coding")
        if not shot.get("ok"):
            return {
                "ok": False,
                "error": shot.get("message") or "Could not capture browser screenshot",
                "recovery": "Navigate to the broken page, then retry",
            }
        path = shot["path"]

    from jarvis.coding_product.vision_fix import vision_bugfix

    result = vision_bugfix(
        assistant,
        image_path=path,
        hint=hint or "UI issue visible in browser screenshot",
        propose=True,
    )
    result["routed_through"] = "coding"
    result["auto_applied"] = False
    result["note"] = "Review and Apply only in Coding — Browser never writes code."
    return result
