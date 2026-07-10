"""Runtime introspection — live state from AI Platform Mission Control only."""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

from jarvis.env_loader import PROJECT_ROOT
from jarvis.runtime_client import RuntimeClientError, get_runtime_client

# Questions about Aria / the workstation itself — never RAG or web search.
_RUNTIME_SELF = (
    r"(?:you|aria|jarvis|your(?:self)?|the (?:assistant|workstation|ai workstation)|"
    r"this (?:instance|system|workstation|machine))"
)
_RUNTIME_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        rf"\b(?:what|who) are you\b|"
        rf"\btell me about (?:yourself|{_RUNTIME_SELF})\b|"
        rf"\bdescribe (?:yourself|{_RUNTIME_SELF})\b",
        re.I,
    ),
    re.compile(
        r"\b(?:standalone|attached|compatibility|platform[- ]?authoritative)\b.*"
        r"\b(?:mode|running|attached|connected)\b|"
        r"\b(?:running|attached|connected)\b.*"
        r"\b(?:standalone|attached|ai[- ]?platform|platform)\b|"
        r"\bam i running\b.*\b(?:standalone|attached|platform)\b",
        re.I,
    ),
    re.compile(
        rf"\b(?:are|is) {_RUNTIME_SELF}\b.*\b(?:attached|connected|running on|using)\b|"
        rf"\b(?:what|which) (?:mode|execution mode)\b.*\b(?:running|using|in)\b|"
        rf"\b{_RUNTIME_SELF}\b.*\b(?:health|status|mode|providers?|services?)\b|"
        rf"\b(?:your|aria'?s?|workstation) (?:health|status|mode|state)\b",
        re.I,
    ),
    re.compile(
        r"\bwhat (?:model|models|llm)\b.*\b(?:using|running|loaded|active|on)\b|"
        r"\bwhich model\b.*\b(?:using|running|loaded)\b|"
        r"\bcurrent model\b|"
        r"\bwhat(?:'s| is) (?:the )?(?:loaded|active|current) model\b",
        re.I,
    ),
    re.compile(
        r"\bwhat (?:services?|databases?|providers?)\b.*\b(?:running|connected|attached|up)\b|"
        r"\bwhich (?:services?|databases?|providers?)\b.*\b(?:running|connected|attached)\b|"
        r"\bwhat(?:'s| is) (?:running|connected)\b|"
        r"\bwhat applications\b.*\b(?:running|active)\b|"
        r"\bwhat(?:'s| is) (?:the )?phase\b|"
        r"\bwhat needs attention\b",
        re.I,
    ),
    re.compile(
        r"\bwhat are you running on\b|"
        r"\bwhat (?:gpu|cpu|hardware)\b.*\b(?:using|have|available)\b|"
        r"\bruntime[_ ](?:status|health|mode|providers?|services?|models?|jobs?|gpu|platform)\b",
        re.I,
    ),
    re.compile(
        r"\bworkstation (?:phase|acceptance|readiness|health|status)\b|"
        r"\bwhat phase\b.*\b(?:workstation|platform|system)\b|"
        r"\bproduction readiness\b|"
        r"\bactive jobs\b|"
        r"\bwhat jobs\b.*\b(?:active|running)\b|"
        r"\bwhat needs attention\b|"
        r"\brecent errors\b",
        re.I,
    ),
)

_RUNTIME_ACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\b(?:execution |runtime )?mode\b|standalone|attached|platform[- ]?authoritative|compatibility\b",
            re.I,
        ),
        "runtime_mode",
    ),
    (re.compile(r"\bhealth\b|diagnos", re.I), "runtime_health"),
    (re.compile(r"\bproviders?\b", re.I), "runtime_providers"),
    (
        re.compile(r"\bservices?\b|databases?\b|redis|postgres|mongo|qdrant\b", re.I),
        "runtime_services",
    ),
    (re.compile(r"\bmodels?\b|ollama|litellm\b", re.I), "runtime_models"),
    (re.compile(r"\bgpu\b|vram\b|cpu\b|memory\b|hardware\b", re.I), "runtime_gpu"),
    (re.compile(r"\bjobs?\b|background tasks?\b|queues?\b", re.I), "runtime_jobs"),
    (re.compile(r"\bplatform\b|cutover\b|attachment\b", re.I), "runtime_platform"),
    (re.compile(r"\bapplications?\b", re.I), "runtime_applications"),
)


def is_runtime_introspection_question(message: str) -> bool:
    text = (message or "").strip()
    if len(text) < 4:
        return False
    return any(p.search(text) for p in _RUNTIME_PATTERNS)


def classify_runtime_action(message: str) -> str:
    text = (message or "").strip()
    lower = text.lower()
    literal = {
        "runtime_status": "runtime_status",
        "runtime_mode": "runtime_mode",
        "runtime_health": "runtime_health",
        "runtime_platform": "runtime_platform",
        "runtime_services": "runtime_services",
        "runtime_models": "runtime_models",
        "runtime_gpu": "runtime_gpu",
        "runtime_jobs": "runtime_jobs",
        "runtime_providers": "runtime_providers",
        "runtime_applications": "runtime_applications",
    }
    if lower in literal:
        return literal[lower]
    for pattern, action in _RUNTIME_ACTION_PATTERNS:
        if pattern.search(text):
            return action
    return "runtime_status"


def route_runtime_introspection(message: str) -> dict[str, Any] | None:
    if not is_runtime_introspection_question(message):
        return None
    action = classify_runtime_action(message)
    return {"action": action, "params": {}, "thinking": "runtime introspection"}


def _mc_snapshot(*, required: bool = True) -> dict[str, Any]:
    return get_runtime_client().snapshot(required=required)


def _identity() -> dict[str, Any]:
    return {
        "name": os.getenv("JARVIS_ASSISTANT_NAME", "Aria"),
        "version": "3.1.0",
        "install_path": str(PROJECT_ROOT),
    }


def execution_mode() -> str:
    try:
        mc = _mc_snapshot(required=False)
        if mc.get("ok"):
            ov = mc.get("overview") or {}
            mode = ov.get("execution_mode")
            if mode:
                return str(mode)
    except RuntimeClientError:
        pass
    return "disconnected"


def collect_runtime_status() -> dict[str, Any]:
    """Full live runtime snapshot from Mission Control."""
    mc = _mc_snapshot(required=True)
    ov = mc.get("overview") or {}
    return {
        "ok": True,
        "ts": mc.get("ts") or datetime.now().isoformat(timespec="seconds"),
        "source": "mission_control",
        "connection_mode": mc.get("connection_mode"),
        "identity": _identity(),
        "execution_mode": ov.get("execution_mode"),
        "phase": ov.get("phase"),
        "acceptance": {
            "overall": ov.get("acceptance_overall"),
            "production_readiness": ov.get("production_readiness"),
        },
        "providers": {
            "inference": ov.get("inference_provider"),
            "memory": ov.get("memory_provider"),
            "knowledge": ov.get("knowledge_provider"),
        },
        "services": {
            "ready": mc.get("services_ready"),
            "services": mc.get("services") or [],
            "databases": mc.get("databases") or [],
        },
        "models": mc.get("inference") or {},
        "gpu": mc.get("hardware") or {},
        "jobs": mc.get("jobs") or {},
        "applications": mc.get("applications") or [],
        "activity": mc.get("activity") or {},
        "performance": mc.get("performance") or {},
        "recovery": mc.get("recovery") or {},
        "health": mc.get("recovery") or {},
        "overview": ov,
        "needs_attention": ov.get("needs_attention") or [],
    }


def collect_runtime_mode() -> dict[str, Any]:
    mc = _mc_snapshot(required=True)
    ov = mc.get("overview") or {}
    apps = mc.get("applications") or []
    aria = next((a for a in apps if a.get("id") == "aria"), {})
    return {
        "ok": True,
        "source": "mission_control",
        "execution_mode": ov.get("execution_mode"),
        "phase": ov.get("phase"),
        "host": {
            "attached": bool(aria.get("running") or aria.get("healthy")),
            "healthy": aria.get("healthy"),
            "application": aria,
        },
        "platform": {
            "execution_mode": ov.get("execution_mode"),
            "platform_status": ov.get("platform_status"),
        },
    }


def collect_runtime_platform() -> dict[str, Any]:
    return collect_runtime_mode()


def collect_runtime_applications() -> dict[str, Any]:
    mc = _mc_snapshot(required=True)
    return {
        "ok": True,
        "source": "mission_control",
        "applications": mc.get("applications") or [],
    }


def collect_runtime_providers() -> dict[str, Any]:
    mc = _mc_snapshot(required=True)
    ov = mc.get("overview") or {}
    return {
        "ok": True,
        "source": "mission_control",
        "execution_mode": ov.get("execution_mode"),
        "providers": {
            "inference": ov.get("inference_provider"),
            "memory": ov.get("memory_provider"),
            "knowledge": ov.get("knowledge_provider"),
        },
        "inference": mc.get("inference") or {},
        "memory": mc.get("memory") or {},
        "knowledge": mc.get("knowledge") or {},
    }


def collect_runtime_services() -> dict[str, Any]:
    mc = _mc_snapshot(required=True)
    return {
        "ok": True,
        "source": "mission_control",
        "ready": mc.get("services_ready"),
        "services": mc.get("services") or [],
        "databases": mc.get("databases") or [],
    }


def collect_runtime_models() -> dict[str, Any]:
    mc = _mc_snapshot(required=True)
    inf = mc.get("inference") or {}
    ov = mc.get("overview") or {}
    return {
        "ok": True,
        "source": "mission_control",
        "active": inf.get("active_models") or {"current": ov.get("current_model")},
        "current_model": ov.get("current_model") or inf.get("current_model"),
        "provider": ov.get("inference_provider") or inf.get("provider"),
        "inference": inf,
    }


def collect_runtime_gpu() -> dict[str, Any]:
    mc = _mc_snapshot(required=True)
    hw = mc.get("hardware") or {}
    ov = mc.get("overview") or {}
    return {
        "ok": True,
        "source": "mission_control",
        "gpu": {
            "name": ov.get("gpu") or hw.get("gpu_name"),
            "vram_mb": ov.get("vram_mb") or hw.get("vram_mb"),
            "free_vram_mb": ov.get("free_vram_mb") or hw.get("free_vram_mb"),
        },
        "cpu_load": ov.get("cpu_load") or hw.get("cpu_load"),
        "ram_available_gb": ov.get("ram_available_gb") or hw.get("ram_available_gb"),
        "hardware": hw,
    }


def collect_runtime_jobs() -> dict[str, Any]:
    mc = _mc_snapshot(required=True)
    jobs = mc.get("jobs") or {}
    ov = mc.get("overview") or {}
    return {
        "ok": True,
        "source": "mission_control",
        "jobs": jobs,
        "active_jobs": ov.get("active_jobs"),
    }


def collect_runtime_health() -> dict[str, Any]:
    mc = _mc_snapshot(required=True)
    ov = mc.get("overview") or {}
    recovery = mc.get("recovery") or {}
    return {
        "ok": True,
        "source": "mission_control",
        "platform_status": ov.get("platform_status"),
        "health": recovery,
        "phase": ov.get("phase"),
        "acceptance": {
            "overall": ov.get("acceptance_overall"),
            "production_readiness": ov.get("production_readiness"),
        },
        "services": {
            "ready": mc.get("services_ready"),
            "services": mc.get("services") or [],
        },
        "needs_attention": ov.get("needs_attention") or [],
    }


_COLLECTORS: dict[str, Any] = {
    "runtime_status": collect_runtime_status,
    "runtime_mode": collect_runtime_mode,
    "runtime_platform": collect_runtime_platform,
    "runtime_applications": collect_runtime_applications,
    "runtime_providers": collect_runtime_providers,
    "runtime_services": collect_runtime_services,
    "runtime_models": collect_runtime_models,
    "runtime_gpu": collect_runtime_gpu,
    "runtime_jobs": collect_runtime_jobs,
    "runtime_health": collect_runtime_health,
}


def collect_runtime(action: str) -> dict[str, Any]:
    fn = _COLLECTORS.get(action, collect_runtime_status)
    try:
        data = fn()
        return {"ok": True, "action": action, "data": data, "source": "mission_control"}
    except RuntimeClientError as exc:
        return {
            "ok": False,
            "action": action,
            "error": str(exc),
            "source": "none",
            "message": _format_connection_warning(str(exc)),
        }


def _format_connection_warning(detail: str) -> str:
    return (
        "Mission Control could not provide live runtime information.\n\n"
        f"{detail}\n\n"
        "Start **AI Platform** and ensure Mission Control is reachable. "
        "Aria does not answer runtime questions from local state, RAG, embeddings, or web search."
    )


def format_runtime_markdown(action: str, data: dict[str, Any] | None = None) -> str:
    if data is not None and data.get("ok") is False:
        return data.get("message") or _format_connection_warning(data.get("error", "unknown"))

    payload = data if data is not None else _COLLECTORS.get(action, collect_runtime_status)()
    if isinstance(payload, dict) and payload.get("ok") is False:
        return _format_connection_warning(payload.get("error", "unknown"))

    lines = ["## Aria Runtime Report", ""]

    if action in ("runtime_status", "runtime_mode", "runtime_platform"):
        mode = payload.get("execution_mode")
        if mode:
            lines.append(f"**Execution mode:** `{mode}`")
        host = payload.get("host") or {}
        if host:
            lines.append(
                f"**ApplicationHost:** attached={host.get('attached')}, "
                f"healthy={host.get('healthy')}"
            )
        phase = payload.get("phase") or {}
        if isinstance(phase, dict) and phase.get("phase"):
            lines.append(
                f"**Workstation phase:** `{phase.get('phase')}` — {phase.get('detail', '')}"
            )

    if action in ("runtime_status", "runtime_health"):
        acc = payload.get("acceptance") or {}
        if acc.get("overall") is not None:
            lines.append(
                f"**Acceptance:** {acc.get('overall')}% overall, "
                f"production readiness {acc.get('production_readiness')}%"
            )
        status = payload.get("platform_status")
        if status:
            lines.append(f"**Platform status:** {status}")
        needs = payload.get("needs_attention") or []
        if needs:
            lines.append("**Needs attention:**")
            lines.extend(f"- {item}" for item in needs)

    if action in ("runtime_status", "runtime_models", "runtime_providers"):
        model = payload.get("current_model")
        if not model:
            models = payload.get("models") or payload.get("inference") or {}
            if isinstance(models, dict):
                model = models.get("current_model")
                active = models.get("active_models") or models.get("active")
                if active and isinstance(active, dict):
                    lines.append("**Models:**")
                    for role, name in active.items():
                        if name:
                            lines.append(f"- {role}: `{name}`")
        if model:
            lines.append(f"**Current model:** `{model}`")

    if action in ("runtime_status", "runtime_services"):
        svc = payload.get("services") or payload
        if isinstance(svc, dict):
            services = svc.get("services") if "services" in svc else svc
            if isinstance(services, list) and services:
                running = [s.get("name") or s.get("id") for s in services if s.get("running")]
                lines.append(f"**Services running:** {', '.join(running) or 'none'}")
            dbs = svc.get("databases") if isinstance(svc, dict) else payload.get("databases")
            if dbs:
                db_line = ", ".join(
                    f"{d.get('name') or d.get('id')}={'up' if d.get('running') else 'down'}"
                    for d in dbs
                )
                lines.append(f"**Databases:** {db_line}")

    if action in ("runtime_status", "runtime_applications"):
        apps = payload.get("applications") or []
        if apps:
            lines.append("**Applications:**")
            for app in apps:
                label = app.get("label") or app.get("id")
                state = "running" if app.get("running") else "stopped"
                lines.append(f"- {label}: {state}")

    if action in ("runtime_status", "runtime_providers"):
        prov = payload.get("providers") or {}
        if prov:
            lines.append("**Providers:**")
            for name, value in prov.items():
                lines.append(f"- {name}: `{value}`")

    if action in ("runtime_status", "runtime_gpu"):
        gpu = payload.get("gpu") or {}
        if gpu.get("name"):
            lines.append(f"**GPU:** {gpu.get('name')}")
        if gpu.get("free_vram_mb") is not None:
            lines.append(f"**Free VRAM:** {gpu.get('free_vram_mb')} MB")

    if action in ("runtime_status", "runtime_jobs"):
        active = payload.get("active_jobs")
        if active is None:
            jobs = payload.get("jobs") or {}
            active = jobs.get("active_count") or jobs.get("busy_count") or 0
        lines.append(f"**Active background jobs:** {active}")

    if len(lines) <= 2:
        lines.append("_No live Mission Control fields matched this query._")
    lines.append("")
    lines.append("_Source: AI Platform Mission Control (live)._")
    return "\n".join(lines)


def runtime_action_result(action: str) -> dict[str, Any]:
    result = collect_runtime(action)
    if not result.get("ok"):
        return {
            "ok": False,
            "message": result.get("message") or _format_connection_warning(result.get("error", "")),
            "error": result.get("error"),
            "source": "none",
        }
    data = result["data"]
    return {
        "ok": True,
        "message": format_runtime_markdown(action, data),
        "data": data,
        "source": "mission_control",
    }


STATUS_COMMANDS: dict[str, str] = {
    "status": "status_summary",
    "health": "runtime_health",
    "services": "runtime_services",
    "models": "runtime_models",
    "memory": "runtime_providers",
    "providers": "runtime_providers",
    "gpu": "runtime_gpu",
    "jobs": "runtime_jobs",
}


def is_status_command(message: str) -> str | None:
    text = (message or "").strip().lower()
    if text.startswith("/"):
        text = text[1:].strip()
    if text in STATUS_COMMANDS:
        return STATUS_COMMANDS[text]
    literal = {
        "runtime_status": "runtime_status",
        "runtime_mode": "runtime_mode",
        "runtime_health": "runtime_health",
        "runtime_platform": "runtime_platform",
        "runtime_services": "runtime_services",
        "runtime_models": "runtime_models",
        "runtime_gpu": "runtime_gpu",
        "runtime_jobs": "runtime_jobs",
        "runtime_providers": "runtime_providers",
        "runtime_applications": "runtime_applications",
    }
    return literal.get(text)


def collect_dashboard() -> dict[str, Any]:
    return _mc_snapshot(required=True)


def format_status_summary(data: dict[str, Any] | None = None) -> str:
    from jarvis.mission_control import format_overview_markdown

    try:
        return format_overview_markdown()
    except Exception as exc:
        return _format_connection_warning(str(exc))


def format_startup_summary() -> dict[str, Any]:
    from jarvis.platform_runtime import runtime_connection_status

    conn = runtime_connection_status()
    greeting = "Hello"
    try:
        from jarvis.morning_briefing import personalized_greeting

        greeting = personalized_greeting()
    except Exception:
        pass

    if not conn.get("runtime_synced"):
        summary = _format_connection_warning(
            "; ".join(conn.get("issues") or ["Mission Control not synced"])
        )
        return {
            "ok": False,
            "greeting": greeting,
            "markdown": summary,
            "summary": summary,
            "connection": conn,
            "dashboard": {},
        }

    snap = collect_runtime_status()
    summary = format_status_summary(snap)
    return {
        "ok": True,
        "greeting": greeting,
        "markdown": summary.replace("## AI Platform Mission Control", f"## {greeting}"),
        "summary": summary,
        "connection": conn,
        "dashboard": collect_dashboard(),
    }
