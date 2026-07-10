"""Platform runtime bootstrap and startup self-test for Aria."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.platform_runtime")


def bootstrap_runtime_connection() -> dict[str, Any]:
    """Attach ApplicationHost and connect RuntimeClient to Mission Control."""
    from jarvis.runtime_client import get_runtime_client

    client = get_runtime_client()
    report = client.connect()
    validation = validate_runtime_startup()
    merged = {**report, **validation}
    if not merged.get("ok"):
        logger.warning(
            "Runtime connection incomplete: %s",
            "; ".join(merged.get("issues") or merged.get("warnings") or []),
        )
    else:
        logger.info(
            "Platform Connected · Mission Control Connected · Runtime Synced (%s)",
            merged.get("connection_mode"),
        )
    return merged


def validate_runtime_startup() -> dict[str, Any]:
    """Self-test after startup — never silently fall back."""
    from jarvis.runtime_client import RuntimeClientError, get_runtime_client

    client = get_runtime_client()
    report = client.connection_report()

    checks = {
        "mission_control_api": report.get("mission_control_reachable")
        or report.get("connection_mode") == "in_process",
        "runtime_client_connected": report.get("connection_mode") in ("http", "in_process"),
        "application_attached": report.get("application_registered"),
        "application_host": report.get("application_host_connected"),
        "heartbeat_active": report.get("heartbeat_age_seconds") is not None
        or report.get("connection_mode") == "in_process",
    }

    try:
        snap = client.snapshot(force_refresh=True, required=True)
        checks["snapshot_ok"] = snap.get("ok") is True
        checks["applications_visible"] = bool(snap.get("applications"))
        checks["services_visible"] = snap.get("services") is not None
        checks["providers_visible"] = bool(
            (snap.get("overview") or {}).get("inference_provider")
            or snap.get("inference")
        )
        report["runtime_synced"] = True
    except RuntimeClientError as exc:
        checks["snapshot_ok"] = False
        report["runtime_synced"] = False
        issues = list(report.get("issues") or [])
        issues.append(str(exc))
        report["issues"] = issues
        report["ok"] = False

    report["checks"] = checks
    if report.get("ok") and not all(checks.values()):
        report["ok"] = False
        issues = list(report.get("issues") or [])
        for name, passed in checks.items():
            if not passed:
                issues.append(f"check failed: {name}")
        report["issues"] = issues
    return report


def runtime_connection_status() -> dict[str, Any]:
    """Live connection diagnostics for API and UI."""
    from jarvis.runtime_client import get_runtime_client

    client = get_runtime_client()
    report = client.connection_report()
    report["checks"] = validate_runtime_startup().get("checks", {})
    return report
