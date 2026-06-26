"""Long-running chat actions queued on the coding job worker (LLM / CPU)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant

BACKGROUND_ACTIONS = frozenset({
    "document_summarize",
    "learn_about",
})

ACTION_LABELS = {
    "document_summarize": "Document summarize",
    "learn_about": "Learn topic",
}

ACTION_MODULES = {
    "document_summarize": "document",
    "learn_about": "general",
}

_HANDLER_METHODS: dict[str, str] = {
    "document_summarize": "_document_summarize",
    "learn_about": "_learn_about",
}


def submit_action(assistant: JarvisAssistant, action: str, params: dict, message: str) -> str:
    from jarvis.coding_jobs import submit

    method_name = _HANDLER_METHODS.get(action)
    if not method_name:
        raise ValueError(f"Unknown background action: {action}")
    handler: Callable[[dict, str], dict] = getattr(assistant, method_name)
    label = ACTION_LABELS.get(action, action)

    def _run() -> dict:
        return handler(params, message)

    return submit(label, _run)
