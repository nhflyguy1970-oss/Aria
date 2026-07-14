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
    "runtime_status": lambda _params, _message: _runtime_action("runtime_status"),
    "runtime_report": lambda _params, _message: _runtime_action("runtime_report"),
    "runtime_health": lambda _params, _message: _runtime_action("runtime_health"),
    "runtime_providers": lambda _params, _message: _runtime_action("runtime_providers"),
    "runtime_services": lambda _params, _message: _runtime_action("runtime_services"),
    "runtime_databases": lambda _params, _message: _runtime_action("runtime_databases"),
    "runtime_mode": lambda _params, _message: _runtime_action("runtime_mode"),
    "runtime_models": lambda _params, _message: _runtime_action("runtime_models"),
    "runtime_jobs": lambda _params, _message: _runtime_action("runtime_jobs"),
    "runtime_gpu": lambda _params, _message: _runtime_action("runtime_gpu"),
    "runtime_ram": lambda _params, _message: _runtime_action("runtime_ram"),
    "runtime_storage": lambda _params, _message: _runtime_action("runtime_storage"),
    "runtime_network": lambda _params, _message: _runtime_action("runtime_network"),
    "runtime_platform": lambda _params, _message: _runtime_action("runtime_platform"),
    "runtime_applications": lambda _params, _message: _runtime_action("runtime_applications"),
    "runtime_attention": lambda _params, _message: _runtime_action("runtime_attention"),
    "status_summary": lambda _params, _message: _status_summary(),
    "cognitive_compose": lambda params, message: _cognitive_compose(params, message),
    "routing_last": lambda _params, _message: _routing_last(),
    "routing_history": lambda _params, _message: _routing_history(),
    "routing_stats": lambda _params, _message: _routing_stats(),
    "timeline_recent": lambda _params, _message: _timeline("timeline_recent"),
    "timeline_today": lambda _params, _message: _timeline("timeline_today"),
    "timeline_startup": lambda _params, _message: _timeline("timeline_startup"),
    "timeline_failures": lambda _params, _message: _timeline("timeline_failures"),
    "timeline_services": lambda _params, _message: _timeline("timeline_services"),
    "timeline_models": lambda _params, _message: _timeline("timeline_models"),
    "timeline_repairs": lambda _params, _message: _timeline("timeline_repairs"),
    "timeline_backups": lambda _params, _message: _timeline("timeline_backups"),
    "reference_search": lambda params, message: _reference_search(params, message),
    "documentation_search": lambda params, message: _reference_search(params, message),
    "nlu_clarify": lambda params, message: _nlu_clarify(params, message),
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


def _runtime_action(action: str) -> dict:
    from jarvis.runtime_introspection import runtime_action_result

    return runtime_action_result(action)


def _cognitive_compose(params: dict, message: str) -> dict:
    """Multi-capability plan → execute → compose (Problem Report ce2a6e07).

    Observability attachments (maturity pass): composed_plan, provenance,
    section_confidence — execution metadata for Conversation Trace / MC only.
    """
    text = (params.get("text") or message or "").strip()
    if not text:
        return {"ok": False, "error": "empty_prompt"}
    try:
        from aria_core.cognitive_orchestrator import orchestrate_compose
        from aria_core.observability import capability_plan_view

        result = orchestrate_compose(text)
        plan = (result.get("data") or {}).get("plan") or {}
        duration_ms = (result.get("data") or {}).get("duration_ms")
        if isinstance(params, dict):
            params["composed_plan"] = plan
            params["plan"] = plan
            params["capabilities"] = list(plan.get("selected") or plan.get("executed") or [])
            params["capability_plan"] = capability_plan_view(plan, action="cognitive_compose")
            params["provenance"] = plan.get("provenance") or []
            params["section_confidence"] = plan.get("section_confidence") or {}
            params["composition_stage"] = "final_response"
            params["compose_duration_ms"] = duration_ms
            for part in (result.get("data") or {}).get("parts") or []:
                if part.get("capability") == "reference":
                    ref_diag = (part.get("data") or {}).get("diagnostics")
                    if ref_diag:
                        params["reference_diagnostics"] = ref_diag
                        params["reference_data"] = part.get("data") or {}
                    break
        return {
            "ok": bool(result.get("ok")),
            "message": result.get("message") or "",
            "reply": result.get("message") or "",
            "composed": True,
            "plan": {
                "capabilities": list(plan.get("selected") or []),
                "executed": list(plan.get("executed") or []),
                "skipped": list(plan.get("skipped") or []),
                "failed": list(plan.get("failed") or []),
                "skip_reasons": plan.get("skip_reasons") or {},
                "plan_view": plan.get("plan_view") or {},
                "provenance": plan.get("provenance") or [],
                "section_confidence": plan.get("section_confidence") or {},
                "latency_ms": duration_ms,
                "execution_plan_display": plan.get("execution_plan_display"),
            },
            "intent": "cognitive_compose",
            "data": result.get("data") or {},
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:240], "intent": "cognitive_compose"}


def _status_summary() -> dict:
    from jarvis.mission_control import collect_mission_control, format_overview_markdown

    data = collect_mission_control(record_metrics=False)
    return {
        "ok": True,
        "message": format_overview_markdown(),
        "data": data.get("overview"),
        "type": "info",
    }


def _routing_last() -> dict:
    from jarvis.routing_inspector import format_routing_record_markdown, last_routing_record

    record = last_routing_record()
    return {
        "ok": True,
        "message": format_routing_record_markdown(record),
        "data": record,
        "type": "info",
    }


def _routing_history() -> dict:
    from jarvis.routing_inspector import routing_history

    items = routing_history(limit=10)
    lines = ["## Routing history (last 10)", ""]
    for item in items:
        lines.append(
            f"- `{item.get('iso')}` **{item.get('intent')}** → {item.get('route')} "
            f"({item.get('latency_ms')} ms)"
        )
    return {"ok": True, "message": "\n".join(lines), "data": items, "type": "info"}


def _routing_stats() -> dict:
    from jarvis.routing_inspector import format_routing_stats_markdown, routing_stats_summary

    stats = routing_stats_summary()
    return {
        "ok": True,
        "message": format_routing_stats_markdown(stats),
        "data": stats,
        "type": "info",
    }


def _timeline(action: str) -> dict:
    from jarvis.timeline_commands import execute_timeline_command

    return execute_timeline_command(action)


def _reference_search(params: dict, message: str) -> dict:
    from jarvis.reference_engine import search_reference

    query = (params.get("query") or message or "").strip()
    subject = (params.get("subject") or "").strip()
    return search_reference(query, subject=subject)


def _nlu_clarify(params: dict, message: str) -> dict:
    choices = params.get("choices") or []
    question = params.get("clarification_question") or "What did you mean?"
    lines = [question, ""]
    for idx, label in enumerate(choices, 1):
        lines.append(f"{idx}. {label}")
    return {"ok": True, "message": "\n".join(lines), "type": "clarify"}


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
