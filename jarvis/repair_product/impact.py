"""Repair impact + priority — what Jeff will feel before approving."""

from __future__ import annotations

from typing import Any

# Known subsystem universe for "not affected" contrast
ALL_SUBSYSTEMS = (
    "providers",
    "search",
    "documents",
    "gallery",
    "health",
    "acm",
    "coding",
    "mission_control",
    "browser",
    "smarthome",
    "docker",
    "jobs",
    "system",
    "aria",
    "security",
    "voice",
    "calendar",
    "planner",
    "flytying",
    "ocr",
)

PRIORITY_ORDER = ("critical", "high", "medium", "low", "informational")

_MODULE_IMPACT: dict[str, dict[str, Any]] = {
    "provider_ollama": {
        "affected": ["providers", "coding", "voice"],
        "downtime_hint": "inference pauses briefly",
        "restart": True,
        "data_risk": "none",
        "config_risk": "none",
        "user_interruption": "chat/generation may pause",
        "priority": "critical",
        "monitor_seconds": [30, 120, 300],
    },
    "search_index": {
        "affected": ["search", "documents"],
        "downtime_hint": "search results may be empty during rebuild",
        "restart": False,
        "data_risk": "none — source documents preserved",
        "config_risk": "none",
        "user_interruption": "search unavailable briefly",
        "priority": "high",
        "monitor_seconds": [30, 120, 300],
    },
    "documents_index": {
        "affected": ["documents", "search", "ocr"],
        "downtime_hint": "document search lag during rebuild",
        "restart": False,
        "data_risk": "none — files preserved",
        "config_risk": "none",
        "user_interruption": "document search delayed",
        "priority": "high",
        "monitor_seconds": [30, 120, 300],
    },
    "scheduler": {
        "affected": ["jobs"],
        "downtime_hint": "proactive nudges pause briefly",
        "restart": False,
        "data_risk": "none",
        "config_risk": "none",
        "user_interruption": "minimal",
        "priority": "medium",
        "monitor_seconds": [30, 120],
    },
    "docker_services": {
        "affected": ["docker", "providers"],
        "downtime_hint": "dependent containers briefly restart",
        "restart": True,
        "data_risk": "low — volumes preserved",
        "config_risk": "low",
        "user_interruption": "services may flicker",
        "priority": "high",
        "monitor_seconds": [30, 120, 300],
    },
    "health_store": {
        "affected": ["health"],
        "downtime_hint": "Health API may pause during migrate",
        "restart": False,
        "data_risk": "none — migrations only, no row deletes",
        "config_risk": "none",
        "user_interruption": "Health view briefly unavailable",
        "priority": "high",
        "monitor_seconds": [30, 120, 300],
    },
    "aria_restart": {
        "affected": ["aria", "mission_control"],
        "downtime_hint": "full UI/API restart",
        "restart": True,
        "data_risk": "none",
        "config_risk": "none",
        "user_interruption": "reconnect required",
        "priority": "high",
        "monitor_seconds": [30, 120, 300],
    },
    "caches_temp": {
        "affected": ["system"],
        "downtime_hint": "none expected",
        "restart": False,
        "data_risk": "none — only old temp files",
        "config_risk": "none",
        "user_interruption": "none",
        "priority": "low",
        "monitor_seconds": [30],
    },
    "mission_control_cache": {
        "affected": ["mission_control"],
        "downtime_hint": "sparklines refresh",
        "restart": False,
        "data_risk": "none",
        "config_risk": "none",
        "user_interruption": "none",
        "priority": "low",
        "monitor_seconds": [30, 120],
    },
    "gallery_metadata": {
        "affected": ["gallery"],
        "downtime_hint": "gallery listing may refresh",
        "restart": False,
        "data_risk": "none — metadata only",
        "config_risk": "none",
        "user_interruption": "brief",
        "priority": "medium",
        "monitor_seconds": [30, 120],
    },
    "home_assistant": {
        "affected": ["smarthome"],
        "downtime_hint": "HA commands pause during reconnect",
        "restart": False,
        "data_risk": "none",
        "config_risk": "none",
        "user_interruption": "brief",
        "priority": "medium",
        "monitor_seconds": [30, 120],
    },
    "background_jobs": {
        "affected": ["jobs"],
        "downtime_hint": "jobs resume",
        "restart": False,
        "data_risk": "none",
        "config_risk": "none",
        "user_interruption": "none",
        "priority": "medium",
        "monitor_seconds": [30, 120, 300],
    },
    "browser_websocket": {
        "affected": ["browser"],
        "downtime_hint": "browser session reconnects",
        "restart": False,
        "data_risk": "none",
        "config_risk": "none",
        "user_interruption": "brief",
        "priority": "low",
        "monitor_seconds": [30],
    },
    "destructive_guard": {
        "affected": ["security"],
        "downtime_hint": "n/a — refused by policy",
        "restart": False,
        "data_risk": "critical if ever allowed",
        "config_risk": "critical",
        "user_interruption": "n/a",
        "priority": "informational",
        "monitor_seconds": [],
    },
}


def severity_to_priority(severity: str, module_id: str = "") -> str:
    meta = _MODULE_IMPACT.get(module_id) or {}
    if meta.get("priority"):
        # Escalate module default if severity is critical
        if severity == "critical":
            return "critical"
        return str(meta["priority"])
    return {
        "critical": "critical",
        "warning": "medium",
        "info": "informational",
        "error": "high",
    }.get((severity or "").lower(), "medium")


def build_impact(module_id: str, *, estimated_seconds: float = 0, risk: str = "low") -> dict[str, Any]:
    meta = dict(_MODULE_IMPACT.get(module_id) or {})
    affected = list(meta.get("affected") or [module_id])
    not_affected = [s for s in ALL_SUBSYSTEMS if s not in affected]
    downtime = float(estimated_seconds or 0)
    return {
        "affected": affected,
        "not_affected": not_affected,
        "expected_downtime_seconds": downtime,
        "expected_downtime_label": f"{int(round(downtime))} seconds" if downtime < 60 else f"{downtime/60:.1f} minutes",
        "restart_required": bool(meta.get("restart")),
        "data_risk": meta.get("data_risk") or "unknown",
        "configuration_risk": meta.get("config_risk") or "unknown",
        "user_interruption": meta.get("user_interruption") or "unknown",
        "downtime_hint": meta.get("downtime_hint") or "",
        "risk": risk,
        "monitor_seconds": list(meta.get("monitor_seconds") or [30, 120, 300]),
        "priority_default": meta.get("priority") or "medium",
    }


def priority_rank(priority: str) -> int:
    try:
        return PRIORITY_ORDER.index((priority or "medium").lower())
    except ValueError:
        return 2


def sort_by_priority(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        issues,
        key=lambda i: (
            priority_rank(i.get("priority") or "medium"),
            0 if i.get("severity") == "critical" else 1,
            -float(i.get("confidence") or 0),
        ),
    )
