"""Intent router — voice commands to products without dumping everything into Chat."""

from __future__ import annotations

import re
from typing import Any

# Patterns: (compiled regex, product, action, view)
_ROUTES: list[tuple[re.Pattern[str], str, str, str]] = [
    (re.compile(r"\b(open|show|go to)\s+(the\s+)?gallery\b", re.I), "gallery", "open", "gallery"),
    (re.compile(r"\b(open|show)\s+(image\s+)?(gen|generation|studio)\b", re.I), "image_generation", "open", "image-studio"),
    (re.compile(r"\b(generate|make|create)\s+(an?\s+)?image\b", re.I), "image_generation", "generate", "image-studio"),
    (re.compile(r"\b(open|show)\s+(video\s+)?(gen|generation|studio)\b", re.I), "video_generation", "open", "video-studio"),
    (re.compile(r"\b(generate|make|create)\s+(a\s+)?video\b", re.I), "video_generation", "generate", "video-studio"),
    (re.compile(r"\b(open|show)\s+(the\s+)?browser\b", re.I), "browser", "open", "browser"),
    (re.compile(r"\b(open|show)\s+(coding|code|editor)\b", re.I), "coding", "open", "coding"),
    (re.compile(r"\b(open|show)\s+(mission\s+control|health|status)\b", re.I), "mission_control", "open", "mission-control"),
    (re.compile(r"\b(open|show)\s+(home\s+assistant|ha)\b", re.I), "home_assistant", "open", "home"),
    (re.compile(r"\b(open|show)\s+(projects?)\b", re.I), "projects", "open", "projects"),
    (re.compile(r"\b(open|show)\s+(the\s+)?planner\b", re.I), "planner", "open", "planner"),
    (re.compile(r"\b(open|show)\s+(documents?|docs)\b", re.I), "documents", "open", "documents"),
    (re.compile(r"\b(open|show)\s+(audio\s+studio|studio)\b", re.I), "audio_studio", "open", "audio"),
    (re.compile(r"\b(open|show)\s+(voice|voice\s+settings)\b", re.I), "voice", "open", "voice"),
    (re.compile(r"\b(open|show)\s+(chat|conversation)\b", re.I), "chat", "open", "chat"),
    (re.compile(r"\b(mute|stop\s+speaking|be\s+quiet)\b", re.I), "voice", "stop_speak", ""),
    (re.compile(r"\b(speak\s+replies|unmute|read\s+aloud)\b", re.I), "voice", "speak_on", ""),
]


def route_utterance(text: str) -> dict[str, Any] | None:
    """Return a structured route or None if Chat/assistant should handle it."""
    utterance = (text or "").strip()
    if not utterance:
        return None
    for pattern, product, action, view in _ROUTES:
        if pattern.search(utterance):
            return {
                "kind": "product_command",
                "product": product,
                "action": action,
                "view": view,
                "utterance": utterance,
                "confidence": 0.85,
            }
    return None


def apply_route(route: dict[str, Any]) -> dict[str, Any]:
    """Execute a product route (navigation / voice policy). Chat is not opened unless product is chat."""
    product = route.get("product") or ""
    action = route.get("action") or "open"
    view = route.get("view") or ""

    if product == "voice" and action == "stop_speak":
        try:
            from jarvis.voice_product.engine import stop_speaking

            stop_speaking()
        except Exception:
            pass
        return {"ok": True, "handled": True, "reply": "Stopped speaking.", "route": route}

    if product == "voice" and action == "speak_on":
        try:
            from jarvis.voice_product.settings import save_unified_settings

            save_unified_settings({"speak_replies": True})
        except Exception:
            pass
        return {"ok": True, "handled": True, "reply": "Speak replies enabled.", "route": route}

    # Navigation is returned to the client; server records activity
    try:
        from jarvis.action_log import log_event

        log_event(
            "voice_intent",
            product=product,
            action=action,
            view=view,
            utterance=(route.get("utterance") or "")[:200],
        )
    except Exception:
        pass

    return {
        "ok": True,
        "handled": True,
        "navigate": view or None,
        "product": product,
        "action": action,
        "reply": f"Opening {product.replace('_', ' ')}." if action == "open" else f"Routing to {product}.",
        "route": route,
    }
