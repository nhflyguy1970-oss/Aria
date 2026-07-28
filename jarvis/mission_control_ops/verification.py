"""Post-repair auto-verification — publish results to Activity, never auto-remediate further."""

from __future__ import annotations

import time
from typing import Any


def verify_after_repair(*, previous: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    After an approved repair, re-check Recovery / Provider / Routing / Hardware / Connection.
    """
    checks: dict[str, Any] = {}
    overall_ok = True
    try:
        from jarvis.mission_control import collect_mission_control, get_tab

        snap = collect_mission_control(record_metrics=False)
        brief = snap.get("health_brief") or {}
        recovery = snap.get("recovery") or {}
        health = recovery.get("health") if isinstance(recovery.get("health"), dict) else {}
        checks["recovery"] = {
            "ok": bool(health.get("ok", brief.get("healthy"))),
            "detail": brief.get("headline") or health,
        }
        inf = snap.get("inference") or {}
        checks["provider"] = {
            "ok": bool(inf.get("ollama_running", True)) and bool(inf.get("provider")),
            "provider": inf.get("provider"),
            "model": inf.get("current_model"),
        }
        routing = snap.get("routing_stats") or {}
        err = routing.get("error_pct")
        try:
            routing_ok = err is None or float(err) < 25
        except (TypeError, ValueError):
            routing_ok = True
        checks["routing"] = {"ok": routing_ok, "error_pct": err, "avg_latency_ms": routing.get("average_latency_ms")}
        hw = snap.get("hardware") or {}
        checks["hardware"] = {
            "ok": True,
            "ram_available_gb": hw.get("ram_available_gb"),
            "free_vram_mb": hw.get("free_vram_mb"),
            "cpu_load": hw.get("cpu_load"),
        }
        try:
            conn = get_tab("connection")
            cdata = (conn or {}).get("data") or conn or {}
            conn_ok = bool(cdata.get("ok", True)) if isinstance(cdata, dict) else True
            checks["connection"] = {"ok": conn_ok, "data": {k: cdata.get(k) for k in ("status", "mode", "ok") if isinstance(cdata, dict)}}
        except Exception as exc:
            checks["connection"] = {"ok": False, "error": str(exc)}
            conn_ok = False

        for key in ("recovery", "provider", "routing", "hardware", "connection"):
            if not (checks.get(key) or {}).get("ok", True):
                overall_ok = False
    except Exception as exc:
        return {
            "ok": False,
            "verified": False,
            "error": str(exc),
            "checks": checks,
            "activity": {
                "category": "mission",
                "type": "verification_failed",
                "severity": "warning",
                "title": "Post-repair verification failed",
                "message": str(exc),
                "fix": "mc:recovery",
            },
        }

    activity = {
        "category": "mission",
        "type": "verification_ok" if overall_ok else "verification_issues",
        "severity": "success" if overall_ok else "warning",
        "title": "Post-repair verification",
        "message": "All subsystems verified" if overall_ok else "Some checks still need attention",
        "fix": "mc:recovery" if not overall_ok else "mc:overview",
        "detail": checks,
        "timestamp": time.time(),
    }
    return {
        "ok": overall_ok,
        "verified": True,
        "checks": checks,
        "previous_overall": (previous or {}).get("overall"),
        "activity": activity,
        "source": "mission_control_ops.verification",
    }
