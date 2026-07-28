"""Honest automation execution semantics — never conflate skipped/dry-run with success."""

from __future__ import annotations

from typing import Any

# Canonical run states
QUEUED = "queued"
WAITING = "waiting"
RUNNING = "running"
PAUSED = "paused"
SKIPPED = "skipped"
CANCELLED = "cancelled"
SUCCEEDED = "succeeded"
FAILED = "failed"
DRY_RUN = "dry_run"
PARTIAL_SUCCESS = "partial_success"
TIMEOUT = "timeout"
PERMISSION_REQUIRED = "permission_required"

TERMINAL = frozenset(
    {
        SKIPPED,
        CANCELLED,
        SUCCEEDED,
        FAILED,
        DRY_RUN,
        PARTIAL_SUCCESS,
        TIMEOUT,
        PERMISSION_REQUIRED,
    }
)

SUCCESS_LIKE = frozenset({SUCCEEDED, DRY_RUN, PARTIAL_SUCCESS})


def normalize_result(
    result: dict[str, Any] | None,
    *,
    dry_run: bool = False,
    default_status: str | None = None,
) -> dict[str, Any]:
    """Normalize any engine result into an honest execution payload."""
    raw = dict(result or {})
    if dry_run:
        status = DRY_RUN
        ok = True  # dry-run completed as a dry-run (not an execution success claim)
        executed = False
    elif raw.get("permission_required") or raw.get("status") == PERMISSION_REQUIRED:
        status = PERMISSION_REQUIRED
        ok = False
        executed = False
    elif raw.get("cancelled") or raw.get("status") == CANCELLED:
        status = CANCELLED
        ok = False
        executed = False
    elif raw.get("timeout") or raw.get("status") == TIMEOUT:
        status = TIMEOUT
        ok = False
        executed = True
    elif raw.get("skipped") or raw.get("status") == SKIPPED:
        # CRITICAL: skipped is NOT success
        status = SKIPPED
        ok = False
        executed = False
    elif raw.get("partial") or raw.get("status") == PARTIAL_SUCCESS:
        status = PARTIAL_SUCCESS
        ok = True
        executed = True
    elif raw.get("ok") is True and not raw.get("skipped"):
        status = SUCCEEDED
        ok = True
        executed = True
    elif raw.get("ok") is False:
        status = FAILED
        ok = False
        executed = True
    elif default_status:
        status = default_status
        ok = status in SUCCESS_LIKE and status != SKIPPED
        executed = status not in (SKIPPED, DRY_RUN, CANCELLED, PERMISSION_REQUIRED, QUEUED, WAITING)
    else:
        status = FAILED
        ok = False
        executed = False

    why = (
        raw.get("why")
        or raw.get("reason")
        or raw.get("error")
        or raw.get("message")
        or (
            "Dry run — nothing was executed"
            if status == DRY_RUN
            else "No handler for this action"
            if status == SKIPPED
            else "Completed"
            if status == SUCCEEDED
            else "Failed"
        )
    )
    changed = raw.get("changed")
    if changed is None:
        changed = [] if not executed or status in (DRY_RUN, SKIPPED) else raw.get("result")
    not_changed = raw.get("not_changed")
    if not_changed is None:
        not_changed = why if status in (SKIPPED, DRY_RUN, CANCELLED) else ""

    return {
        "ok": ok and status != SKIPPED,  # skipped never reports product-level ok
        "status": status,
        "executed": executed,
        "dry_run": status == DRY_RUN or dry_run,
        "skipped": status == SKIPPED,
        "why": str(why),
        "what_changed": changed,
        "what_did_not": not_changed,
        "raw": {k: v for k, v in raw.items() if k not in ("variables",)},
    }


def is_success(status: str) -> bool:
    return status == SUCCEEDED


def badge_for(status: str) -> str:
    return {
        SUCCEEDED: "ok",
        FAILED: "err",
        SKIPPED: "warn",
        DRY_RUN: "info",
        PARTIAL_SUCCESS: "warn",
        PERMISSION_REQUIRED: "warn",
        TIMEOUT: "err",
        CANCELLED: "info",
        RUNNING: "info",
        QUEUED: "info",
    }.get(status, "info")
