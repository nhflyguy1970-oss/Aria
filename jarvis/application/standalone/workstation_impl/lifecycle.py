"""Workstation lifecycle — up, down, status, restart."""

from __future__ import annotations

import logging
from typing import Any

from jarvis.application.standalone.workstation_impl.registry import (
    all_components,
    component,
    get_registry,
    registry_snapshot,
)

logger = logging.getLogger("jarvis.workstation")


def _autostart_ids() -> set[str]:
    import os

    raw = os.getenv("JARVIS_AUTOSTART_SERVICES", "").strip()
    if not raw:
        return set()
    return {part.strip() for part in raw.split(",") if part.strip()}


def status(*, force: bool = False) -> dict[str, Any]:
    """Full workstation status snapshot."""
    return registry_snapshot(force=force)


def up(target: str | None = None, *, profile: str | None = None) -> dict[str, Any]:
    """Start workstation services. Optional target component or docker profile."""
    results: list[dict[str, Any]] = []

    if profile:
        ok = _start_profile(profile)
        results.append({"id": f"profile:{profile}", "ok": ok, "action": "start"})
        return {"ok": ok, "results": results, "status": status(force=True)}

    if target:
        return _component_action(target, "start")

    # Bootstrap core workstation
    ws = component("workstation")
    if ws and ws.start:
        ok = bool(ws.start())
        results.append({"id": "workstation", "ok": ok, "action": "start"})

    for comp in all_components():
        if comp.id in ("workstation", "aria"):
            continue
        should_start = comp.autostart or comp.id in _autostart_ids()
        if not should_start:
            continue
        if comp.healthy():
            results.append(
                {"id": comp.id, "ok": True, "action": "skip", "detail": "already running"}
            )
            continue
        if comp.start:
            ok = bool(comp.start())
            results.append({"id": comp.id, "ok": ok, "action": "start"})

    snap = status(force=True)
    return {
        "ok": snap.get("ready", False),
        "results": results,
        "status": snap,
    }


def down(target: str | None = None, *, profile: str | None = None) -> dict[str, Any]:
    """Stop managed services. Never stops Ollama system-wide by default."""
    if profile:
        ok = _stop_profile(profile)
        return {
            "ok": ok,
            "results": [{"id": f"profile:{profile}", "ok": ok, "action": "stop"}],
            "status": status(force=True),
        }

    if target:
        return _component_action(target, "stop")

    results: list[dict[str, Any]] = []
    for comp in all_components():
        if not comp.managed or comp.required or comp.id == "workstation":
            continue
        if not comp.healthy():
            continue
        if comp.stop:
            ok = bool(comp.stop())
            results.append({"id": comp.id, "ok": ok, "action": "stop"})

    snap = status(force=True)
    return {"ok": True, "results": results, "status": snap}


def restart(target: str) -> dict[str, Any]:
    """Restart a single managed component."""
    return _component_action(target, "restart")


def _component_action(component_id: str, action: str) -> dict[str, Any]:
    comp = component(component_id)
    if comp is None:
        known = sorted(get_registry().keys())
        return {
            "ok": False,
            "error": f"Unknown component: {component_id}",
            "known": known[:20],
        }
    fn = getattr(comp, action, None)
    if fn is None:
        return {
            "ok": False,
            "error": f"Component '{component_id}' does not support {action}",
            "managed": comp.managed,
        }
    ok = bool(fn())
    return {
        "ok": ok,
        "results": [{"id": component_id, "ok": ok, "action": action}],
        "status": status(force=True),
    }


def _start_profile(profile: str) -> bool:
    try:
        import logging as _logging

        from aiplatform.runtime.docker import DockerRuntime

        DockerRuntime(_logging.getLogger("jarvis.workstation")).start_profile(profile)
        return True
    except Exception as exc:
        logger.warning("Profile start %s failed: %s", profile, exc)
        return False


def _stop_profile(profile: str) -> bool:
    try:
        import logging as _logging

        from aiplatform.runtime.docker import DockerRuntime

        DockerRuntime(_logging.getLogger("jarvis.workstation")).stop_profile(profile)
        return True
    except Exception as exc:
        logger.warning("Profile stop %s failed: %s", profile, exc)
        return False
