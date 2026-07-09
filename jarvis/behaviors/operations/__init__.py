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
    "inference_status": lambda _params, _message: {
        "ok": True,
        "message": _inference_status_message(),
        "data": _inference_status(),
    },
    "maintenance_run": lambda _params, _message: _maintenance_run(),
    "context_preview": lambda params, message: _context_preview(params, message),
    "platform_cutover_status": lambda _params, _message: _platform_cutover_status(),
    "platform_cutover_enable": lambda _params, _message: _platform_cutover_enable(),
    "platform_cutover_rollback": lambda _params, _message: _platform_cutover_rollback(),
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


def _inference_status() -> dict:
    from jarvis.inference.gateway import gateway_status

    return gateway_status()


def _inference_status_message() -> str:
    status = _inference_status()
    mode = status.get("gateway_mode", "auto")
    litellm = "up" if status.get("litellm_available") else "down"
    cloud = "enabled" if status.get("cloud_enabled") else "disabled"
    vram = "low" if status.get("low_vram") else "ok"
    return f"Inference: mode={mode}, LiteLLM={litellm}, cloud={cloud}, VRAM={vram}"


def _maintenance_run() -> dict:
    from jarvis.automation.ops import run_maintenance

    result = run_maintenance(smoke_tests=False)
    return {
        "ok": result.get("ok", False),
        "message": f"Maintenance complete ({result.get('elapsed_ms', 0)}ms)",
        "data": result,
    }


def _context_preview(params: dict, message: str) -> dict:
    from jarvis.assistant_instance import get_assistant
    from jarvis.context.builder import build_unified_context

    query = (params.get("query") or message or "status").strip()
    result = build_unified_context(get_assistant(), query)
    ctx = (result.get("context") or "")[:6000]
    return {
        "ok": result.get("ok", False),
        "message": ctx or "_No context assembled._",
        "data": {k: v for k, v in result.items() if k != "context"},
    }


def _platform_cutover_status() -> dict:
    from jarvis.platform_cutover import format_status_markdown, status

    return {"ok": True, "message": format_status_markdown(), "data": status()}


def _platform_cutover_enable() -> dict:
    from jarvis.platform_cutover import enable_platform_authoritative

    result = enable_platform_authoritative()
    return {
        "ok": result.get("ok", False),
        "message": result.get("message") or result.get("error") or "cutover",
        "data": result,
    }


def _platform_cutover_rollback() -> dict:
    from jarvis.platform_cutover import rollback_to_legacy

    result = rollback_to_legacy()
    return {"ok": True, "message": result.get("message", "rolled back"), "data": result}


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
