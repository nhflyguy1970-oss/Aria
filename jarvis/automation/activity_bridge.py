"""Publish Automation events into Activity Center (server-side log + client hook via API)."""

from __future__ import annotations

from typing import Any

from jarvis.automation.execution import badge_for
from jarvis.automation.history import record_run
from jarvis.automation.mute import is_muted


def publish_run_event(
    *,
    kind: str,
    name: str,
    status: str,
    target_id: str = "",
    why: str = "",
    what_changed: Any = None,
    what_did_not: Any = None,
    dry_run: bool = False,
    executed: bool = False,
    detail: dict[str, Any] | None = None,
    source: str = "automation",
) -> dict[str, Any]:
    """Record history always; Activity payload returned for UI to ingest (and logged)."""
    if target_id and is_muted(target_id):
        entry = record_run(
            kind=kind,
            name=name,
            status=status,
            source=source,
            target_id=target_id,
            why=why or "muted",
            what_changed=what_changed,
            what_did_not=what_did_not,
            dry_run=dry_run,
            executed=executed,
            detail={**(detail or {}), "muted": True},
        )
        return {"ok": True, "muted": True, "run": entry, "activity": None}

    entry = record_run(
        kind=kind,
        name=name,
        status=status,
        source=source,
        target_id=target_id,
        why=why,
        what_changed=what_changed,
        what_did_not=what_did_not,
        dry_run=dry_run,
        executed=executed,
        detail=detail,
    )

    severity = "info"
    if status == "failed" or status == "timeout":
        severity = "error"
    elif status in ("skipped", "permission_required", "partial_success"):
        severity = "warning"
    elif status == "succeeded":
        severity = "success"
    elif status == "dry_run":
        severity = "info"

    # Quiet successes: still recorded in history; Activity only for non-success or failures
    emit_activity = status not in ("succeeded",) or kind in ("webhook",)
    # Actually spec wants run completed too — emit all but mark success read-friendly
    activity = {
        "category": "automation" if kind != "home" else "home",
        "type": f"run_{status}",
        "severity": severity,
        "title": f"Automation {status}: {name}",
        "summary": why or status,
        "detail": why or status,
        "source": source,
        "deepLink": "automation",
        "metadata": {
            "runId": entry["id"],
            "targetId": target_id,
            "kind": kind,
            "status": status,
            "dryRun": dry_run,
        },
        "read": status in ("succeeded", "dry_run"),
        "tone": badge_for(status),
    }
    if not emit_activity and status == "succeeded":
        # Still emit but start read to reduce fatigue
        activity["read"] = True

    return {"ok": True, "run": entry, "activity": activity}
