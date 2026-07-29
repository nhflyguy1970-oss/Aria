"""Contribution registration — chat actions, routes, agent tools."""

from __future__ import annotations

import re
from typing import Any

from jarvis.capabilities_product.history import record_activity
from jarvis.handlers.registry import register_action
from jarvis.router_table import RouteRule

_CONTRIB_ACTIONS: dict[str, list[str]] = {}
_CONTRIB_ROUTE_META: list[tuple[str, RouteRule]] = []  # (cap_id, rule)
_CONTRIB_TOOLS: dict[str, list[dict[str, Any]]] = {}
_CONTRIB_VOICE: dict[str, list[dict[str, Any]]] = {}
_CONTRIB_WORKFLOW: dict[str, list[dict[str, Any]]] = {}
_CONTRIB_AUTOMATION: dict[str, list[dict[str, Any]]] = {}


def contribution_routes() -> list[RouteRule]:
    return [rule for _, rule in _CONTRIB_ROUTE_META]


def list_agent_tools() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cap_id, tools in _CONTRIB_TOOLS.items():
        for t in tools:
            out.append({**t, "capability_id": cap_id})
    return out


def list_voice_intents() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cap_id, items in _CONTRIB_VOICE.items():
        for t in items:
            out.append({**t, "capability_id": cap_id})
    return out


def list_workflow_steps() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cap_id, items in _CONTRIB_WORKFLOW.items():
        for t in items:
            out.append({**t, "capability_id": cap_id})
    return out


def list_automation_actions() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cap_id, items in _CONTRIB_AUTOMATION.items():
        for t in items:
            out.append({**t, "capability_id": cap_id})
    return out


def unregister_contributions(cap_id: str) -> None:
    global _CONTRIB_ROUTE_META
    names = _CONTRIB_ACTIONS.pop(cap_id, [])
    from jarvis.handlers import registry as reg

    for name in names:
        reg._REGISTRY.pop(name, None)  # noqa: SLF001
    _CONTRIB_ROUTE_META = [(cid, r) for cid, r in _CONTRIB_ROUTE_META if cid != cap_id]
    _CONTRIB_TOOLS.pop(cap_id, None)
    _CONTRIB_VOICE.pop(cap_id, None)
    _CONTRIB_WORKFLOW.pop(cap_id, None)
    _CONTRIB_AUTOMATION.pop(cap_id, None)


def _manifest_bits(manifest: Any) -> tuple[dict[str, Any], str, str]:
    if hasattr(manifest, "contributions"):
        contrib = getattr(manifest, "contributions", None) or {}
        mid = str(getattr(manifest, "id", "") or "")
        mname = str(getattr(manifest, "name", mid) or mid)
        return (contrib if isinstance(contrib, dict) else {}), mid, mname
    if isinstance(manifest, dict):
        contrib = manifest.get("contributions") or {}
        mid = str(manifest.get("id") or "")
        mname = str(manifest.get("name") or mid)
        return (contrib if isinstance(contrib, dict) else {}), mid, mname
    return {}, "", ""


def register_contributions(cap_id: str, manifest: Any) -> dict[str, Any]:
    """Register chat/tool/voice/workflow/automation contributions from a manifest."""
    unregister_contributions(cap_id)
    contrib, mid, mname = _manifest_bits(manifest)
    mid = mid or cap_id.split(":", 1)[-1]
    mname = mname or mid

    registered = {"actions": 0, "routes": 0, "tools": 0, "voice": 0, "workflow": 0, "automation": 0}
    action_names: list[str] = []

    for spec in contrib.get("actions") or []:
        if not isinstance(spec, dict):
            continue
        action = str(spec.get("name") or "").strip()
        if not action:
            continue
        description = str(spec.get("description") or action)
        reply = str(spec.get("reply") or f"{mname} capability responded.")

        def _make_handler(text: str, cid: str):
            def _handler(assistant, params, message):  # noqa: ARG001
                return {"ok": True, "message": text, "module": "general", "capability_id": cid}

            return _handler

        register_action(
            action,
            info=bool(spec.get("info", True)),
            module=str(spec.get("module") or "general"),
            description=description,
            extension=str(mid),
        )(_make_handler(reply, cap_id))
        action_names.append(action)
        registered["actions"] += 1

        for pat in spec.get("patterns") or spec.get("phrases") or []:
            pat_s = str(pat).strip()
            if not pat_s:
                continue

            def _make_match(p: str):
                rx = re.compile(p, re.I) if p.startswith("^") else None
                needle = p.lower()

                def _match(m: str, lower: str, _s) -> bool:  # noqa: ARG001
                    if rx:
                        return bool(rx.search(m))
                    return needle in lower

                return _match

            rule = RouteRule(
                action,
                int(spec.get("priority") or 40),
                f"capability:{mid}",
                _make_match(pat_s),
            )
            _CONTRIB_ROUTE_META.append((cap_id, rule))
            registered["routes"] += 1

    _CONTRIB_ACTIONS[cap_id] = action_names

    tools = [t for t in (contrib.get("tools") or []) if isinstance(t, dict)]
    _CONTRIB_TOOLS[cap_id] = tools
    registered["tools"] = len(tools)

    voice = [t for t in (contrib.get("voice_intents") or []) if isinstance(t, dict)]
    _CONTRIB_VOICE[cap_id] = voice
    registered["voice"] = len(voice)

    workflow = [t for t in (contrib.get("workflow_steps") or []) if isinstance(t, dict)]
    _CONTRIB_WORKFLOW[cap_id] = workflow
    registered["workflow"] = len(workflow)

    automation = [t for t in (contrib.get("automation_actions") or []) if isinstance(t, dict)]
    _CONTRIB_AUTOMATION[cap_id] = automation
    registered["automation"] = len(automation)

    record_activity(
        "contributions",
        capability_id=cap_id,
        message=f"Registered contributions for {cap_id}",
        detail=registered,
    )
    return {"ok": True, "capability_id": cap_id, "registered": registered}
