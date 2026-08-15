"""Single conversation turn helpers — shared by sync and stream paths.

Batch B: delete duplicate normalize / decorate / queue-dispatch logic.
User-visible behavior must remain unchanged.
"""

from __future__ import annotations

import re
from typing import Any, Callable


def normalize_action_params(intent: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Normalize intent action/params (was duplicated in sync + stream)."""
    action = intent.get("action", "chat")
    if isinstance(action, dict):
        action = str(action.get("name") or action.get("action") or "chat")
    elif not isinstance(action, str) or not action.strip():
        action = "chat"
    params = intent.get("params", {})
    if not isinstance(params, dict):
        params = {}
    return action, params


def apply_editor_params_if_coding(assistant: Any, action: str, params: dict, message: str) -> None:
    if action.startswith("coding_") or action in (
        "find_references",
        "extract_function",
        "move_module",
        "rename_symbol",
    ):
        from jarvis.behaviors.engineering.context import EngineeringContext
        from jarvis.behaviors.engineering.engine import EngineeringEngine

        EngineeringEngine.apply_editor_params(
            EngineeringContext.from_orchestrator(assistant), params, message, action
        )


def local_handlers(assistant: Any) -> dict[str, Callable[..., dict]]:
    return {
        "chat": assistant._chat,
        "apply_proposal": assistant._apply_proposal_nl,
        "dismiss_proposal": assistant._dismiss_proposal,
        "undo_apply": assistant._undo_apply,
        "upgrade_wizard": assistant._upgrade_wizard,
        "upgrade_verify": assistant._upgrade_verify,
        "upgrade_apply": assistant._upgrade_apply,
        "upgrade_rollback": assistant._upgrade_rollback,
    }


def dispatch_action(
    assistant: Any,
    action: str,
    params: dict[str, Any],
    message: str,
    *,
    prefer_queue: bool = True,
) -> dict[str, Any]:
    """
    Shared dispatch cascade used by the sync path (and stream for non-SSE actions).

    Order: media queue → background → coding queues → registry → local handlers → chat.
    """
    from jarvis.background_jobs import BACKGROUND_ACTIONS
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action, get_queue, has_action
    from jarvis.media_jobs import QUEUED_ACTIONS

    ensure_handlers_loaded()
    handlers = local_handlers(assistant)
    handler = handlers.get(action, assistant._chat)
    queue = get_queue(action) if prefer_queue else None

    if prefer_queue and (queue == "media" or action in QUEUED_ACTIONS):
        return assistant._enqueue_media(action, params, message)
    if prefer_queue and (queue == "background" or action in BACKGROUND_ACTIONS):
        return assistant._enqueue_background(action, params, message)
    if prefer_queue and (queue == "coding" or action == "coding_agent"):
        return assistant._enqueue_coding(params, message)
    if prefer_queue and (queue == "fix_tests" or action == "coding_fix_tests"):
        return assistant._enqueue_fix_tests(params, message)
    if action in ("coding_propose", "coding_fix", "coding_improve"):
        from jarvis.coding_jobs import submit_coding_propose

        path = assistant._engineering_resolve_path(params.get("path", ""))
        if action == "coding_improve" or action == "coding_propose":
            mode = "improve"
        else:
            mode = "fix"
        # Do NOT diagnose on the request thread — that holds the chat lock and
        # wedged the whole assistant while LSP/sandbox/LLM ran. Diagnosis belongs
        # inside the coding worker (see submit_coding_propose / coding_propose).
        editor_prompt = assistant._engineering_editor_suffix(params)
        task = params.get("task") or message
        job_id = submit_coding_propose(
            assistant,
            path,
            mode,
            task=task,
            editor_prompt=editor_prompt,
        )
        return assistant._engineering_job_result(
            f"**Coding** queued — `{path or 'file'}` ({mode})\n\n"
            "Working in the background — result appears here when ready.",
            job_id,
            action,
        )
    if action == "documents_import_folder":
        from jarvis.document_services import import_folder
        from jarvis.response import err as _err, ok as _ok

        path = (params.get("path") or "").strip()
        # Chat path: copy under lock, reindex in background — sync RAG rebuild wedged chat.
        result = import_folder(path, reindex=False)
        if not result.get("ok"):
            return _err(result.get("message") or "Import failed", module="document")
        return _ok(result.get("message") or "Import complete", module="document", **{
            k: result[k] for k in ("imported", "count", "errors", "capped") if k in result
        })
    if action == "coding_create":
        from jarvis.coding_jobs import submit_coding_create

        job_id = submit_coding_create(assistant, params, message)
        return assistant._engineering_job_result(
            "**Coding** queued — new script\n\n"
            "Working in the background — result appears here when ready.",
            job_id,
            "coding_create",
        )
    if has_action(action):
        # Chat LLM can take a minute — never hold the request lock through it.
        if action == "chat" and hasattr(assistant, "yield_request_lock"):
            assistant.yield_request_lock()
        return call_action(assistant, action, params, message)
    # Fallback local chat handler
    if action == "chat" or handler is assistant._chat:
        if hasattr(assistant, "yield_request_lock"):
            assistant.yield_request_lock()
    return handler(params, message)


def decorate_result(
    assistant: Any,
    result: dict[str, Any],
    *,
    intent: dict[str, Any],
    action: str,
    params: dict[str, Any],
    message: str,
) -> dict[str, Any]:
    """Post-dispatch decoration (was duplicated / inconsistently applied)."""
    from jarvis.action_log import log_action
    from jarvis.config import is_uncensored
    from jarvis.handlers.registry import is_info_action

    result["action"] = action
    result["thinking"] = intent.get("thinking", "")
    result["uncensored"] = is_uncensored()
    if is_info_action(action) or action in ("capabilities", "models_info", "greeting"):
        result["type"] = "info"
    if result.get("module"):
        assistant.session.note_module(result["module"])
    # Preserve active conversational subject for bare follow-ups ("fix it").
    try:
        if message and getattr(assistant.session, "note_subject", None):
            low = message.lower()
            if re.search(
                r"\b(?:scraper|script|pipeline|job|project|bug|error|issue|problem|"
                r"rotor|brake|ranger|truck|vehicle|ubuntu|lts|fly)\b",
                low,
            ):
                assistant.session.note_subject(message.strip()[:200])
            elif action == "web_search" and message.strip():
                assistant.session.note_subject(message.strip()[:200])
    except Exception:
        pass
    # Non-chat research turns must enter the transcript so chat follow-ups
    # cannot invent unrelated entities from older history (RW-001/RW-008).
    try:
        if (
            action == "web_search"
            and result.get("ok")
            and message
            and getattr(assistant, "conversation", None)
        ):
            answer = str(result.get("answer") or result.get("message") or "").strip()
            if answer:
                conv = assistant.conversation
                msgs = list(getattr(conv, "messages", None) or [])
                last_user = next(
                    (m for m in reversed(msgs) if m.get("role") == "user"),
                    None,
                )
                if not last_user or (last_user.get("content") or "") != message:
                    conv.add_user(message)
                conv.add_assistant(answer[:4000])
    except Exception:
        pass
    if result.get("module") in ("coding", "data"):
        assistant.sync_project_namespace()
    if action in (
        "coding_agent",
        "coding_refactor",
        "coding_fix",
        "coding_improve",
        "coding_create",
        "coding_fix_tests",
    ):
        mode = params.get("mode") or action.replace("coding_", "")
        assistant.session.note_coding_mode(mode)
    log_action(action, result.get("module", ""), message[:120], result.get("ok", True))
    if result.get("ok") and action not in (
        "chat",
        "capabilities",
        "greeting",
        "models_info",
    ):
        from jarvis.trust_memory import record_tool_outcome

        record_tool_outcome(assistant.memory, action=action, detail=message[:120], ok=True)
    if action == "chat":
        assistant.branches.persist(session=assistant.session)
    return result
