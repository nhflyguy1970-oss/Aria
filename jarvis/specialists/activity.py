"""Activity Center bridge for Specialist Team runs."""

from __future__ import annotations

from typing import Any


def publish_team_event(payload: dict[str, Any]) -> dict[str, Any]:
    status = str(payload.get("status") or "unknown")
    name = f"Specialists: {(payload.get('goal') or '')[:60]}"
    severity = "info"
    if status in ("failed", "timeout"):
        severity = "error"
    elif status in ("partial_success", "permission_required", "cancelled"):
        severity = "warning"
    elif status == "succeeded":
        severity = "success"

    # Prefer automation activity_bridge pattern for durability when available
    try:
        from jarvis.automation.activity_bridge import publish_run_event

        return publish_run_event(
            kind="specialist_team",
            name=name,
            status=status,
            target_id=str(payload.get("run_id") or ""),
            why=(payload.get("synthesis") or payload.get("summary") or status)[:500],
            dry_run=False,
            executed=status not in ("permission_required", "cancelled"),
            detail={
                "run_id": payload.get("run_id"),
                "job_id": payload.get("job_id"),
                "team": payload.get("team"),
                "correlation_id": payload.get("correlation_id"),
                "deep_link_run": f"specialists:run:{payload.get('run_id')}",
            },
            source="specialists",
        )
    except Exception:
        activity = {
            "category": "agents",
            "type": f"team_{status}",
            "severity": severity,
            "title": name,
            "summary": status,
            "deepLink": "jobs",
            "metadata": {
                "runId": payload.get("run_id"),
                "jobId": payload.get("job_id"),
                "team": payload.get("team"),
            },
            "read": status in ("succeeded",),
        }
        return {"ok": True, "activity": activity}
