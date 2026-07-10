"""Runtime introspection — live application state without RAG, search, or hallucination."""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

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
        r"\bwhat(?:'s| is) (?:running|connected)\b",
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
        r"\bproduction readiness\b|"
        r"\bactive jobs\b|"
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
)


def is_runtime_introspection_question(message: str) -> bool:
    """True when the user asks about Aria's live runtime — not external knowledge."""
    text = (message or "").strip()
    if len(text) < 4:
        return False
    return any(p.search(text) for p in _RUNTIME_PATTERNS)


def classify_runtime_action(message: str) -> str:
    """Pick the most specific runtime action for a self-introspection question."""
    text = (message or "").strip()
    for pattern, action in _RUNTIME_ACTION_PATTERNS:
        if pattern.search(text):
            return action
    return "runtime_status"


def route_runtime_introspection(message: str) -> dict[str, Any] | None:
    """Return a router intent dict when message is runtime self-introspection."""
    if not is_runtime_introspection_question(message):
        return None
    action = classify_runtime_action(message)
    return {"action": action, "params": {}, "thinking": "runtime introspection"}


def execution_mode() -> str:
    """standalone | attached | compatibility | platform-authoritative."""
    from jarvis.platform_cutover import current_mode

    cutover = current_mode()
    if cutover == "platform_authoritative":
        return "platform-authoritative"
    attached = os.getenv("JARVIS_PLATFORM_ATTACHED") == "1"
    try:
        import aiplatform  # noqa: F401

        platform_available = True
    except ImportError:
        platform_available = False
    if attached or platform_available:
        if cutover in ("dual_write", "legacy"):
            return "compatibility"
        return "attached"
    return "standalone"


def _host_status() -> dict[str, Any]:
    try:
        from jarvis.application.host import HOST
        from jarvis.platform_attachment import is_attached

        caps = HOST.capabilities()
        return {
            "attached": is_attached(),
            "healthy": HOST.health(),
            "capabilities": {
                "id": caps.id,
                "label": caps.label,
                "version": caps.version,
                "features": list(caps.features or []),
            },
            "configuration": HOST.configuration(),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _platform_attachment() -> dict[str, Any]:
    layers = {
        "infrastructure": "JARVIS_PLATFORM_ATTACHED",
        "inference": "JARVIS_PLATFORM_INFERENCE_ATTACHED",
        "memory": "JARVIS_PLATFORM_MEMORY_ATTACHED",
        "semantic_memory": "JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED",
        "knowledge_retrieval": "JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED",
        "tool_capability": "JARVIS_PLATFORM_TOOL_CAPABILITY_ATTACHED",
        "workflow_orchestration": "JARVIS_PLATFORM_WORKFLOW_ORCHESTRATION_ATTACHED",
    }
    return {
        "execution_mode": execution_mode(),
        "application_id": os.getenv("JARVIS_PLATFORM_APPLICATION", "aria"),
        "layers": {name: os.getenv(env) == "1" for name, env in layers.items()},
        "data_authoritative": os.getenv("JARVIS_PLATFORM_DATA_AUTHORITATIVE") == "1",
    }


def _cutover_status() -> dict[str, Any]:
    try:
        from jarvis.platform_cutover import status

        return status()
    except Exception as exc:
        return {"error": str(exc)}


def _phase_status() -> dict[str, Any]:
    try:
        from jarvis.application.standalone.workstation_impl.phase import phase_snapshot

        return phase_snapshot()
    except Exception:
        return {"phase": "unknown"}


def _acceptance_summary() -> dict[str, Any]:
    try:
        from jarvis.application.standalone.workstation_impl.acceptance import (
            last_acceptance,
            run_acceptance,
        )

        report = last_acceptance() or run_acceptance(persist=False, live=False)
        scores = report.get("score") or {}
        summary = report.get("summary") or {}
        return {
            "acceptance_passed": report.get("acceptance_passed"),
            "overall": scores.get("overall"),
            "daily_required": scores.get("daily_required"),
            "integration": scores.get("integration"),
            "production_readiness": scores.get("production_readiness"),
            "ready": summary.get("ready"),
            "needs_attention": summary.get("needs_attention"),
            "not_installed": summary.get("not_installed"),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _providers() -> dict[str, Any]:
    providers: dict[str, Any] = {}
    env_map = {
        "memory": "JARVIS_PLATFORM_MEMORY_ATTACHED",
        "knowledge": "JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED",
        "semantic_memory": "JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED",
        "inference": "JARVIS_PLATFORM_INFERENCE_ATTACHED",
        "workflow": "JARVIS_PLATFORM_WORKFLOW_ORCHESTRATION_ATTACHED",
        "tools": "JARVIS_PLATFORM_TOOL_CAPABILITY_ATTACHED",
    }
    for name, env in env_map.items():
        providers[name] = {
            "platform_attached": os.getenv(env) == "1",
            "source": "platform" if os.getenv(env) == "1" else "local",
        }
    try:
        from jarvis.inference.gateway import gateway_status

        providers["inference"]["gateway"] = gateway_status()
    except Exception:
        pass
    try:
        import aiplatform.scheduler.registry as sched_reg  # type: ignore[import-untyped]

        providers["scheduler"] = {
            "providers": sched_reg.schedule_registry.providers(),
            "count": len(sched_reg.schedule_registry.all()),
        }
    except Exception:
        providers["scheduler"] = {"source": "unavailable"}
    return providers


def _services_and_databases() -> dict[str, Any]:
    try:
        from jarvis.services import get_status

        status = get_status(force=False)
        services = status.get("services") or []
        db_ids = {"postgres", "redis", "mongodb", "qdrant"}
        return {
            "ready": status.get("ready"),
            "services": services,
            "databases": [s for s in services if s.get("id") in db_ids],
            "ollama": status.get("ollama"),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _models() -> dict[str, Any]:
    try:
        from jarvis.assistant_instance import get_assistant

        status = get_assistant().get_status()
        return {
            "active": status.get("models"),
            "ollama_running": status.get("ollama", {}).get("running"),
            "embed_available": status.get("embed_available"),
            "vision_model": status.get("vision_model"),
            "gpu": status.get("gpu"),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _gpu_cpu_memory() -> dict[str, Any]:
    payload: dict[str, Any] = {}
    try:
        from jarvis.environment import snapshot

        env = snapshot(include_resources=True)
        payload["environment"] = env
        payload["gpu"] = env.get("gpu") or {}
        payload["resources"] = env.get("resources") or {}
    except Exception as exc:
        payload["error"] = str(exc)
    return payload


def _jobs() -> dict[str, Any]:
    try:
        from jarvis.jobs_center import snapshot

        return snapshot()
    except Exception as exc:
        return {"error": str(exc)}


def _workspace_git() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "install_path": str(PROJECT_ROOT),
        "workspace": os.getcwd(),
    }
    platform_root = PROJECT_ROOT.parent / "AI-Platform"
    if platform_root.is_dir():
        payload["platform_root"] = str(platform_root)
    for label, path in (("aria", PROJECT_ROOT), ("ai_platform", platform_root)):
        if not path.is_dir() or not (path / ".git").is_dir():
            continue
        try:
            branch = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            dirty = subprocess.run(
                ["git", "-C", str(path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=8,
            )
            payload[f"{label}_branch"] = (branch.stdout or "").strip() or "?"
            payload[f"{label}_dirty"] = bool((dirty.stdout or "").strip())
        except Exception:
            payload[f"{label}_branch"] = "unavailable"
    try:
        from jarvis.active_project import get_active_project, get_active_slug

        meta = get_active_project() or {}
        payload["current_project"] = (
            meta.get("name") or meta.get("label") or get_active_slug() or ""
        )
    except Exception:
        payload["current_project"] = os.getenv("JARVIS_PROJECT", "")
    return payload


def _health() -> dict[str, Any]:
    try:
        from jarvis.workstation.operations import diagnose

        return diagnose(force=False)
    except Exception:
        try:
            from jarvis.application.standalone.workstation_impl.operations import diagnose

            return diagnose(force=False)
        except Exception as exc:
            return {"error": str(exc)}


def collect_runtime_mode() -> dict[str, Any]:
    return {
        "execution_mode": execution_mode(),
        "platform": _platform_attachment(),
        "cutover": _cutover_status(),
        "phase": _phase_status(),
        "host": _host_status(),
    }


def collect_runtime_platform() -> dict[str, Any]:
    return {
        "execution_mode": execution_mode(),
        "attachment": _platform_attachment(),
        "cutover": _cutover_status(),
        "host": _host_status(),
    }


def collect_runtime_providers() -> dict[str, Any]:
    return {"providers": _providers(), "execution_mode": execution_mode()}


def collect_runtime_services() -> dict[str, Any]:
    return _services_and_databases()


def collect_runtime_models() -> dict[str, Any]:
    return _models()


def collect_runtime_gpu() -> dict[str, Any]:
    return _gpu_cpu_memory()


def collect_runtime_jobs() -> dict[str, Any]:
    return _jobs()


def collect_runtime_health() -> dict[str, Any]:
    return {
        "health": _health(),
        "phase": _phase_status(),
        "acceptance": _acceptance_summary(),
        "services": _services_and_databases(),
    }


def collect_runtime_status() -> dict[str, Any]:
    """Full live runtime snapshot."""
    return {
        "ok": True,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "identity": {
            "name": os.getenv("JARVIS_ASSISTANT_NAME", "Aria"),
            "version": "3.1.0",
            "install_path": str(PROJECT_ROOT),
        },
        "execution_mode": execution_mode(),
        "host": _host_status(),
        "platform": _platform_attachment(),
        "cutover": _cutover_status(),
        "phase": _phase_status(),
        "acceptance": _acceptance_summary(),
        "providers": _providers(),
        "services": _services_and_databases(),
        "models": _models(),
        "gpu": _gpu_cpu_memory(),
        "jobs": _jobs(),
        "workspace": _workspace_git(),
        "health": _health(),
    }


_COLLECTORS: dict[str, Any] = {
    "runtime_status": collect_runtime_status,
    "runtime_mode": collect_runtime_mode,
    "runtime_platform": collect_runtime_platform,
    "runtime_providers": collect_runtime_providers,
    "runtime_services": collect_runtime_services,
    "runtime_models": collect_runtime_models,
    "runtime_gpu": collect_runtime_gpu,
    "runtime_jobs": collect_runtime_jobs,
    "runtime_health": collect_runtime_health,
}


def collect_runtime(action: str) -> dict[str, Any]:
    fn = _COLLECTORS.get(action, collect_runtime_status)
    data = fn()
    return {"ok": True, "action": action, "data": data}


def format_runtime_markdown(action: str, data: dict[str, Any] | None = None) -> str:
    """Human-readable runtime report for chat responses."""
    payload = data if data is not None else _COLLECTORS.get(action, collect_runtime_status)()
    lines = ["## Aria Runtime Report", ""]

    if action in ("runtime_status", "runtime_mode", "runtime_platform"):
        mode = payload.get("execution_mode") or payload.get("platform", {}).get("execution_mode")
        if mode:
            lines.append(f"**Execution mode:** `{mode}`")
        host = payload.get("host") or {}
        if host:
            healthy = host.get("healthy")
            attached = host.get("attached")
            lines.append(f"**ApplicationHost:** attached={attached}, healthy={healthy}")
        plat = payload.get("platform") or payload.get("attachment") or {}
        layers = plat.get("layers") or {}
        if layers:
            attached_layers = [k for k, v in layers.items() if v]
            lines.append(f"**Platform layers attached:** {', '.join(attached_layers) or 'none'}")
        phase = payload.get("phase") or {}
        if phase.get("phase"):
            lines.append(
                f"**Workstation phase:** `{phase.get('phase')}` — {phase.get('detail', '')}"
            )

    if action in ("runtime_status", "runtime_health"):
        acc = payload.get("acceptance") or {}
        if acc and "overall" in acc:
            lines.append(
                f"**Acceptance:** {acc.get('overall')}% overall, "
                f"production readiness {acc.get('production_readiness')}%"
            )
        health = payload.get("health") or {}
        if health.get("ok") is not None:
            lines.append(f"**Health:** {'OK' if health.get('ok') else 'issues detected'}")

    if action in ("runtime_status", "runtime_models"):
        models = payload.get("models") or payload
        active = models.get("active") if isinstance(models, dict) else None
        if active:
            lines.append("**Models:**")
            for role, name in active.items():
                if name:
                    lines.append(f"- {role}: `{name}`")

    if action in ("runtime_status", "runtime_services"):
        svc = payload.get("services") or payload
        if isinstance(svc, dict) and svc.get("services"):
            running = [s.get("id") for s in svc["services"] if s.get("running")]
            lines.append(f"**Services running:** {', '.join(running) or 'none'}")
            dbs = svc.get("databases") or []
            if dbs:
                db_line = ", ".join(
                    f"{d.get('id')}={'up' if d.get('running') else 'down'}" for d in dbs
                )
                lines.append(f"**Databases:** {db_line}")

    if action in ("runtime_status", "runtime_providers"):
        prov = payload.get("providers") or payload.get("providers", {})
        if isinstance(prov, dict) and prov:
            lines.append("**Providers:**")
            for name, info in prov.items():
                if isinstance(info, dict):
                    src = info.get("source") or (
                        "platform" if info.get("platform_attached") else "local"
                    )
                    lines.append(f"- {name}: {src}")

    if action in ("runtime_status", "runtime_gpu"):
        gpu_block = payload.get("gpu") or payload
        env = gpu_block.get("environment") if isinstance(gpu_block, dict) else None
        gpu = (env or gpu_block or {}).get("gpu") if isinstance(env or gpu_block, dict) else {}
        if gpu:
            lines.append(
                f"**GPU:** {gpu.get('name', 'unknown')} ({gpu.get('vram_gb', '?')} GB VRAM)"
            )

    if action in ("runtime_status", "runtime_jobs"):
        jobs = payload.get("jobs") or payload
        if isinstance(jobs, dict):
            active = jobs.get("active_count") or jobs.get("busy_count") or 0
            lines.append(f"**Active background jobs:** {active}")

    if action == "runtime_status":
        ws = payload.get("workspace") or {}
        if ws.get("aria_branch"):
            lines.append(f"**Aria git branch:** `{ws['aria_branch']}`")
        if ws.get("current_project"):
            lines.append(f"**Current project:** {ws['current_project']}")

    if len(lines) <= 2:
        lines.append("_Live runtime data collected — see structured payload for details._")
    lines.append("")
    lines.append("_Source: live runtime introspection (no search, no RAG)._")
    return "\n".join(lines)


def runtime_action_result(action: str) -> dict[str, Any]:
    """Handler result shape for operations behavior."""
    data = _COLLECTORS.get(action, collect_runtime_status)()
    return {
        "ok": True,
        "message": format_runtime_markdown(action, data if action != "runtime_status" else data),
        "data": data,
    }


# Chat one-word status commands → runtime collectors (no RAG / web search).
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
    """Return runtime action name when message is a bare status command."""
    text = (message or "").strip().lower()
    if text.startswith("/"):
        text = text[1:].strip()
    return STATUS_COMMANDS.get(text)


def _memory_detail() -> dict[str, Any]:
    payload: dict[str, Any] = {"provider": "local"}
    if os.getenv("JARVIS_PLATFORM_MEMORY_ATTACHED") == "1":
        payload["provider"] = "platform"
    try:
        from jarvis.assistant_instance import get_assistant

        mem = get_assistant().memory
        entries = mem.list_entries() if hasattr(mem, "list_entries") else []
        payload["entry_count"] = len(entries)
        namespaces: dict[str, int] = {}
        for e in entries:
            ns = e.get("namespace") or "default"
            namespaces[ns] = namespaces.get(ns, 0) + 1
        payload["namespaces"] = namespaces
    except Exception as exc:
        payload["error"] = str(exc)
    try:
        idx = PROJECT_ROOT / "data" / "semantic-index" / "vectors.json"
        if idx.is_file():
            import json

            data = json.loads(idx.read_text(encoding="utf-8"))
            payload["semantic_vectors"] = len(data) if isinstance(data, list) else len(data.keys())
    except Exception:
        payload["semantic_vectors"] = None
    payload["semantic_attached"] = os.getenv("JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED") == "1"
    return payload


def _knowledge_detail() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "retrieval": "local",
        "platform_attached": os.getenv("JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED") == "1",
    }
    if payload["platform_attached"]:
        payload["retrieval"] = "platform"
    try:
        from jarvis.knowledge.registry import registry_snapshot

        snap = registry_snapshot()
        payload["documents"] = snap.get("total_documents")
        payload["sources"] = snap.get("sources") or []
        payload["last_sync"] = snap.get("last_sync") or ""
    except Exception as exc:
        payload["registry_error"] = str(exc)
    return payload


def _applications() -> list[dict[str, Any]]:
    apps: list[dict[str, Any]] = [
        {
            "id": "aria",
            "label": os.getenv("JARVIS_ASSISTANT_NAME", "Aria"),
            "attached": _host_status().get("attached"),
            "healthy": _host_status().get("healthy"),
            "primary": True,
        }
    ]
    try:
        from aiplatform.applications.host import all_hosts

        for host in all_hosts():
            if host.get("id") == "aria":
                continue
            apps.append(
                {
                    "id": host.get("id"),
                    "label": host.get("id"),
                    "attached": host.get("attached"),
                    "healthy": host.get("health"),
                    "primary": False,
                }
            )
    except Exception:
        pass
    return apps


def _recent_activity_summary(*, limit: int = 12) -> list[dict[str, Any]]:
    try:
        from jarvis.workstation_activity import list_events

        return list_events(limit=limit)
    except Exception:
        return []


def collect_dashboard() -> dict[str, Any]:
    """Structured payload for Mission Control UI (alias)."""
    from jarvis.mission_control import collect_mission_control

    return collect_mission_control()


def format_status_summary(data: dict[str, Any] | None = None) -> str:
    """Compact status for chat — sourced from Mission Control."""
    from jarvis.mission_control import format_overview_markdown

    return format_overview_markdown()


def format_startup_summary() -> dict[str, Any]:
    """Greeting + startup reassurance payload for overlay and first chat."""
    snap = collect_runtime_status()
    greeting = "Hello"
    try:
        from jarvis.morning_briefing import personalized_greeting

        greeting = personalized_greeting()
    except Exception:
        pass
    return {
        "ok": True,
        "greeting": greeting,
        "markdown": format_status_summary(snap).replace("## Workstation Status", f"## {greeting}"),
        "summary": format_status_summary(snap),
        "dashboard": collect_dashboard(),
    }
