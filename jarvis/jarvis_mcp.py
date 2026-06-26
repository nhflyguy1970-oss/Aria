"""Non-coding MCP tools — briefing, environment, HA, journal, documents, image queue."""

from __future__ import annotations

from typing import Any


def handle_jarvis_mcp_tool(name: str, arguments: dict) -> dict[str, Any]:
    from jarvis.assistant_instance import get_assistant

    a = get_assistant()

    if name == "jarvis_briefing":
        return a._morning_briefing({}, "morning briefing")

    if name == "jarvis_environment":
        from jarvis.environment import snapshot

        return {"ok": True, **snapshot(include_resources=True)}

    if name == "jarvis_journal_log":
        text = (arguments.get("text") or "").strip()
        if not text:
            return {"ok": False, "message": "text required"}
        return a._journal_log({"text": text}, text)

    if name == "jarvis_document_search":
        query = (arguments.get("query") or "").strip()
        if not query:
            return {"ok": False, "message": "query required"}
        return a._document_search({"query": query}, query)

    if name == "jarvis_ha_toggle":
        from jarvis.home_assistant import call_service, ha_enabled

        if not ha_enabled():
            return {"ok": False, "message": "Home Assistant not configured"}
        eid = (arguments.get("entity_id") or "").strip()
        action = (arguments.get("action") or "toggle").strip().lower()
        if not eid:
            return {"ok": False, "message": "entity_id required"}
        domain = eid.split(".")[0]
        svc = "turn_on" if action == "on" else "turn_off" if action == "off" else "toggle"
        call_service(domain, svc, {"entity_id": eid})
        return {"ok": True, "entity_id": eid, "action": svc}

    if name == "jarvis_ha_scene":
        from jarvis.home_assistant import activate_scene, ha_enabled

        if not ha_enabled():
            return {"ok": False, "message": "Home Assistant not configured"}
        scene = (arguments.get("scene") or arguments.get("entity_id") or "").strip()
        if not scene:
            return {"ok": False, "message": "scene required"}
        ok = activate_scene(scene)
        return {"ok": ok, "scene": scene}

    if name == "jarvis_generate_image":
        prompt = (arguments.get("prompt") or "").strip()
        if not prompt:
            return {"ok": False, "message": "prompt required"}
        return a._enqueue_media(
            "generate_image",
            {"prompt": prompt},
            prompt,
        )

    if name == "jarvis_chat":
        message = (arguments.get("message") or "").strip()
        if not message:
            return {"ok": False, "message": "message required"}
        return a.process(message)

    return {"ok": False, "message": f"Unknown jarvis tool: {name}"}
