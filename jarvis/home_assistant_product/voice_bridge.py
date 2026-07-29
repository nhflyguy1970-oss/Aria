"""Voice Home Mode — Voice product speaks; Smart Home engine executes (never duplicate Voice)."""

from __future__ import annotations

from typing import Any


def _speak(text: str, *, assistant=None, speak: bool = True) -> dict[str, Any]:
    if not speak:
        return {"ok": True, "spoken": False, "text": text}
    from jarvis.voice_product.engine import speak_text

    result = speak_text(text, assistant=assistant, force=True, source="smarthome_home")
    return {"ok": bool(result.get("ok", True)), "spoken": True, "text": text, "tts": result}


def home_command(
    command: str,
    *,
    target: str = "",
    scene: str = "",
    brightness: int | None = None,
    color_name: str = "",
    assistant=None,
    speak: bool = True,
) -> dict[str, Any]:
    """
    Hands-free home: on | off | toggle | dim | brighten | scene | status |
    goodnight | good_morning | heading_out
    """
    from jarvis.home_assistant_product import engine

    cmd = (command or "").strip().lower().replace("-", "_").replace(" ", "_")
    if cmd in ("turn_on", "on"):
        cmd = "on"
    elif cmd in ("turn_off", "off"):
        cmd = "off"
    elif cmd in ("house_status", "status", "home_status"):
        cmd = "status"
    elif cmd in ("good_morning", "morning"):
        cmd = "good_morning"
    elif cmd in ("heading_out", "leave", "away"):
        cmd = "heading_out"

    if cmd == "status":
        result = engine.house_status()
        spoken = _speak(result.get("message") or "House status unavailable.", assistant=assistant, speak=speak)
        return {"ok": bool(result.get("ok")), "command": "status", "bridge": "voice_product", **result, **spoken}

    if cmd in ("scene", "set_scene") or scene:
        sc = scene or target
        result = engine.activate_scene(sc, source="voice")
        spoken = _speak(result.get("message") or sc, assistant=assistant, speak=speak)
        return {"ok": bool(result.get("ok")), "command": "scene", "bridge": "voice_product", **result, **spoken}

    if cmd == "goodnight":
        result = engine.activate_scene("movie mode", source="voice")
        if not result.get("ok"):
            result = engine.activate_scene("relax", source="voice")
        spoken = _speak(result.get("message") or "Good night.", assistant=assistant, speak=speak)
        return {"ok": bool(result.get("ok")), "command": "goodnight", "bridge": "voice_product", **result, **spoken}

    if cmd == "good_morning":
        result = engine.activate_scene("sunlight", source="voice")
        if not result.get("ok"):
            result = engine.activate_scene("work mode", source="voice")
        spoken = _speak(result.get("message") or "Good morning.", assistant=assistant, speak=speak)
        return {"ok": bool(result.get("ok")), "command": "good_morning", "bridge": "voice_product", **result, **spoken}

    if cmd == "heading_out":
        from jarvis.home_assistant import leave_scene

        sc = leave_scene() or "leaving"
        result = engine.activate_scene(sc, source="voice")
        spoken = _speak(result.get("message") or "Heading out.", assistant=assistant, speak=speak)
        return {"ok": bool(result.get("ok")), "command": "heading_out", "bridge": "voice_product", **result, **spoken}

    if cmd in ("on", "off", "toggle", "dim", "brighten"):
        if not target:
            return {"ok": False, "error": "target required", "bridge": "voice_product"}
        result = engine.control_device(
            target,
            cmd,
            brightness=brightness,
            color_name=color_name or None,
            source="voice",
        )
        spoken = _speak(result.get("message") or f"{cmd} {target}", assistant=assistant, speak=speak)
        return {"ok": bool(result.get("ok")), "command": cmd, "bridge": "voice_product", **result, **spoken}

    return {
        "ok": False,
        "error": f"unknown_command:{command}",
        "supported": ["on", "off", "toggle", "dim", "brighten", "scene", "status", "goodnight", "good_morning", "heading_out"],
        "bridge": "voice_product",
    }
