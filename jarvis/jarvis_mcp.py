"""Non-coding MCP tools — briefing, environment, HA, journal, documents, image queue.

C6: Prefer the serve-registered assistant when co-located. Otherwise proxy to
the live Aria HTTP serve process so MCP never constructs a divergent assistant.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlencode

log = logging.getLogger("jarvis.jarvis_mcp")


def _serve_base_url() -> str:
    from jarvis.lan import client_base_url

    return client_base_url().rstrip("/")


def _http_json(
    method: str,
    path: str,
    *,
    form: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    query: dict[str, str] | None = None,
    timeout: float = 120.0,
) -> dict[str, Any]:
    url = f"{_serve_base_url()}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"
    data = None
    headers = {"Accept": "application/json"}
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif form is not None:
        data = urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"detail": body}
        if isinstance(parsed, dict):
            return {
                "ok": False,
                "message": str(parsed.get("message") or parsed.get("detail") or f"HTTP {exc.code}"),
                "http_status": exc.code,
                **{k: v for k, v in parsed.items() if k not in ("ok", "message")},
            }
        return {"ok": False, "message": f"HTTP {exc.code}", "detail": body}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "ok": False,
            "message": (
                f"Aria serve unreachable at {_serve_base_url()} ({exc}). "
                "Start `python main.py serve` (or tray) before using MCP domain tools."
            ),
        }
    try:
        parsed = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return {"ok": False, "message": "invalid JSON from Aria serve", "raw": raw[:500]}
    if isinstance(parsed, dict):
        return parsed
    return {"ok": True, "data": parsed}


def _shared_assistant():
    from jarvis.assistant_instance import get_assistant_or_none

    return get_assistant_or_none()


def handle_jarvis_mcp_tool(name: str, arguments: dict) -> dict[str, Any]:
    if name == "jarvis_environment":
        from jarvis.environment import snapshot

        return {"ok": True, **snapshot(include_resources=True)}

    if name == "jarvis_ha_toggle":
        from jarvis.home_assistant import call_service, ha_enabled

        if not ha_enabled():
            return {"ok": False, "message": "Home Assistant not configured"}
        entity_id = (arguments.get("entity_id") or "").strip()
        action = (arguments.get("action") or "toggle").strip().lower()
        if not entity_id:
            return {"ok": False, "message": "entity_id required"}
        domain = entity_id.split(".")[0]
        service = "turn_on" if action == "on" else "turn_off" if action == "off" else "toggle"
        call_service(domain, service, {"entity_id": entity_id})
        return {"ok": True, "entity_id": entity_id, "action": service}

    if name == "jarvis_ha_scene":
        from jarvis.home_assistant import activate_scene, ha_enabled

        if not ha_enabled():
            return {"ok": False, "message": "Home Assistant not configured"}
        scene = (arguments.get("scene") or arguments.get("entity_id") or "").strip()
        if not scene:
            return {"ok": False, "message": "scene required"}
        ok, _msg = activate_scene(scene)
        return {"ok": ok, "scene": scene}

    from jarvis.handlers import ensure_handlers_loaded

    ensure_handlers_loaded()
    assistant = _shared_assistant()

    # Domain tools that need the live assistant: in-process if co-located, else HTTP.
    if assistant is not None:
        from jarvis.handlers.registry import call_action

        if name == "jarvis_briefing":
            return call_action(assistant, "morning_briefing", {}, "morning briefing")

        if name == "jarvis_journal_log":
            text = (arguments.get("text") or "").strip()
            if not text:
                return {"ok": False, "message": "text required"}
            return call_action(assistant, "journal_log", {"text": text}, text)

        if name == "jarvis_document_search":
            query = (arguments.get("query") or "").strip()
            if not query:
                return {"ok": False, "message": "query required"}
            return call_action(assistant, "document_search", {"query": query}, query)

        if name == "jarvis_generate_image":
            from jarvis.image_generation.engine import submit_generation

            prompt = (arguments.get("prompt") or "").strip()
            if not prompt:
                return {"ok": False, "message": "prompt required"}
            return submit_generation(assistant, dict(arguments or {}), message=prompt, source="mcp")

        if name == "jarvis_generate_video":
            from jarvis.video_generation.engine import submit_video

            prompt = (arguments.get("prompt") or "").strip()
            if not prompt:
                return {"ok": False, "message": "prompt required"}
            return submit_video(assistant, dict(arguments or {}), message=prompt, source="mcp")

        if name == "jarvis_chat":
            message = (arguments.get("message") or "").strip()
            if not message:
                return {"ok": False, "message": "message required"}
            return assistant.process(message)

        return {"ok": False, "message": f"Unknown jarvis tool: {name}"}

    log.info("MCP domain tool %s proxied to Aria serve (no shared assistant)", name)

    if name == "jarvis_briefing":
        return _http_json("GET", "/api/briefing")

    if name == "jarvis_journal_log":
        text = (arguments.get("text") or "").strip()
        if not text:
            return {"ok": False, "message": "text required"}
        return _http_json("POST", "/api/journal/daily", form={"content": text, "bullet_type": "note"})

    if name == "jarvis_document_search":
        query = (arguments.get("query") or "").strip()
        if not query:
            return {"ok": False, "message": "query required"}
        return _http_json("GET", "/api/documents/search", query={"q": query})

    if name == "jarvis_generate_image":
        prompt = (arguments.get("prompt") or "").strip()
        if not prompt:
            return {"ok": False, "message": "prompt required"}
        return _http_json("POST", "/api/gallery/generate", json_body={"prompt": prompt})

    if name == "jarvis_generate_video":
        prompt = (arguments.get("prompt") or "").strip()
        if not prompt:
            return {"ok": False, "message": "prompt required"}
        return _http_json(
            "POST",
            "/api/video-generation/generate",
            json_body={"prompt": prompt},
        )

    if name == "jarvis_chat":
        message = (arguments.get("message") or "").strip()
        if not message:
            return {"ok": False, "message": "message required"}
        return _http_json("POST", "/api/chat", form={"message": message}, timeout=300.0)

    return {"ok": False, "message": f"Unknown jarvis tool: {name}"}
