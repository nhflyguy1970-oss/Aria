"""Platform runtime bootstrap and startup self-test for Aria."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

logger = logging.getLogger("jarvis.platform_runtime")


def bootstrap_runtime_connection() -> dict[str, Any]:
    """Attach ApplicationHost and connect RuntimeClient to Mission Control."""
    from jarvis.runtime_client import get_runtime_client

    client = get_runtime_client()
    report = client.connect()

    def _self_test() -> None:
        """Validate the runtime, off the boot path.

        The self-test forces a full Mission Control snapshot — a dashboard
        aggregation that shells out to the GitHub CLI and rebuilds the ACM
        dashboard, around 5.4s. It is a self-test that logs; nothing waits on
        its result, so running it inline simply delayed the moment ARIA could
        answer a request. It still runs, and still reports, every boot.
        """
        merged = dict(report)
        # The snapshot warm-up runs in its own thread; judging the runtime
        # before it has finished would report "not synced yet" every boot.
        deadline = time.time() + 60.0
        while time.time() < deadline:
            if client.connection_report().get("runtime_synced"):
                break
            time.sleep(0.5)
        try:
            merged.update(validate_runtime_startup())
        except Exception as exc:  # noqa: BLE001 - a self-test must not kill the process
            logger.warning("Runtime self-test failed: %s", exc)
            merged["ok"] = False
        try:
            from jarvis.intelligence.platform_bus import bootstrap_platform

            intel = bootstrap_platform(start_automation=True)
            merged["intelligence"] = {
                "ok": bool(intel.get("ok")),
                "connectors": intel.get("connectors"),
                "workflows_seeded": intel.get("workflows_seeded"),
                "automation": (intel.get("automation") or {}).get("running"),
            }
        except Exception as exc:
            logger.warning("Intelligence platform bootstrap skipped: %s", exc)
            merged["intelligence"] = {"ok": False, "error": str(exc)}
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

    threading.Thread(target=_self_test, name="runtime-self-test", daemon=True).start()
    return report


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
            (snap.get("overview") or {}).get("inference_provider") or snap.get("inference")
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
