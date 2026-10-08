"""Record managed-tool outcomes — one adapter, one contract.

Phase 1 replaced a broken ``memory.add`` call (wrong signature, swallowed
TypeError) with this adapter. That version wrote outcomes through the memory
API, which under ACM-primary encodes with *trusted user teaching* provenance —
so a coding agent's report of its own work would have entered ACM as
something the user had taught. ACM's ingestion policy (D046) exists precisely
to keep tool output out of autobiographical memory.

Outcomes now go to the continuity store as tool-actor outcome records: kept
locally, retrievable for "what did we finish?", clearly labelled as reported
by the tool rather than verified. The receipt says whether the record was
written; failures are logged and counted, never swallowed.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

logger = logging.getLogger("jarvis.tools.memory_sink")

TASK_CHARS = 200
SUMMARY_CHARS = 600

_lock = threading.Lock()
_status: dict[str, Any] = {"recorded": 0, "failed": 0, "last_error": None}


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
) -> dict[str, Any]:
    """Store one tool run's outcome. Never raises; the receipt reports what happened."""
    task = (task or "").strip()[:TASK_CHARS]
    summary = (summary or "").strip()[:SUMMARY_CHARS]
    try:
        from jarvis.continuity import record_tool_outcome as continuity_outcome

        record_id = continuity_outcome(tool_id, task, ok=ok, summary=summary, run_id=run_id)
    except Exception as exc:  # noqa: BLE001 - reported in the receipt and the log
        logger.warning("Tool outcome for %s not recorded: %s: %s", tool_id, type(exc).__name__, exc)
        return _receipt(False, error=f"{type(exc).__name__}: {exc}")
    return _receipt(True, record_id=record_id, store="continuity")


def status() -> dict[str, Any]:
    with _lock:
        return dict(_status)
