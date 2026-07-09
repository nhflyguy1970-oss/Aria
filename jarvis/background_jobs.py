"""Long-running chat actions queued on the coding job worker (LLM / CPU)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant

BACKGROUND_ACTIONS = frozenset({
    "document_summarize",
    "learn_about",
    "knowledge_research_run",
    "self_upgrade_run",
    "aria_self_fix",
})

ACTION_LABELS = {
    "document_summarize": "Document summarize",
    "learn_about": "Learn topic",
    "knowledge_research_run": "Nightly knowledge research",
    "self_upgrade_run": "Self-upgrade pipeline",
    "aria_self_fix": "ARIA self-fix",
}

ACTION_MODULES = {
    "document_summarize": "document",
    "learn_about": "general",
    "knowledge_research_run": "general",
    "self_upgrade_run": "coding",
    "aria_self_fix": "coding",
}

_HANDLER_METHODS: dict[str, str] = {
    "document_summarize": "_document_summarize",
    "learn_about": "_learn_about",
}


def submit_action(assistant: "JarvisAssistant", action: str, params: dict, message: str) -> str:
    from jarvis.modules.workflow_orchestration_adapter import workflow_enqueue

    return workflow_enqueue(
        "background",
        action,
        _submit_action_impl,
        assistant,
        action,
        params,
        message,
    )


def _submit_action_impl(
    assistant: "JarvisAssistant", action: str, params: dict, message: str
) -> str:
    from jarvis.coding_jobs import submit
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action, get_spec

    ensure_handlers_loaded()
    label = ACTION_LABELS.get(action, action.replace("_", " ").title())
    job_id_ref: dict[str, str] = {"id": ""}

    def _run() -> dict:
        from jarvis.coding_jobs import _is_cancelled

        run_params = dict(params)
        run_params["_cancel_check"] = lambda: _is_cancelled(job_id_ref["id"])
        spec = get_spec(action)
        if spec and spec.handler:
            return call_action(assistant, action, run_params, message)

        method_name = _HANDLER_METHODS.get(action)
        if not method_name:
            raise ValueError(f"Unknown background action: {action}")
        handler: Callable[[dict, str], dict] = getattr(assistant, method_name)
        return handler(run_params, message)

    job_id = submit(label, _run)
    job_id_ref["id"] = job_id
    return job_id
