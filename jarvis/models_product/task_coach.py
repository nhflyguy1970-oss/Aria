"""Task coach — suggest better models; never silent switch."""

from __future__ import annotations

from typing import Any


def suggest_for_prompt(prompt: str, *, current_model: str = "") -> dict[str, Any]:
    text = (prompt or "").lower()
    suggestions: list[dict[str, Any]] = []
    if any(k in text for k in ("code", "refactor", "python", "bug", "compile", "function")):
        suggestions.append({
            "kind": "coding",
            "message": "This looks like coding. A coding-role model may be better.",
            "role": "coding",
            "confirm_required": True,
        })
    if any(k in text for k in ("image", "screenshot", "photo", "vision", "describe this picture")):
        suggestions.append({
            "kind": "vision",
            "message": "This looks like vision. Use the Vision role model.",
            "role": "vision",
            "confirm_required": True,
        })
    if any(k in text for k in ("reason step", "think carefully", "analyze deeply", "prove")):
        suggestions.append({
            "kind": "reasoning",
            "message": "This looks like reasoning. Consider the Reasoning role model.",
            "role": "reasoning",
            "confirm_required": True,
        })
    return {
        "ok": True,
        "auto_switch": False,
        "current_model": current_model,
        "suggestions": suggestions,
        "message": "Suggestions only — confirm in Models Home or Chat before switching.",
    }
