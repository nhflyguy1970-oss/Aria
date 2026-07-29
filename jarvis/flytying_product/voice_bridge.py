"""Voice bench commands — session manager + shared Voice speak_text (never duplicate recipe logic)."""

from __future__ import annotations

from typing import Any


def _current_step_text(session: dict[str, Any]) -> str:
    recipe_id = (session.get("recipe_id") or "").strip()
    idx = int(session.get("step_idx") or 0)
    if not recipe_id:
        return "No recipe loaded in this session."
    from jarvis.flytying import bridge

    recipe = bridge.get_recipe(recipe_id) or {}
    steps = list(recipe.get("steps") or [])
    name = recipe.get("fly_name") or recipe.get("name") or session.get("recipe_name") or recipe_id
    if not steps:
        return f"{name}: no steps available."
    idx = max(0, min(idx, len(steps) - 1))
    return f"Step {idx + 1} of {len(steps)} for {name}: {steps[idx]}"


def _speak(text: str, *, assistant=None, speak: bool = True) -> dict[str, Any]:
    if not speak:
        return {"ok": True, "spoken": False, "text": text}
    from jarvis.voice_product.engine import speak_text

    result = speak_text(text, assistant=assistant, force=True, source="flytying_bench")
    return {"ok": bool(result.get("ok", True)), "spoken": True, "text": text, "tts": result}


def bench_command(
    command: str,
    *,
    session_id: str = "",
    assistant=None,
    speak: bool = True,
) -> dict[str, Any]:
    """
    Hands-free bench commands: next | prev | repeat | read | pause | resume
    Session manager owns step state; Voice only speaks.
    """
    from jarvis.flytying_product import sessions as session_mgr

    cmd = (command or "").strip().lower()
    if cmd in ("next_step", "next"):
        cmd = "next"
    elif cmd in ("prev_step", "previous", "previous_step", "prev", "back"):
        cmd = "prev"
    elif cmd in ("repeat_step", "again"):
        cmd = "repeat"
    elif cmd in ("read_recipe", "read", "status"):
        cmd = "read" if cmd != "status" else "repeat"
    elif cmd in ("pause_session",):
        cmd = "pause"
    elif cmd in ("resume_session",):
        cmd = "resume"

    session = session_mgr.get_session(session_id)
    if not session and cmd not in ("pause", "resume"):
        return {"ok": False, "message": "no_active_session", "error": "No active tying session", "bridge": "voice_product"}

    if cmd == "next":
        max_steps = None
        try:
            from jarvis.flytying import bridge

            recipe = bridge.get_recipe((session or {}).get("recipe_id") or "") if session else None
            if recipe:
                max_steps = len(list(recipe.get("steps") or [])) or None
        except Exception:
            pass
        session = session_mgr.next_step(session_id or (session or {}).get("id") or "", max_steps=max_steps)
        text = _current_step_text(session)
        spoken = _speak(text, assistant=assistant, speak=speak)
        return {"ok": True, "command": "next", "session": session, "step_text": text, "bridge": "voice_product", **spoken}

    if cmd == "prev":
        session = session_mgr.prev_step(session_id or (session or {}).get("id") or "")
        text = _current_step_text(session)
        spoken = _speak(text, assistant=assistant, speak=speak)
        return {"ok": True, "command": "prev", "session": session, "step_text": text, "bridge": "voice_product", **spoken}

    if cmd == "repeat":
        text = _current_step_text(session or {})
        spoken = _speak(text, assistant=assistant, speak=speak)
        return {"ok": True, "command": "repeat", "session": session, "step_text": text, "bridge": "voice_product", **spoken}

    if cmd == "read":
        recipe_id = (session or {}).get("recipe_id") or ""
        from jarvis.flytying import bridge

        recipe = bridge.get_recipe(recipe_id) if recipe_id else None
        if not recipe:
            return {"ok": False, "message": "recipe_not_found", "session": session, "bridge": "voice_product"}
        name = recipe.get("fly_name") or recipe.get("name") or recipe_id
        mats = recipe.get("materials") or []
        steps = recipe.get("steps") or []
        parts = [f"Recipe: {name}."]
        if mats:
            parts.append("Materials: " + "; ".join(str(m) for m in mats[:12]) + ".")
        if steps:
            parts.append(f"{len(steps)} steps. Current: {_current_step_text(session or {})}")
        text = " ".join(parts)
        spoken = _speak(text, assistant=assistant, speak=speak)
        return {
            "ok": True,
            "command": "read",
            "session": session,
            "recipe": {"id": recipe_id, "name": name},
            "step_text": text,
            "bridge": "voice_product",
            **spoken,
        }

    if cmd == "pause":
        session = session_mgr.pause_session(session_id or (session or {}).get("id") or "")
        spoken = _speak("Session paused.", assistant=assistant, speak=speak)
        return {"ok": True, "command": "pause", "session": session, "bridge": "voice_product", **spoken}

    if cmd == "resume":
        session = session_mgr.resume_session(session_id or (session or {}).get("id") or "")
        text = "Session resumed. " + _current_step_text(session)
        spoken = _speak(text, assistant=assistant, speak=speak)
        return {"ok": True, "command": "resume", "session": session, "step_text": text, "bridge": "voice_product", **spoken}

    return {
        "ok": False,
        "message": f"unknown_command:{command}",
        "error": f"unknown bench action: {command}",
        "supported": ["next", "prev", "repeat", "read", "pause", "resume"],
        "bridge": "voice_product",
    }
