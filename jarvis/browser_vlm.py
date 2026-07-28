"""VLM-guided browser clicks — screenshot → vision model → coordinates."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.browser.vlm")

_VLM_PROMPT = """You are a browser automation assistant. Look at this screenshot.
The user wants: {goal}

Reply with ONLY one JSON object (no markdown):
{{"action":"click","x":123,"y":456,"reason":"short"}}
OR if done: {{"action":"done","summary":"what was accomplished"}}
OR if stuck: {{"action":"fail","reason":"why"}}
Use pixel coordinates from the top-left of the image."""


def _parse_vlm_json(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        m = re.search(r"\{\s*\"action\"\s*:", text)
        if m:
            start = m.start()
            end = text.rfind("}") + 1
    if start < 0:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None


def vlm_plan_click(screenshot_path: str, goal: str, *, assistant=None) -> dict[str, Any]:
    path = Path(screenshot_path)
    if not path.is_file():
        return {"ok": False, "error": f"Screenshot missing: {path}"}

    from jarvis.browser_product.vision_support import prepare_for_browser_vlm

    prepare_for_browser_vlm()

    try:
        if assistant is not None:
            vision = assistant.vision
        else:
            from jarvis.assistant_instance import get_assistant

            vision = get_assistant().vision

        prompt = _VLM_PROMPT.format(goal=goal[:400])
        # Prefer vision role; task stays describe for model_store compatibility
        raw = vision.analyze(prompt, str(path), task="describe")
        if isinstance(raw, str) and raw.startswith("ERROR:"):
            return {"ok": False, "error": raw}
        plan = _parse_vlm_json(str(raw))
        if not plan:
            return {"ok": False, "error": "Vision model did not return valid JSON", "raw": str(raw)[:300]}
        return {"ok": True, "plan": plan, "raw": str(raw)[:500]}
    except Exception as exc:
        log.warning("VLM plan failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def vlm_click_at(x: int, y: int) -> dict[str, Any]:
    from jarvis.browser_product.session import append_step, get_page, is_paused

    if is_paused():
        return {"ok": False, "message": "Agent paused"}
    page = get_page()
    if not page:
        return {"ok": False, "message": "No browser page"}
    try:
        page.mouse.click(int(x), int(y))
        append_step("vlm_click", f"{x},{y}")
        return {"ok": True, "x": x, "y": y}
    except Exception as exc:
        append_step("vlm_click", str(exc), ok=False)
        return {"ok": False, "message": str(exc)}
