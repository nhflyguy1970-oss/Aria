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
        r"\bhow much (?:ram|memory|vram)\b|"
        r"\b(?:ram|vram|disk|storage)\b.*\b(?:available|free|using)\b|"
        r"\bruntime[_ ](?:status|health|mode|providers?|services?|models?|jobs?|gpu|platform|report)\b",
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
            r"\b(?:full status|runtime report|system report|diagnostics?|full runtime)\b",
            re.I,
        ),
        "runtime_report",
    ),
    (
        re.compile(
            r"\b(?:execution |runtime )?mode\b|standalone|attached|platform[- ]?authoritative|compatibility\b",
            re.I,
        ),
        "runtime_mode",
    ),
    (
        re.compile(r"\bwhat needs attention\b|\bneeds attention\b|\battention\b", re.I),
        "runtime_attention",
    ),
    (re.compile(r"\bhealth\b", re.I), "runtime_health"),
    (re.compile(r"\bproviders?\b", re.I), "runtime_providers"),
    (
        re.compile(r"\bdatabases?\b|postgres|mongodb|mongo\b|redis\b|qdrant\b", re.I),
        "runtime_databases",
    ),
    (re.compile(r"\bservices?\b", re.I), "runtime_services"),
    (re.compile(r"\bmodels?\b|ollama|litellm\b", re.I), "runtime_models"),
    (
        re.compile(r"\b(?:how much )?ram\b|\bsystem memory\b|\bavailable memory\b", re.I),
        "runtime_ram",
    ),
    (re.compile(r"\b(?:disk|storage)\b", re.I), "runtime_storage"),
    (re.compile(r"\bnetwork\b", re.I), "runtime_network"),
    (re.compile(r"\bgpu\b|vram\b|graphics\b|hardware\b|\bcpu\b", re.I), "runtime_gpu"),
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
        "runtime_report": "runtime_report",
        "runtime_mode": "runtime_mode",
        "runtime_health": "runtime_health",
        "runtime_platform": "runtime_platform",
        "runtime_services": "runtime_services",
        "runtime_databases": "runtime_databases",
        "runtime_models": "runtime_models",
        "runtime_gpu": "runtime_gpu",
        "runtime_ram": "runtime_ram",
        "runtime_storage": "runtime_storage",
        "runtime_network": "runtime_network",
        "runtime_jobs": "runtime_jobs",
        "runtime_providers": "runtime_providers",
        "runtime_applications": "runtime_applications",
        "runtime_attention": "runtime_attention",
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
        "platform_status": ov.get("platform_status"),
        "services": {
            "ready": mc.get("services_ready"),
            "services": mc.get("services") or [],
            "databases": mc.get("databases") or [],
        },
        "databases": mc.get("databases") or [],
        "models": mc.get("inference") or {},
        "inference": mc.get("inference") or {},
        "current_model": ov.get("current_model"),
        "provider": ov.get("inference_provider"),
        "gpu": {
            "name": ov.get("gpu") or (mc.get("hardware") or {}).get("gpu_name"),
            "vram_mb": ov.get("vram_mb") or (mc.get("hardware") or {}).get("vram_mb"),
            "free_vram_mb": ov.get("free_vram_mb")
            or (mc.get("hardware") or {}).get("free_vram_mb"),
        },
        "hardware": mc.get("hardware") or {},
        "ram_available_gb": ov.get("ram_available_gb")
        or (mc.get("hardware") or {}).get("ram_available_gb"),
        "jobs": mc.get("jobs") or {},
        "active_jobs": ov.get("active_jobs"),
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


def collect_runtime_databases() -> dict[str, Any]:
    return collect_runtime_services()


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
        "profile": ov.get("profile") or inf.get("profile"),
        "device": inf.get("device") or inf.get("placement"),
        "context_length": inf.get("context_length") or inf.get("num_ctx"),
        "inference": inf,
        "overview": ov,
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


def collect_runtime_ram() -> dict[str, Any]:
    return collect_runtime_gpu()


def collect_runtime_storage() -> dict[str, Any]:
    """Enumerate host storage devices (lsblk/df) plus Mission Control disk free if present."""
    import shutil
    import subprocess

    devices: list[dict[str, Any]] = []
    try:
        proc = subprocess.run(
            [
                "lsblk",
                "-b",
                "-J",
                "-o",
                "NAME,TYPE,SIZE,FSTYPE,MOUNTPOINT,TRAN,ROTA,MODEL,HOTPLUG,RM",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        payload = {}
        if proc.returncode == 0 and (proc.stdout or "").strip():
            import json

            payload = json.loads(proc.stdout)
        for block in payload.get("blockdevices") or []:
            _append_storage_device(devices, block, parent_tran="")
    except Exception:
        devices = []

    mounts: list[dict[str, Any]] = []
    try:
        proc = subprocess.run(
            [
                "df",
                "-B1",
                "--output=source,fstype,size,used,avail,target",
                "-x",
                "tmpfs",
                "-x",
                "devtmpfs",
            ],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        lines = (proc.stdout or "").splitlines()
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 6:
                continue
            source, fstype, size_s, used_s, avail_s, target = (
                parts[0],
                parts[1],
                parts[2],
                parts[3],
                parts[4],
                parts[5],
            )
            if source.startswith("overlay") or target.startswith("/snap"):
                continue
            try:
                size_b, used_b, avail_b = int(size_s), int(used_s), int(avail_s)
            except ValueError:
                continue
            mounts.append(
                {
                    "source": source,
                    "filesystem": fstype,
                    "mount_point": target,
                    "total_bytes": size_b,
                    "used_bytes": used_b,
                    "free_bytes": avail_b,
                    "total_gb": round(size_b / (1024**3), 1),
                    "used_gb": round(used_b / (1024**3), 1),
                    "free_gb": round(avail_b / (1024**3), 1),
                }
            )
    except Exception:
        mounts = []

    root_free_gb = None
    root_total_gb = None
    try:
        usage = shutil.disk_usage("/")
        root_free_gb = round(usage.free / (1024**3), 1)
        root_total_gb = round(usage.total / (1024**3), 1)
    except Exception:
        pass

    mc_hw: dict[str, Any] = {}
    try:
        mc = _mc_snapshot(required=False) or {}
        mc_hw = mc.get("hardware") if isinstance(mc.get("hardware"), dict) else {}
    except Exception:
        mc_hw = {}

    return {
        "ok": True,
        "source": "host_storage",
        "devices": devices,
        "mounts": mounts,
        "root_filesystem": {
            "mount_point": "/",
            "free_gb": root_free_gb,
            "total_gb": root_total_gb,
            "scope": "root filesystem",
        },
        "disk_free_gb": root_free_gb,
        "hardware": mc_hw,
    }


def _storage_device_type(block: dict[str, Any], *, parent_tran: str = "") -> str:
    tran = str(block.get("tran") or parent_tran or "").lower()
    rota = block.get("rota")
    name = str(block.get("name") or "").lower()
    hotplug = bool(block.get("hotplug") or block.get("rm"))
    if tran == "nvme" or name.startswith("nvme"):
        return "NVMe"
    if tran == "usb" or hotplug:
        return "USB"
    if rota in (1, True, "1"):
        return "HDD"
    if rota in (0, False, "0"):
        if tran in ("sata", "ata", "sas"):
            return "SATA SSD"
        return "SSD"
    if tran in ("sata", "ata", "sas"):
        return "SATA"
    return tran.upper() if tran else "disk"


def _append_storage_device(
    out: list[dict[str, Any]], block: dict[str, Any], *, parent_tran: str
) -> None:
    name = str(block.get("name") or "").strip()
    if not name or name.startswith(("loop", "zram", "sr")):
        return
    dtype = str(block.get("type") or "")
    tran = str(block.get("tran") or parent_tran or "")
    size_b = block.get("size")
    try:
        size_b_i = int(size_b) if size_b is not None else None
    except (TypeError, ValueError):
        size_b_i = None
    mount = block.get("mountpoint") or None
    fstype = block.get("fstype") or None
    model = (block.get("model") or "").strip() or None
    if dtype == "disk" or (dtype in ("part", "lvm") and (mount or fstype)):
        entry = {
            "name": name,
            "path": f"/dev/{name}",
            "device_type": _storage_device_type(block, parent_tran=tran),
            "kind": dtype,
            "mount_point": mount,
            "filesystem": fstype,
            "model": model,
            "total_bytes": size_b_i,
            "total_gb": round(size_b_i / (1024**3), 1) if size_b_i else None,
        }
        # Prefer leaf mounts; disks without mount still listed for inventory.
        if dtype == "disk" or mount or fstype:
            out.append(entry)
    for child in block.get("children") or []:
        _append_storage_device(out, child, parent_tran=tran)


def collect_runtime_network() -> dict[str, Any]:
    return collect_runtime_gpu()


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
        "overview": ov,
    }


def collect_runtime_attention() -> dict[str, Any]:
    return collect_runtime_health()


def collect_runtime_report() -> dict[str, Any]:
    return collect_runtime_status()


_COLLECTORS: dict[str, Any] = {
    "runtime_status": collect_runtime_status,
    "runtime_report": collect_runtime_report,
    "runtime_mode": collect_runtime_mode,
    "runtime_platform": collect_runtime_platform,
    "runtime_applications": collect_runtime_applications,
    "runtime_providers": collect_runtime_providers,
    "runtime_services": collect_runtime_services,
    "runtime_databases": collect_runtime_databases,
    "runtime_models": collect_runtime_models,
    "runtime_gpu": collect_runtime_gpu,
    "runtime_ram": collect_runtime_ram,
    "runtime_storage": collect_runtime_storage,
    "runtime_network": collect_runtime_network,
    "runtime_jobs": collect_runtime_jobs,
    "runtime_health": collect_runtime_health,
    "runtime_attention": collect_runtime_attention,
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

    from jarvis.runtime_formatters import format_runtime_intent

    body = format_runtime_intent(action, payload if isinstance(payload, dict) else {})
    return body.rstrip() + "\n\n_Source: AI Platform Mission Control (live)._"


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
    "databases": "runtime_databases",
    "models": "runtime_models",
    "memory": "runtime_providers",
    "ram": "runtime_ram",
    "providers": "runtime_providers",
    "gpu": "runtime_gpu",
    "jobs": "runtime_jobs",
    "attention": "runtime_attention",
}


def is_status_command(message: str) -> str | None:
    text = (message or "").strip().lower()
    if text.startswith("/"):
        text = text[1:].strip()
    if text in STATUS_COMMANDS:
        return STATUS_COMMANDS[text]
    literal = {
        "runtime_status": "runtime_status",
        "runtime_report": "runtime_report",
        "runtime_mode": "runtime_mode",
        "runtime_health": "runtime_health",
        "runtime_platform": "runtime_platform",
        "runtime_services": "runtime_services",
        "runtime_databases": "runtime_databases",
        "runtime_models": "runtime_models",
        "runtime_gpu": "runtime_gpu",
        "runtime_ram": "runtime_ram",
        "runtime_storage": "runtime_storage",
        "runtime_network": "runtime_network",
        "runtime_jobs": "runtime_jobs",
        "runtime_providers": "runtime_providers",
        "runtime_applications": "runtime_applications",
        "runtime_attention": "runtime_attention",
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
