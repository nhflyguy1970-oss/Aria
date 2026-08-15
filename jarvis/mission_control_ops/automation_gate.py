"""Expose Mission Control health to Automation — pause / delay / warn / skip."""

from __future__ import annotations

from typing import Any


def get_infrastructure_health(*, force: bool = False) -> dict[str, Any]:
    """Lightweight health summary for Automation gates.

    Delegates to the shared Mission Control lite path (Tier 3A) — do not re-collect
    Platform MC independently from /api/mission-control/health.
    """
    from jarvis.mission_control import health_summary

    return health_summary(force=force)


def evaluate_health_gate(
    *,
    mode: str | None = None,
    params: dict[str, Any] | None = None,
    rule_name: str = "",
) -> dict[str, Any]:
    """
    Decide whether Automation should proceed under current MC health.

    Modes (from rule params.health_gate or mode arg):
      - off / none: always allow
      - warn: allow but flag warning
      - delay: skip this tick (retry later) when unhealthy
      - skip: skip run when unhealthy
      - pause: block dangerous work when critical
    Default when omitted: warn for degraded, skip for critical.
    """
    p = params or {}
    gate = (mode or p.get("health_gate") or p.get("mc_health_gate") or "auto")
    gate = str(gate).strip().lower() or "auto"
    if gate in ("off", "none", "disabled", "false", "0"):
        return {"ok": True, "action": "allow", "gate": gate, "reason": "health gate disabled"}

    health = get_infrastructure_health()
    overall = health.get("overall")
    severity = health.get("severity")
    dangerous = bool(health.get("dangerous"))
    unhealthy = not health.get("ok")

    if gate == "auto":
        if dangerous or overall == "critical" or severity == "critical":
            gate = "skip"
        elif unhealthy:
            gate = "warn"
        else:
            return {
                "ok": True,
                "action": "allow",
                "gate": "auto",
                "health": health,
                "reason": "healthy",
            }

    if not unhealthy and not dangerous:
        return {"ok": True, "action": "allow", "gate": gate, "health": health, "reason": "healthy"}

    reason = (
        f"Mission Control {overall} ({severity})"
        + (f" — blocked for {rule_name}" if rule_name else "")
    )

    if gate == "warn":
        return {
            "ok": True,
            "action": "warn",
            "gate": gate,
            "health": health,
            "reason": reason,
            "warning": reason,
        }
    if gate == "delay":
        return {
            "ok": False,
            "action": "delay",
            "gate": gate,
            "health": health,
            "reason": reason,
            "status": "skipped",
            "skipped": True,
        }
    if gate == "pause":
        return {
            "ok": False,
            "action": "pause",
            "gate": gate,
            "health": health,
            "reason": reason,
            "status": "cancelled",
            "cancelled": True,
        }
    # skip (default for critical)
    return {
        "ok": False,
        "action": "skip",
        "gate": gate,
        "health": health,
        "reason": reason,
        "status": "skipped",
        "skipped": True,
    }
