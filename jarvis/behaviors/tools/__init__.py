"""Tools behavior — managed coding tool executors."""

from __future__ import annotations

from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action
from jarvis.tools.executor import execute_tool, format_tool_status, select_tool, tool_status

_TOOL_ACTIONS = {
    "tool_list": lambda _p, _m: {"ok": True, "message": format_tool_status(), "data": tool_status()},
    "tool_status": lambda _p, _m: {"ok": True, "message": format_tool_status(), "data": tool_status()},
    "tool_execute": lambda p, _m: _execute(p),
    "tool_select": lambda p, m: _select(p, m),
    "tool_runs": lambda p, _m: _runs(p),
    "tool_run_status": lambda p, _m: _run_status(p),
}


def _execute(params: dict) -> dict:
    tool_id = (params.get("tool") or params.get("tool_id") or "").strip()
    if not tool_id:
        return {"ok": False, "message": "tool parameter required"}
    result = execute_tool(tool_id, params)
    msg = result.get("stdout") or result.get("message") or result.get("error") or "done"
    return {"ok": result.get("ok", False), "message": str(msg)[:4000], "data": result}


def _select(params: dict, message: str) -> dict:
    task = (params.get("task") or message or "").strip()
    tool = select_tool(task, prefer=(params.get("prefer") or params.get("tool") or ""))
    if not tool:
        return {"ok": False, "message": "No coding tools available on this workstation."}
    return {
        "ok": True,
        "message": f"Selected **{tool.label}** for this task.",
        "data": tool.to_dict(),
    }


def _runs(params: dict) -> dict:
    from jarvis.tools.runner import list_runs

    tool_id = (params.get("tool") or params.get("tool_id") or "").strip()
    runs = [r.to_dict() for r in list_runs(tool_id=tool_id)]
    return {"ok": True, "runs": runs, "message": f"{len(runs)} recent tool run(s)"}


def _run_status(params: dict) -> dict:
    from jarvis.tools.runner import run_status

    run_id = (params.get("run_id") or params.get("id") or "").strip()
    if not run_id:
        return {"ok": False, "message": "run_id required"}
    result = run_status(run_id)
    if not result.get("ok"):
        return {"ok": False, "message": result.get("error", "not found")}
    run = result.get("run") or {}
    return {"ok": True, "message": f"Run `{run_id}` — {run.get('status')}", "data": result}


@register_behavior
class ToolsBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="tools",
            name="Tools",
            category="Tools",
            description="Managed coding tool executors — launch, run, capture, remember",
            module_path="jarvis.behaviors.tools",
            test_module="tests.test_tools",
            action_names=list(_TOOL_ACTIONS.keys()),
            dependencies=["capability_registry"],
            stability="stable",
            owner="application",
            version="1.0.0",
        )

    def attach(self) -> list[str]:
        for action, handler in _TOOL_ACTIONS.items():
            register_action(
                action,
                info=True,
                module="tools",
                description=action.replace("_", " "),
            )(self._bind(handler))
        return []

    def execute(self, orchestrator: Any, action: str, params: dict, message: str) -> dict | None:
        handler = _TOOL_ACTIONS.get(action)
        if handler is None:
            return None
        return handler(params, message)

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            return handler(params, message)

        return _entry
