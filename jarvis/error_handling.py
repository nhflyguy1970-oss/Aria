"""Structured error logging and user-safe error responses."""

from __future__ import annotations

import logging
import uuid
from typing import Any

logger = logging.getLogger("jarvis.errors")


def new_error_id() -> str:
    return uuid.uuid4().hex[:8]


def user_message(exc: BaseException, *, fallback: str = "Something went wrong.") -> str:
    """Short, user-facing message without stack traces."""
    text = str(exc).strip()
    if not text:
        return fallback
    if len(text) > 280:
        text = text[:277] + "..."
    if text == fallback:
        return fallback
    return f"{fallback} ({text})"


def log_exception(
    log: logging.Logger,
    exc: BaseException,
    *,
    action: str = "",
    module: str = "",
    detail: str = "",
    err_id: str = "",
    level: int = logging.ERROR,
) -> str:
    """Log an exception with context; return a stable reference id."""
    eid = err_id or new_error_id()
    parts = [p for p in (f"action={action}" if action else "", f"module={module}" if module else "", detail[:240]) if p]
    ctx = " | ".join(parts) if parts else "unhandled"
    log.log(level, "Error [%s] %s: %s", eid, ctx, exc, exc_info=exc)
    return eid


def report_error(
    log: logging.Logger,
    exc: BaseException,
    *,
    action: str = "",
    module: str = "",
    detail: str = "",
    err_id: str = "",
) -> str:
    """Log exception and append a structured row to action_log.json."""
    eid = log_exception(log, exc, action=action, module=module, detail=detail, err_id=err_id)
    try:
        from jarvis.action_log import log_event

        log_event(
            "error",
            error_id=eid,
            action=action or None,
            module=module or None,
            detail=(detail or str(exc))[:500],
            ok=False,
        )
    except Exception:
        logger.warning("Failed to persist error event [%s]", eid, exc_info=True)
    return eid


def assistant_error(
    exc: BaseException,
    *,
    action: str = "",
    message: str = "",
    module: str = "general",
    log: logging.Logger | None = None,
) -> dict:
    """Build a standard assistant error payload with a support reference id."""
    from jarvis.response import err

    eid = report_error(
        log or logging.getLogger("jarvis.assistant"),
        exc,
        action=action,
        module=module,
        detail=message,
    )
    return err(
        f"Something went wrong. Reference: **{eid}**",
        module=module,
        error_id=eid,
        action=action or None,
    )


def api_error_payload(
    exc: BaseException,
    *,
    request_path: str = "",
    err_id: str = "",
    include_detail: bool = False,
) -> dict[str, Any]:
    """JSON body for failed API routes."""
    log = logging.getLogger("jarvis.http")
    eid = report_error(
        log,
        exc,
        action="api",
        module="http",
        detail=request_path,
        err_id=err_id,
    )
    payload: dict[str, Any] = {
        "ok": False,
        "message": f"Server error. Reference: {eid}",
        "error_id": eid,
    }
    if include_detail:
        import traceback

        payload["detail"] = traceback.format_exc()[-800:]
    return payload
