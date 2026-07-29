"""Product bridges — extend other products; never own them."""

from __future__ import annotations

from typing import Any


def voice_bridge() -> dict[str, Any]:
    from jarvis.capabilities_product.contributions import list_voice_intents

    return {
        "ok": True,
        "product": "Voice",
        "role": "extends",
        "intents": list_voice_intents(),
        "note": "Capabilities may contribute voice intents; Voice remains the product owner.",
    }


def vision_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "Vision",
        "role": "extends",
        "hooks": [],
        "note": "No Vision ownership. Future vision post-processors register as contributions only.",
    }


def automation_bridge() -> dict[str, Any]:
    from jarvis.capabilities_product.contributions import list_automation_actions

    return {
        "ok": True,
        "product": "Automation",
        "role": "extends",
        "actions": list_automation_actions(),
        "note": "Capabilities may contribute automation actions; Automation owns the engine.",
    }


def planner_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "Planner",
        "role": "extends",
        "note": "Capabilities does not own Planner tasks. Contribution slots reserved for providers.",
    }


def calendar_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "Calendar",
        "role": "extends",
        "note": "Capabilities does not own Calendar events.",
    }


def memory_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "Memory",
        "role": "extends",
        "permissions": ["memory.read", "memory.write"],
        "note": "SDK helpers gate memory access via PluginContext.require.",
    }


def coding_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "product": "Coding",
        "role": "extends",
        "note": "Host git/engineering extensions appear in Capabilities registry; Coding owns workflows.",
    }
