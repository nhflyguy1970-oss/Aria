"""Intent-aware presentation of Mission Control runtime snapshots.

Formatters only reshape live MC data for chat. No routing, Cap Bus,
cognition, or Mission Control API changes.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def _label(item: dict[str, Any]) -> str:
    return str(item.get("label") or item.get("name") or item.get("id") or "unknown")


def _is_up(item: dict[str, Any]) -> bool:
    if item.get("running") is True or item.get("healthy") is True:
        return True
    if item.get("stopped") is True:
        return False
    status = str(item.get("status") or item.get("state") or "").lower()
    return status in ("up", "running", "ready", "healthy", "ok", "active")


def _mb_to_gb(mb: Any) -> str | None:
    try:
        return f"{float(mb) / 1024.0:.1f} GB"
    except (TypeError, ValueError):
        return None


def _phase_name(payload: dict[str, Any]) -> str:
    phase = payload.get("phase") or {}
    if isinstance(phase, dict):
        return str(phase.get("phase") or "").strip()
    return str(phase or "").strip()


def operational_state(payload: dict[str, Any]) -> tuple[str, str]:
    """Return (display_state, detail) — never misleading STOPPED when live."""
    phase = payload.get("phase") or {}
    detail = ""
    name = ""
    if isinstance(phase, dict):
        name = str(phase.get("phase") or "").strip()
        detail = str(phase.get("detail") or "").strip()
    else:
        name = str(phase or "").strip()

    platform_status = str(
        payload.get("platform_status")
        or (payload.get("overview") or {}).get("platform_status")
        or ""
    ).lower()
    services = payload.get("services")
    service_list: list[Any] = []
    if isinstance(services, dict):
        service_list = list(services.get("services") or [])
    elif isinstance(services, list):
        service_list = services
    running = sum(1 for s in service_list if isinstance(s, dict) and _is_up(s))

    upper = name.upper()
    if upper in ("STOPPED", "STOPPING", "UNKNOWN", "") and (
        platform_status in ("healthy", "degraded", "ok") or running > 0
    ):
        if platform_status == "healthy" or running > 0:
            return "Idle", detail or "Workstation idle; services available"
        return "Ready", detail or "Workstation ready"
    if upper in ("READY", "PRODUCTION"):
        return "Ready", detail or name
    if upper == "DEGRADED":
        return "Degraded", detail or name
    if upper in ("STARTING", "INITIALIZING", "RECOVERING"):
        return name.title() or "Starting", detail
    if upper == "STOPPED":
        return "Stopped", detail or "Workstation stopped"
    return (name.title() if name else "Unknown"), detail


def _services_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    svc = payload.get("services")
    if isinstance(svc, list):
        return [s for s in svc if isinstance(s, dict)]
    if isinstance(svc, dict):
        inner = svc.get("services")
        if isinstance(inner, list):
            return [s for s in inner if isinstance(s, dict)]
    return []


def _databases_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    dbs = payload.get("databases")
    if isinstance(dbs, list):
        return [d for d in dbs if isinstance(d, dict)]
    svc = payload.get("services")
    if isinstance(svc, dict):
        inner = svc.get("databases")
        if isinstance(inner, list):
            return [d for d in inner if isinstance(d, dict)]
    return []


def format_services(payload: dict[str, Any]) -> str:
    services = _services_list(payload)
    running = [s for s in services if _is_up(s)]
    degraded = [
        s
        for s in services
        if not _is_up(s)
        and str(s.get("status") or "").lower() in ("degraded", "unhealthy", "error")
    ]
    lines = ["Running Services", ""]
    if running:
        for s in running:
            lines.append(f"✓ {_label(s)}")
    else:
        lines.append("• None reported running")
    lines.append("")
    lines.append(f"{len(running)} service{'s' if len(running) != 1 else ''} running.")
    if degraded:
        lines.append(f"{len(degraded)} degraded.")
        for s in degraded:
            lines.append(f"⚠ {_label(s)}")
    else:
        lines.append("No degraded services.")
    return "\n".join(lines)


def format_databases(payload: dict[str, Any]) -> str:
    dbs = _databases_list(payload)
    lines = ["Connected Databases", ""]
    if not dbs:
        lines.append("• No databases reported by Mission Control.")
        return "\n".join(lines)
    up = []
    down = []
    for d in dbs:
        if _is_up(d):
            up.append(d)
            lines.append(f"✓ {_label(d)}")
        else:
            down.append(d)
            lines.append(f"• {_label(d)} (down)")
    lines.append("")
    if down:
        lines.append(f"{len(up)} healthy, {len(down)} down.")
    else:
        lines.append("All healthy.")
    return "\n".join(lines)


def format_applications(payload: dict[str, Any]) -> str:
    apps = [a for a in (payload.get("applications") or []) if isinstance(a, dict)]
    running = [a for a in apps if _is_up(a)]
    stopped = [a for a in apps if not _is_up(a)]
    lines = ["Applications", ""]
    lines.append("Running")
    if running:
        for a in running:
            lines.append(f"✓ {_label(a)}")
    else:
        lines.append("• None")
    lines.append("")
    lines.append("Stopped")
    if stopped:
        for a in stopped:
            lines.append(f"• {_label(a)}")
    else:
        lines.append("• None")
    return "\n".join(lines)


def format_jobs(payload: dict[str, Any]) -> str:
    active = payload.get("active_jobs")
    jobs = payload.get("jobs") or {}
    if active is None and isinstance(jobs, dict):
        active = jobs.get("active_count")
        if active is None:
            active = jobs.get("busy_count")
        if active is None and jobs.get("any_busy") is False:
            active = 0
        if active is None and isinstance(jobs.get("recent"), list):
            active = sum(1 for j in jobs["recent"] if isinstance(j, dict) and j.get("busy"))
    try:
        count = int(active or 0)
    except (TypeError, ValueError):
        count = 0
    lines = ["Background Jobs", "", f"{count} active."]
    if count == 0:
        lines.append("The workstation is idle.")
    return "\n".join(lines)


def format_gpu(payload: dict[str, Any]) -> str:
    gpu = payload.get("gpu") if isinstance(payload.get("gpu"), dict) else {}
    hw = payload.get("hardware") if isinstance(payload.get("hardware"), dict) else {}
    name = gpu.get("name") or gpu.get("gpu_name") or hw.get("gpu_name") or "Not reported"
    free = gpu.get("free_vram_mb")
    if free is None:
        free = hw.get("free_vram_mb")
    free_s = _mb_to_gb(free) or (f"{free} MB" if free is not None else "Not reported")
    total = gpu.get("vram_mb") or hw.get("vram_mb")
    lines = [
        "Inference GPU",
        str(name),
        "",
        "Free VRAM",
        free_s,
    ]
    if total is not None:
        total_s = _mb_to_gb(total) or f"{total} MB"
        lines.extend(["", "Total VRAM", total_s])
    return "\n".join(lines)


def format_memory(payload: dict[str, Any]) -> str:
    """System RAM only — never VRAM."""
    hw = payload.get("hardware") if isinstance(payload.get("hardware"), dict) else {}
    available = payload.get("ram_available_gb")
    if available is None:
        available = hw.get("ram_available_gb")
    total = hw.get("ram_total_gb") or hw.get("ram_gb")
    swap = hw.get("swap_available_gb") or hw.get("swap_gb")
    lines = ["System RAM", ""]
    if available is not None:
        lines.append(f"Available: {available} GB")
    else:
        lines.append("Available: not reported by Mission Control")
    if total is not None and total != available:
        lines.append(f"Total: {total} GB")
    if swap is not None:
        lines.append(f"Swap: {swap} GB")
    lines.append("")
    lines.append("This is system RAM, not GPU VRAM.")
    return "\n".join(lines)


def format_storage(payload: dict[str, Any]) -> str:
    hw = payload.get("hardware") if isinstance(payload.get("hardware"), dict) else {}
    free = hw.get("disk_free_gb") or payload.get("disk_free_gb")
    lines = ["Storage", ""]
    if free is not None:
        lines.append(f"Disk free: {free} GB")
    else:
        lines.append("Disk free: not reported by Mission Control")
    return "\n".join(lines)


def format_network(payload: dict[str, Any]) -> str:
    hw = payload.get("hardware") if isinstance(payload.get("hardware"), dict) else {}
    net = payload.get("network") or hw.get("network")
    lines = ["Network", ""]
    if isinstance(net, dict) and net:
        for key, value in net.items():
            lines.append(f"{key}: {value}")
    elif net:
        lines.append(str(net))
    else:
        lines.append("Mission Control does not expose network details for this query.")
    return "\n".join(lines)


def format_inference(payload: dict[str, Any]) -> str:
    inf = payload.get("inference") if isinstance(payload.get("inference"), dict) else {}
    active = payload.get("active") or inf.get("active_models") or {}
    model = payload.get("current_model") or inf.get("current_model")
    if not model and isinstance(active, dict):
        model = active.get("current") or active.get("general") or active.get("coder")
    provider = payload.get("provider") or inf.get("provider") or "—"
    profile = (
        payload.get("profile")
        or inf.get("profile")
        or (payload.get("overview") or {}).get("profile")
    )
    device = payload.get("device") or inf.get("device") or inf.get("placement")
    ctx = payload.get("context_length") or inf.get("context_length") or inf.get("num_ctx")

    lines = ["Current Inference", ""]
    if model:
        lines.append(f"Model: `{model}`")
    else:
        lines.append("Model: Mission Control does not currently expose the active model.")
    lines.append(f"Provider: {provider}")
    if profile:
        lines.append(f"Profile: {profile}")
    if device:
        lines.append(f"Device: {device}")
    if ctx:
        lines.append(f"Context length: {ctx}")
    if isinstance(active, dict) and active:
        extras = {k: v for k, v in active.items() if v and v != model}
        if extras:
            lines.append("")
            lines.append("Active roles")
            for role, name in extras.items():
                lines.append(f"• {role}: `{name}`")
    return "\n".join(lines)


def format_health(payload: dict[str, Any]) -> str:
    state, detail = operational_state(payload)
    status = payload.get("platform_status") or "—"
    acc = payload.get("acceptance") or {}
    needs = [n for n in (payload.get("needs_attention") or []) if n and n != "All clear"]
    lines = [
        "Health",
        "",
        f"Platform: {status}",
        f"Operational state: {state}",
    ]
    if detail:
        lines.append(f"Detail: {detail}")
    if acc.get("overall") is not None:
        lines.append(
            f"Acceptance: {acc.get('overall')}% · readiness {acc.get('production_readiness')}%"
        )
    lines.append("")
    if needs:
        lines.append("Needs attention")
        for item in needs:
            lines.append(f"• {item}")
    else:
        lines.append("No issues needing attention.")
    return "\n".join(lines)


def format_attention(payload: dict[str, Any]) -> str:
    needs = [n for n in (payload.get("needs_attention") or []) if n]
    lines = ["What Needs Attention", ""]
    if not needs or needs == ["All clear"]:
        lines.append("All clear.")
        return "\n".join(lines)
    for item in needs:
        lines.append(f"• {item}")
    return "\n".join(lines)


def format_providers(payload: dict[str, Any]) -> str:
    prov = payload.get("providers") or {}
    lines = ["Providers", ""]
    if not prov:
        lines.append("Mission Control did not report providers.")
        return "\n".join(lines)
    for name, value in prov.items():
        lines.append(f"• {name}: `{value}`")
    return "\n".join(lines)


def format_status(payload: dict[str, Any], *, full: bool = False) -> str:
    state, detail = operational_state(payload)
    mode = payload.get("execution_mode") or "—"
    status = (
        payload.get("platform_status")
        or (payload.get("overview") or {}).get("platform_status")
        or "—"
    )
    services = _services_list(payload)
    running_n = sum(1 for s in services if _is_up(s))
    needs = [n for n in (payload.get("needs_attention") or []) if n and n != "All clear"]
    active = payload.get("active_jobs")
    if active is None:
        jobs = payload.get("jobs") or {}
        if isinstance(jobs, dict):
            active = jobs.get("active_count") or jobs.get("busy_count") or 0

    lines = [
        "Workstation Status",
        "",
        "Operational State",
        state,
    ]
    if detail:
        lines.append(detail)
    lines.extend(
        [
            "",
            f"Execution mode: `{mode}`",
            f"Health: {status}",
            f"Services running: {running_n}",
            f"Active jobs: {active if active is not None else '—'}",
        ]
    )
    if needs:
        lines.append("")
        lines.append("Needs attention")
        for item in needs[:5]:
            lines.append(f"• {item}")
    else:
        lines.append("")
        lines.append("All clear.")

    if not full:
        lines.extend(
            [
                "",
                "Ask for services, applications, GPU, RAM, models, or databases for detail.",
                'Say "full status" or "runtime report" for a complete dump.',
            ]
        )
        return "\n".join(lines)

    # Explicit full / diagnostics dump — structured, still not an API blob.
    lines.extend(["", "---", "", format_applications(payload)])
    lines.extend(["", "---", "", format_services(payload)])
    lines.extend(["", "---", "", format_databases(payload)])
    lines.extend(["", "---", "", format_inference(payload)])
    lines.extend(["", "---", "", format_gpu(payload)])
    lines.extend(["", "---", "", format_memory(payload)])
    lines.extend(["", "---", "", format_jobs(payload)])
    return "\n".join(lines)


def format_mode(payload: dict[str, Any]) -> str:
    state, detail = operational_state(payload)
    mode = payload.get("execution_mode") or "—"
    host = payload.get("host") or {}
    lines = [
        "Execution mode",
        f"`{mode}`",
        "",
        "Operational State",
        state,
    ]
    if detail:
        lines.append(detail)
    if host:
        attached = host.get("attached")
        healthy = host.get("healthy")
        lines.extend(["", f"ApplicationHost attached: {attached}", f"Healthy: {healthy}"])
    return "\n".join(lines)


_FORMATTERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "runtime_services": format_services,
    "runtime_databases": format_databases,
    "runtime_applications": format_applications,
    "runtime_jobs": format_jobs,
    "runtime_gpu": format_gpu,
    "runtime_ram": format_memory,
    "runtime_storage": format_storage,
    "runtime_network": format_network,
    "runtime_models": format_inference,
    "runtime_health": format_health,
    "runtime_attention": format_attention,
    "runtime_providers": format_providers,
    "runtime_mode": format_mode,
    "runtime_platform": format_mode,
}


def format_runtime_intent(action: str, payload: dict[str, Any]) -> str:
    """Dispatch to the intent formatter. Never returns the empty-match stub."""
    if action == "runtime_report":
        body = format_status(payload, full=True)
    elif action == "runtime_status":
        body = format_status(payload, full=False)
    elif action in _FORMATTERS:
        body = _FORMATTERS[action](payload)
    else:
        body = format_status(payload, full=False)
    return body.strip() + "\n"
