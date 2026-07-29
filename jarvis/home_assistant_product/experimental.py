"""Experimental Smart Home features — env-gated, same Smart Home engine."""

from __future__ import annotations

import os
from typing import Any


def experimental_flags() -> dict[str, bool]:
    return {
        "websocket": os.getenv("JARVIS_SMARTHOME_EXP_WS", "0") == "1"
        or os.getenv("JARVIS_HA_EXP_WEBSOCKET", "0") == "1",
        "multi_ha": os.getenv("JARVIS_SMARTHOME_EXP_MULTI_HA", "0") == "1",
        "knowledge_graph": os.getenv("JARVIS_SMARTHOME_EXP_KG", "0") == "1",
        "automation_authoring": os.getenv("JARVIS_SMARTHOME_EXP_AUTOMATION", "0") == "1",
        "bench_lighting": os.getenv("JARVIS_SMARTHOME_EXP_BENCH_LIGHT", "0") == "1"
        or os.getenv("JARVIS_FLYTYING_EXP_HA_LIGHT", "0") == "1",
        "live_updates": os.getenv("JARVIS_SMARTHOME_EXP_LIVE", "0") == "1",
        "vision_camera": os.getenv("JARVIS_SMARTHOME_EXP_VISION_CAM", "0") == "1"
        or os.getenv("JARVIS_VISION_EXP_HA_CAMERA", "0") == "1",
    }


def experimental_status() -> dict[str, Any]:
    flags = experimental_flags()
    return {
        "ok": True,
        "experimental": True,
        "message": (
            "Experimental Smart Home features are opt-in and share the same "
            "Smart Home engine wrapping jarvis.home_assistant."
        ),
        "flags": flags,
        "enabled": [k for k, v in flags.items() if v],
        "consent_required": True,
    }


def websocket_status() -> dict[str, Any]:
    if not experimental_flags().get("websocket"):
        return {"ok": False, "error": "websocket disabled", "experimental": True}
    return {
        "ok": True,
        "experimental": "websocket",
        "connected": False,
        "message": "HA WebSocket live updates are staged — REST remains the production path.",
        "requires_confirmation": True,
    }


def multi_ha_status() -> dict[str, Any]:
    if not experimental_flags().get("multi_ha"):
        return {"ok": False, "error": "multi_ha disabled", "experimental": True}
    return {
        "ok": True,
        "experimental": "multi_ha",
        "instances": [],
        "message": "Multi-HA is experimental — single JARVIS_HA_URL remains the default engine target.",
        "requires_confirmation": True,
    }


def link_knowledge_graph(*, entity_id: str = "", room: str = "", summary: str = "") -> dict[str, Any]:
    if not experimental_flags().get("knowledge_graph"):
        return {"ok": False, "error": "knowledge_graph disabled", "experimental": True}
    return {
        "ok": True,
        "experimental": "knowledge_graph",
        "requires_confirmation": True,
        "staged": {
            "entity_id": entity_id,
            "room": room,
            "summary": (summary or "")[:2000],
        },
        "message": "Knowledge graph link staged — confirm in Connections / Memory (never auto-written).",
    }


def automation_authoring_draft(*, scene: str = "", entity_id: str = "") -> dict[str, Any]:
    if not experimental_flags().get("automation_authoring"):
        return {"ok": False, "error": "automation_authoring disabled", "experimental": True}
    from jarvis.home_assistant_product.automation_bridge import automation_candidates

    return {
        **automation_candidates(kind="draft_ha_yaml", scene=scene, entity_id=entity_id),
        "experimental": "automation_authoring",
    }


def bench_lighting_if_enabled(scene: str = "bench", *, entity_id: str = "") -> dict[str, Any]:
    if not experimental_flags().get("bench_lighting"):
        return {"ok": False, "error": "bench_lighting disabled", "experimental": True}
    return {
        "ok": False,
        "error": "HA bench lighting requires explicit operator confirmation",
        "experimental": True,
        "scene": scene,
        "entity_id": entity_id,
        "requires_confirmation": True,
        "note": "Home Assistant owns scenes — Smart Home / Fly Tying only request.",
    }
