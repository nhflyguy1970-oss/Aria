"""Operations behavior — workstation registry, lifecycle, and recovery."""

from __future__ import annotations

from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action
from jarvis.workstation import lifecycle, operations

_OPERATIONS_ACTIONS: dict[str, Any] = {
    "workstation_status": lambda _params, _message: {
        "ok": True,
        "message": operations.format_report(force=True),
        "data": lifecycle.status(force=True),
    },
    "workstation_diagnose": lambda _params, _message: {
        "ok": True,
        "message": operations.format_report(force=True),
        "data": operations.diagnose(force=True),
    },
    "workstation_recover": lambda _params, _message: _recover(),
    "workstation_up": lambda params, _message: _lifecycle("up", params),
    "workstation_down": lambda params, _message: _lifecycle("down", params),
    "workstation_restart": lambda params, _message: _restart(params),
}


def _recover() -> dict:
    result = operations.recover_safe()
    return {
        "ok": result.get("ok", False),
        "message": operations.format_report(force=True),
        "data": result,
    }


def _lifecycle(action: str, params: dict) -> dict:
    target = (params.get("component") or params.get("target") or "").strip() or None
    profile = (params.get("profile") or "").strip() or None
    if action == "up":
        result = lifecycle.up(target, profile=profile)
    else:
        result = lifecycle.down(target, profile=profile)
    return {
        "ok": result.get("ok", False),
        "message": operations.format_report(force=True),
        "data": result,
    }


def _restart(params: dict) -> dict:
    target = (params.get("component") or params.get("target") or "").strip()
    if not target:
        return {"ok": False, "message": "component parameter required for restart"}
    result = lifecycle.restart(target)
    return {
        "ok": result.get("ok", False),
        "message": operations.format_report(force=True),
        "data": result,
    }


@register_behavior
class OperationsBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="operations",
            name="Operations",
            category="Operations",
            description="Workstation registry, lifecycle, diagnostics, and safe recovery",
            module_path="jarvis.behaviors.operations",
            test_module="tests.test_workstation",
            action_names=list(_OPERATIONS_ACTIONS.keys()),
            dependencies=["capability_registry"],
            stability="stable",
            owner="application",
            version="1.0.0",
        )

    def attach(self) -> list[str]:
        for action, handler in _OPERATIONS_ACTIONS.items():
            register_action(
                action,
                info=True,
                module="operations",
                description=action.replace("_", " "),
            )(self._bind(handler))
        return []

    def execute(
        self,
        orchestrator: Any,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        handler = _OPERATIONS_ACTIONS.get(action)
        if handler is None:
            return None
        return handler(params, message)

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            return handler(params, message)

        return _entry

    def health(self) -> dict[str, Any]:
        report = operations.diagnose(force=False)
        return {
            "status": "healthy" if report.get("ok") else "degraded",
            "behavior_id": self.behavior_id,
            "critical": report.get("critical", 0),
            "warnings": report.get("warnings", 0),
        }
