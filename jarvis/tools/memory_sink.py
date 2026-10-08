"""Record managed-tool outcomes in ARIA's memory — one adapter, one contract.

The executor and the background runner used to call ``assistant.memory.add``
directly with a signature it does not have (content positionally where
entry_type belongs, plus an unsupported ``metadata`` keyword). Every call
raised TypeError, and both callers swallowed it — at debug level or not at all
— so no tool outcome was ever stored while the run looked successful.

This adapter calls the real API (``MemoryStore.add(entry_type, content, tags,
namespace=...)``), which routes to ACM when ACM is authoritative, and returns a
receipt saying whether the outcome was recorded. Callers attach the receipt to
their result, and failures are logged as warnings and counted, so a persistence
failure is visible rather than silent.

Outcomes are stored as diagnostic types (``success`` / ``failure``), not as
facts: a tool or coding agent reporting that it did something is a record of
the run, not a verified statement about the world or the user.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger("jarvis.tools.memory_sink")

NAMESPACE = "tools"
TASK_CHARS = 200
SUMMARY_CHARS = 600

_lock = threading.Lock()
_status: dict[str, Any] = {"recorded": 0, "failed": 0, "last_error": None}


def _default_memory() -> Any:
    from jarvis.assistant_instance import get_assistant

    return getattr(get_assistant(), "memory", None)


def _receipt(ok: bool, **fields: Any) -> dict[str, Any]:
    with _lock:
        _status["recorded" if ok else "failed"] += 1
        if not ok:
            _status["last_error"] = fields.get("error")
    return {"recorded": ok, **fields}


def record_tool_outcome(
    tool_id: str,
    task: str,
    *,
    ok: bool,
    summary: str = "",
    run_id: str = "",
    memory: Any = None,
) -> dict[str, Any]:
    """Store one tool run's outcome. Never raises; the receipt reports what happened."""
    task = (task or "").strip()[:TASK_CHARS]
    summary = (summary or "").strip()[:SUMMARY_CHARS]
    status = "completed" if ok else "failed"
    header = f"[tool:{tool_id}" + (f" run:{run_id}" if run_id else "") + f"] {status}"
    content = "\n".join(part for part in (header, task, summary) if part)
    tags = ["tool_result", f"tool:{tool_id}", status]

    try:
        store = memory if memory is not None else _default_memory()
    except Exception as exc:  # noqa: BLE001 - reported in the receipt
        logger.warning("Tool outcome for %s not recorded: memory unavailable (%s)", tool_id, exc)
        return _receipt(False, error=f"memory unavailable: {type(exc).__name__}: {exc}")
    if store is None:
        logger.warning("Tool outcome for %s not recorded: no memory store", tool_id)
        return _receipt(False, error="no memory store")

    try:
        entry = store.add(
            "success" if ok else "failure",
            content,
            tags,
            namespace=NAMESPACE,
        )
    except Exception as exc:  # noqa: BLE001 - reported in the receipt and the log
        logger.warning("Tool outcome for %s not recorded: %s: %s", tool_id, type(exc).__name__, exc)
        return _receipt(False, error=f"{type(exc).__name__}: {exc}")

    entry_id = entry.get("id") if isinstance(entry, dict) else None
    return _receipt(True, entry_id=entry_id, namespace=NAMESPACE)


def status() -> dict[str, Any]:
    with _lock:
        return dict(_status)
