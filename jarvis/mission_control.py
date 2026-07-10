"""AI Platform Mission Control — operational source of truth for the workstation."""

from __future__ import annotations

import getpass
import os
from datetime import datetime
from typing import Any

from jarvis.env_loader import PROJECT_ROOT
from jarvis.runtime_introspection import (
    _applications,
    _health,
    _host_status,
    _jobs,
    _knowledge_detail,
    _memory_detail,
    _models,
    _phase_status,
    _platform_attachment,
    _providers,
    _services_and_databases,
    _workspace_git,
    collect_runtime_status,
    execution_mode,
)

_TABS = (
    "overview",
    "applications",
    "inference",
    "memory",
    "knowledge",
    "databases",
    "hardware",
    "jobs",
    "activity",
    "performance",
    "settings",
    "recovery",
)


def _inference_detail() -> dict[str, Any]:
    models = _models()
    active = models.get("active") or {}
    providers = _providers()
    gateway = (providers.get("inference") or {}).get("gateway") or {}
    loaded: list[Any] = []
    try:
        from jarvis.resource_router import ollama_loaded_models

        loaded = ollama_loaded_models()
    except Exception:
        pass
    return {
        "provider": gateway.get("gateway_mode") or "ollama",
        "current_model": active.get("general") or active.get("coder"),
        "active_models": active,
        "loaded_models": loaded,
        "ollama_running": models.get("ollama_running"),
        "gateway": gateway,
        "litellm_available": gateway.get("litellm_available"),
        "cloud_enabled": gateway.get("cloud_enabled"),
        "low_vram": gateway.get("low_vram"),
    }


def _hardware_detail() -> dict[str, Any]:
    from jarvis.environment import snapshot

    env = snapshot(include_resources=True)
    resources = env.get("resources") or {}
    gpu = env.get("gpu") or {}
    cpu_load = None
    try:
        with open("/proc/loadavg", encoding="utf-8") as fh:
            cpu_load = float(fh.read().split()[0])
    except OSError:
        pass
    return {
        "cpu_load": cpu_load,
        "ram_total_gb": resources.get("ram_total_gb"),
        "ram_available_gb": resources.get("ram_available_gb"),
        "swap_used_gb": resources.get("swap_used_gb"),
        "gpu_name": gpu.get("name"),
        "vram_mb": gpu.get("vram_mb"),
        "free_vram_mb": gpu.get("free_vram_mb"),
        "disk_free_gb": env.get("disk_free_gb"),
        "ollama_models_loaded": resources.get("ollama_models_loaded"),
        "ollama_models": resources.get("ollama_models") or [],
        "recommendations": resources.get("recommendations") or [],
        "raw": resources,
    }


def _memory_extended() -> dict[str, Any]:
    base = _memory_detail()
    recent: list[dict[str, Any]] = []
    try:
        from jarvis.assistant_instance import get_assistant

        mem = get_assistant().memory
        if hasattr(mem, "list_entries"):
            for entry in mem.list_entries()[:12]:
                recent.append(
                    {
                        "id": entry.get("id"),
                        "namespace": entry.get("namespace"),
                        "type": entry.get("type"),
                        "content": (entry.get("content") or "")[:120],
                    }
                )
    except Exception:
        pass
    base["recent"] = recent
    try:
        from jarvis.platform_cutover import current_mode
        from jarvis.platform_cutover import status as cutover_status

        base["cutover_mode"] = current_mode()
        base["cutover"] = cutover_status()
    except Exception:
        base["cutover_mode"] = execution_mode()
    return base


def _applications_extended() -> list[dict[str, Any]]:
    ws = _workspace_git()
    host = _host_status()
    running = bool(host.get("healthy"))
    try:
        from jarvis.config import is_uncensored as _is_uncensored

        uncensored_active = _is_uncensored()
    except Exception:
        uncensored_active = False
    apps: list[dict[str, Any]] = [
        {
            "id": "aria",
            "label": os.getenv("JARVIS_ASSISTANT_NAME", "Aria"),
            "profile": "standard",
            "running": running,
            "stopped": not running,
            "healthy": running,
            "version": (host.get("capabilities") or {}).get("version", "3.1.0"),
            "project": ws.get("current_project") or "",
            "memory_namespace": os.getenv("JARVIS_MEMORY_NAMESPACE", "default"),
            "primary": True,
        },
        {
            "id": "aria-uncensored",
            "label": "Aria (Uncensored)",
            "profile": "uncensored",
            "running": running and uncensored_active,
            "stopped": not running,
            "healthy": running,
            "version": (host.get("capabilities") or {}).get("version", "3.1.0"),
            "project": ws.get("current_project") or "",
            "memory_namespace": "uncensored",
            "primary": False,
        },
    ]
    for app in _applications():
        if app.get("id") in ("aria",):
            continue
        apps.append(
            {
                **app,
                "profile": app.get("id"),
                "running": bool(app.get("healthy")),
                "stopped": not app.get("healthy"),
                "project": "",
                "memory_namespace": "",
            }
        )
    return apps


def _recovery_detail() -> dict[str, Any]:
    health = _health()
    acc: dict[str, Any] = {}
    try:
        from jarvis.application.standalone.workstation_impl.acceptance import last_acceptance

        acc = last_acceptance() or {}
    except Exception:
        pass
    backup = "none"
    backup_dir = PROJECT_ROOT / "backups"
    if backup_dir.is_dir():
        archives = sorted(backup_dir.glob("workstation_*.tar.gz"), reverse=True)
        if archives:
            backup = archives[0].name
    return {
        "health": health,
        "acceptance": acc,
        "latest_backup": backup,
        "log_paths": [
            str(PROJECT_ROOT / "data" / "logs" / "jarvis.log"),
            str(PROJECT_ROOT / "data" / "logs" / "desktop-launch.log"),
            str(PROJECT_ROOT / "data" / "logs" / "workstation_activity.jsonl"),
        ],
        "known_issues": [
            "Optional containers (n8n, MongoDB, Open WebUI) may be stopped — not required for Aria.",
            "First chat after cold start may take 30–45s while models load.",
            "Platform cutover verified but compatibility mode remains enabled by design.",
        ],
        "recommended_actions": _recommended_actions(health, acc),
    }


def _recommended_actions(health: dict[str, Any], acc: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if not health.get("ok"):
        actions.append("Run Repair from Recovery tab or type `workstation repair` in terminal.")
    scores = acc.get("score") or {}
    if scores.get("daily_required", 100) < 100:
        actions.append("Run acceptance: `workstation acceptance`")
    phase = (_phase_status() or {}).get("phase")
    if phase not in ("READY", None, "unknown"):
        actions.append(f"Wait for startup to finish (phase: {phase})")
    if not actions:
        actions.append("No action required — workstation is healthy.")
    return actions


def _settings_snapshot() -> dict[str, Any]:
    return {
        "profile": os.getenv("JARVIS_PROFILE", "default"),
        "host": os.getenv("JARVIS_HOST", "127.0.0.1"),
        "port": os.getenv("JARVIS_PORT", "8765"),
        "gui_mode": os.getenv("JARVIS_GUI_MODE", "fluent"),
        "platform_attached": os.getenv("JARVIS_PLATFORM_ATTACHED") == "1",
        "data_dir": str(PROJECT_ROOT / "data"),
        "install_path": str(PROJECT_ROOT),
    }


def collect_overview() -> dict[str, Any]:
    status = collect_runtime_status()
    inf = _inference_detail()
    mem = _memory_detail()
    know = _knowledge_detail()
    hw = _hardware_detail()
    jobs = _jobs()
    acc = status.get("acceptance") or {}
    ws = status.get("workspace") or {}
    host = status.get("host") or {}
    active_jobs = (
        jobs.get("active_count") or jobs.get("busy_count") or len(jobs.get("recent") or [])
    )
    return {
        "platform_status": "healthy" if (status.get("services") or {}).get("ready") else "degraded",
        "phase": status.get("phase"),
        "acceptance_overall": acc.get("overall"),
        "production_readiness": acc.get("production_readiness"),
        "execution_mode": status.get("execution_mode"),
        "user": getpass.getuser(),
        "project": ws.get("current_project") or "",
        "current_model": inf.get("current_model"),
        "inference_provider": inf.get("provider"),
        "memory_provider": mem.get("provider"),
        "knowledge_provider": know.get("retrieval"),
        "gpu": hw.get("gpu_name"),
        "cpu_load": hw.get("cpu_load"),
        "ram_available_gb": hw.get("ram_available_gb"),
        "vram_mb": hw.get("vram_mb"),
        "free_vram_mb": hw.get("free_vram_mb"),
        "active_jobs": active_jobs,
        "attached": host.get("attached"),
        "healthy": host.get("healthy"),
        "aria_branch": ws.get("aria_branch"),
        "needs_attention": _recovery_detail().get("recommended_actions") or [],
    }


def collect_mission_control(*, record_metrics: bool = True) -> dict[str, Any]:
    """Full Mission Control snapshot — source of truth for dashboard and Aria status."""
    from jarvis.platform_metrics import list_samples, record_sample
    from jarvis.platform_notifications import list_notifications
    from jarvis.workstation_activity import list_events

    overview = collect_overview()
    if record_metrics:
        record_sample(
            {
                "acceptance": overview.get("acceptance_overall"),
                "ram_gb": overview.get("ram_available_gb"),
                "vram_mb": overview.get("free_vram_mb"),
                "active_jobs": overview.get("active_jobs"),
            }
        )

    svc = _services_and_databases()
    return {
        "ok": True,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "title": "AI Platform Mission Control",
        "overview": overview,
        "applications": _applications_extended(),
        "inference": _inference_detail(),
        "memory": _memory_extended(),
        "knowledge": _knowledge_detail(),
        "databases": svc.get("databases") or [],
        "services": svc.get("services") or [],
        "services_ready": svc.get("ready"),
        "hardware": _hardware_detail(),
        "jobs": _jobs(),
        "activity": {"events": list_events(limit=100)},
        "performance": {"samples": list_samples(limit=60)},
        "recovery": _recovery_detail(),
        "notifications": list_notifications(limit=15),
        "settings": _settings_snapshot(),
        "runtime": {
            "mode": execution_mode(),
            "phase": _phase_status(),
            "host": _host_status(),
            "platform": _platform_attachment(),
        },
        "providers": _providers(),
        "git": _workspace_git(),
    }


def get_tab(tab: str) -> dict[str, Any]:
    """Return one Mission Control section."""
    full = collect_mission_control(record_metrics=False)
    key = tab.strip().lower()
    if key not in _TABS:
        return {"ok": False, "error": f"unknown tab: {tab}", "tabs": list(_TABS)}
    return {
        "ok": True,
        "tab": key,
        "data": full.get(key) if key != "overview" else full.get("overview"),
    }


def format_overview_markdown() -> str:
    """Brief status for Aria chat commands — always from Mission Control."""
    mc = collect_mission_control(record_metrics=False)
    ov = mc.get("overview") or {}
    phase = (ov.get("phase") or {}).get("phase", "?")
    lines = [
        "## AI Platform Mission Control",
        "",
        f"**Status:** {ov.get('platform_status', '?')}",
        f"**Mode:** {ov.get('execution_mode', '?')}",
        f"**Phase:** {phase}",
        f"**Acceptance:** {ov.get('acceptance_overall', '—')}%",
        f"**Production readiness:** {ov.get('production_readiness', '—')}%",
        f"**Project:** {ov.get('project') or '—'}",
        f"**Model:** `{ov.get('current_model') or '—'}`",
        f"**Inference:** {ov.get('inference_provider', '—')}",
        f"**Memory:** {ov.get('memory_provider', '—')}",
        f"**Knowledge:** {ov.get('knowledge_provider', '—')}",
        f"**GPU:** {ov.get('gpu') or '—'}",
        f"**RAM available:** {ov.get('ram_available_gb', '—')} GB",
        f"**VRAM free:** {ov.get('free_vram_mb', '—')} MB",
        f"**Active jobs:** {ov.get('active_jobs', 0)}",
        "",
    ]
    needs = ov.get("needs_attention") or []
    if needs:
        lines.append("**Needs attention:**")
        for item in needs[:4]:
            lines.append(f"- {item}")
        lines.append("")
    lines.append("_Source: Mission Control (live)._")
    return "\n".join(lines)


def export_activity_csv(*, limit: int = 200) -> str:
    from jarvis.workstation_activity import list_events

    events = list_events(limit=limit)
    lines = ["timestamp,type,component,status,duration_ms,detail"]
    for ev in reversed(events):
        detail = (ev.get("detail") or "").replace('"', '""')
        lines.append(
            f"{ev.get('iso', '')},{ev.get('type', '')},{ev.get('component', '')},"
            f'{ev.get("status", "")},{ev.get("duration_ms") or ""},"{detail}"'
        )
    return "\n".join(lines) + "\n"
