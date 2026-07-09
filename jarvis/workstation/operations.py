"""Workstation operations — diagnose issues and recover safe failures."""

from __future__ import annotations

import logging
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


def diagnose(*, force: bool = False) -> dict[str, Any]:
    """Analyze workstation health and return actionable issues."""
    snap = registry_snapshot(force=force)
    issues: list[dict[str, Any]] = []

    for comp in snap.get("components") or []:
        cid = comp.get("id") or ""
        if comp.get("required") and not comp.get("running"):
            issues.append({
                "severity": "critical",
                "component": cid,
                "label": comp.get("label"),
                "message": f"Required component offline: {comp.get('label')}",
                "action": "restart" if cid in SAFE_RESTART else "start",
                "auto_recoverable": cid in SAFE_RESTART or comp.get("managed"),
            })
        elif comp.get("managed") and comp.get("autostart") and not comp.get("running"):
            issues.append({
                "severity": "warning",
                "component": cid,
                "label": comp.get("label"),
                "message": f"Autostart component offline: {comp.get('label')}",
                "action": "restart" if cid in SAFE_RESTART else "start",
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
            "auto_recoverable": False,
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


def recover_safe(*, max_attempts: int = 3) -> dict[str, Any]:
    """Attempt safe automatic recovery for known recoverable issues."""
    report = diagnose(force=True)
    attempts: list[dict[str, Any]] = []

    if not report.get("issues"):
        return {"ok": True, "message": "No issues detected", "attempts": attempts, "report": report}

    for issue in report.get("issues") or []:
        if not issue.get("auto_recoverable"):
            continue
        if len(attempts) >= max_attempts:
            break
        cid = issue.get("component") or ""
        action = issue.get("action") or "start"
        if action == "restart" and cid in SAFE_RESTART:
            result = restart(cid)
        elif action == "start":
            result = up(cid)
        else:
            continue
        attempts.append({
            "component": cid,
            "action": action,
            "ok": bool(result.get("ok")),
        })

    if not attempts:
        up()
        attempts.append({"component": "workstation", "action": "bootstrap", "ok": True})

    final = diagnose(force=True)
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
