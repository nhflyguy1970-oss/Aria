"""Expanded workstation operations — diagnose, recover, notify."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from jarvis.workstation.lifecycle import restart, up
from jarvis.workstation.registry import all_components, registry_snapshot

logger = logging.getLogger("jarvis.workstation")

SAFE_RESTART = frozenset({
    "ollama",
    "comfyui",
    "homeassistant",
    "litellm",
    "postgres",
    "redis",
    "qdrant",
    "mongodb",
    "open_webui",
    "n8n",
})

_START_INSTEAD_OF_RESTART = frozenset({"ollama"})


def _issue_action(component_id: str) -> str:
    if component_id in _START_INSTEAD_OF_RESTART:
        return "start"
    if component_id in SAFE_RESTART:
        return "restart"
    return "start"


def _check_scheduler() -> dict[str, Any] | None:
    try:
        from jarvis import proactive_scheduler

        thread = proactive_scheduler._thread
        alive = thread is not None and thread.is_alive()
        if not alive:
            return {
                "severity": "warning",
                "component": "scheduler",
                "label": "Proactive Scheduler",
                "message": "Proactive scheduler thread is not running",
                "action": "restart_scheduler",
                "auto_recoverable": True,
            }
    except Exception as exc:
        logger.debug("scheduler check: %s", exc)
    return None


def _check_vector_store() -> dict[str, Any] | None:
    backend = os.getenv("JARVIS_VECTOR_BACKEND", "sqlite").strip().lower()
    if backend in ("sqlite", "chroma", "qdrant_embedded"):
        return None
    if backend == "qdrant" and os.getenv("JARVIS_QDRANT_URL"):
        return None
    comp = next((c for c in all_components() if c.id == "qdrant"), None)
    if comp and not comp.healthy():
        return {
            "severity": "warning",
            "component": "qdrant",
            "label": "Qdrant",
            "message": "Vector store (Qdrant) is unhealthy",
            "action": "restart",
            "auto_recoverable": True,
        }
    return None


def _check_failed_jobs() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    try:
        from jarvis.jobs.checkpointed import list_jobs

        failed = [j for j in list_jobs(status="failed")[:3]]
        if failed:
            issues.append({
                "severity": "warning",
                "component": "agent_jobs",
                "label": "Agent Jobs",
                "message": f"{len(failed)} failed agent job(s) — latest: {failed[0].goal[:60]}",
                "action": "alert",
                "auto_recoverable": False,
            })
    except Exception:
        pass
    return issues


def _check_platform() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if os.getenv("JARVIS_DISABLE_PLATFORM_ATTACHMENT", "").lower() in ("1", "true", "yes"):
        return issues
    try:
        from jarvis.platform_attachment import validate_platform_startup

        startup = validate_platform_startup()
        if startup:
            issues.append({
                "severity": "warning",
                "component": "platform",
                "label": "AI Platform",
                "message": f"Platform startup issues: {'; '.join(startup[:2])}",
                "action": "alert",
                "auto_recoverable": False,
            })
    except Exception:
        pass
    return issues


def diagnose(*, force: bool = False) -> dict[str, Any]:
    """Analyze workstation health and return actionable issues."""
    snap = registry_snapshot(force=force)
    issues: list[dict[str, Any]] = []

    for comp in snap.get("components") or []:
        cid = comp.get("id") or ""
        if comp.get("required") and not comp.get("running"):
            action = _issue_action(cid)
            issues.append({
                "severity": "critical",
                "component": cid,
                "label": comp.get("label"),
                "message": f"Required component offline: {comp.get('label')}",
                "action": action,
                "auto_recoverable": cid in SAFE_RESTART or comp.get("managed"),
            })
        elif comp.get("managed") and comp.get("autostart") and not comp.get("running"):
            action = _issue_action(cid)
            issues.append({
                "severity": "warning",
                "component": cid,
                "label": comp.get("label"),
                "message": f"Autostart component offline: {comp.get('label')}",
                "action": action,
                "auto_recoverable": cid in SAFE_RESTART,
            })

    resources = snap.get("resources") or {}
    if resources.get("low_vram"):
        issues.append({
            "severity": "warning",
            "component": "gpu",
            "label": "GPU VRAM",
            "message": "Low VRAM — consider unloading Ollama models before media jobs",
            "action": "unload_models",
            "auto_recoverable": True,
        })

    env = snap.get("environment") or {}
    disk = env.get("disk_free_gb") or 0
    if disk and disk < 10:
        issues.append({
            "severity": "warning",
            "component": "storage",
            "label": "Disk",
            "message": f"Low disk space: {disk}GB free on data volume",
            "action": "alert",
            "auto_recoverable": False,
        })

    for extra in (_check_scheduler(), _check_vector_store()):
        if extra:
            issues.append(extra)
    issues.extend(_check_failed_jobs())
    issues.extend(_check_platform())

    critical = sum(1 for i in issues if i.get("severity") == "critical")
    warning = sum(1 for i in issues if i.get("severity") == "warning")

    return {
        "ok": critical == 0,
        "issues": issues,
        "critical": critical,
        "warnings": warning,
        "status": snap,
        "ts": time.time(),
    }


def _recover_issue(issue: dict[str, Any]) -> dict[str, Any]:
    cid = issue.get("component") or ""
    action = issue.get("action") or "start"

    if action == "unload_models":
        try:
            from jarvis.vram_guard import free_vram

            result = free_vram()
            return {"component": cid, "action": action, "ok": bool(result.get("ok", True))}
        except Exception as exc:
            return {"component": cid, "action": action, "ok": False, "error": str(exc)}

    if action == "restart_scheduler":
        try:
            from jarvis.proactive_scheduler import start

            start()
            return {"component": cid, "action": action, "ok": True}
        except Exception as exc:
            return {"component": cid, "action": action, "ok": False, "error": str(exc)}

    if action == "restart" and cid in SAFE_RESTART:
        result = restart(cid)
        return {"component": cid, "action": action, "ok": bool(result.get("ok"))}

    if action == "start":
        result = up(cid)
        return {"component": cid, "action": action, "ok": bool(result.get("ok"))}

    return {"component": cid, "action": action, "ok": False, "skipped": True}


def recover_safe(*, max_attempts: int = 3) -> dict[str, Any]:
    """Attempt safe automatic recovery for known recoverable issues."""
    report = diagnose(force=True)
    attempts: list[dict[str, Any]] = []

    if not report.get("issues"):
        return {"ok": True, "message": "No issues detected", "attempts": attempts, "report": report}

    per_component: dict[str, int] = {}
    for issue in report.get("issues") or []:
        if not issue.get("auto_recoverable"):
            continue
        cid = issue.get("component") or ""
        if per_component.get(cid, 0) >= 1:
            continue
        if len(attempts) >= max_attempts:
            break
        attempt = _recover_issue(issue)
        attempts.append(attempt)
        per_component[cid] = per_component.get(cid, 0) + 1
        if attempt.get("ok") and issue.get("action") in ("restart", "start"):
            time.sleep(2)

    if not attempts:
        up()
        attempts.append({"component": "workstation", "action": "bootstrap", "ok": True})

    final = diagnose(force=True)
    human_needed = [i for i in final.get("issues") or [] if not i.get("auto_recoverable")]
    if human_needed and final.get("critical", 0) > 0:
        try:
            from jarvis.interrupt_policy import evaluate_interrupt

            labels = ", ".join(i.get("label", "") for i in human_needed[:3])
            evaluate_interrupt(
                "workstation_critical",
                title="ARIA workstation",
                body=f"Needs attention: {labels}",
                tier="urgent",
            )
        except Exception:
            pass

    return {
        "ok": final.get("ok", False),
        "attempts": attempts,
        "report": final,
    }


def format_report(*, force: bool = False) -> str:
    """Human-readable workstation operations report."""
    report = diagnose(force=force)
    snap = report.get("status") or {}
    summary = snap.get("summary") or {}
    lines = [
        "## Workstation Status",
        f"**{'Healthy' if report.get('ok') else 'Issues detected'}** — "
        f"{summary.get('running', 0)}/{summary.get('total', 0)} components running",
    ]

    resources = snap.get("resources") or {}
    gpu = (snap.get("environment") or {}).get("gpu") or {}
    if gpu.get("name"):
        vram = resources.get("free_vram_mb") or gpu.get("free_vram_mb") or gpu.get("vram_mb")
        lines.append(f"GPU: **{gpu.get('name')}** · {vram}MB VRAM free")
    if resources.get("ram_available_gb"):
        lines.append(f"RAM: **{resources['ram_available_gb']}GB** available")

    required_down = snap.get("required_down") or []
    if required_down:
        lines.append(f"**Required offline:** {', '.join(required_down)}")

    issues = report.get("issues") or []
    if issues:
        lines.append("\n### Issues")
        for issue in issues[:8]:
            sev = issue.get("severity", "info").upper()
            lines.append(f"- [{sev}] {issue.get('message')}")

    optional_down = snap.get("optional_down") or []
    if optional_down:
        lines.append(f"\nOptional offline: {', '.join(optional_down[:6])}")

    return "\n".join(lines)


def list_managed_components() -> list[dict[str, str]]:
    return [
        {"id": c.id, "label": c.label, "category": c.category, "running": str(c.healthy())}
        for c in all_components()
        if c.managed
    ]
