"""Workstation inventory — single source of truth for installed components."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

_INVENTORY_CACHE = PROJECT_ROOT / "data" / "automation" / "inventory_last.json"


@dataclass
class InventoryRecord:
    id: str
    label: str
    category: str
    installed: bool
    version: str = ""
    running: bool = False
    healthy: bool = False
    configured: bool = False
    dependencies: list[str] = field(default_factory=list)
    data_location: str = ""
    container: str = ""
    gpu_usage_mb: float | None = None
    memory_usage_mb: float | None = None
    last_verified: str = ""
    update_available: bool | None = None
    detail: str = ""
    install_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _command_version(*cmd: str, timeout: float = 5.0) -> str:
    if not cmd or not shutil.which(cmd[0]):
        return ""
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            return ""
        line = (proc.stdout or proc.stderr or "").strip().splitlines()
        return line[0][:120] if line else ""
    except Exception:
        return ""


def _env_configured(*keys: str) -> bool:
    return any(os.getenv(k, "").strip() for k in keys)


def _docker_container_memory(container: str) -> float | None:
    if not container or not shutil.which("docker"):
        return None
    try:
        proc = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.MemUsage}}", container],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return None
        part = proc.stdout.strip().split("/")[0].strip()
        if part.endswith("GiB"):
            return float(part[:-3]) * 1024
        if part.endswith("MiB"):
            return float(part[:-3])
    except Exception:
        return None
    return None


def _tool_record(
    *,
    item_id: str,
    label: str,
    category: str,
    binary: str,
    version_cmd: tuple[str, ...] | None = None,
    install_hint: str = "",
    configured_keys: tuple[str, ...] = (),
    dependencies: list[str] | None = None,
) -> InventoryRecord:
    installed = bool(shutil.which(binary))
    version = _command_version(*(version_cmd or (binary, "--version")))
    return InventoryRecord(
        id=item_id,
        label=label,
        category=category,
        installed=installed,
        version=version,
        running=installed,
        healthy=installed,
        configured=_env_configured(*configured_keys) if configured_keys else installed,
        dependencies=dependencies or [],
        install_hint=install_hint,
        detail=version or ("missing" if not installed else "present"),
    )


def _catalog_tools() -> list[InventoryRecord]:
    return [
        _tool_record(
            item_id="git",
            label="Git",
            category="development",
            binary="git",
            install_hint="sudo apt install git",
        ),
        _tool_record(
            item_id="python3",
            label="Python",
            category="development",
            binary="python3",
            version_cmd=("python3", "--version"),
        ),
        _tool_record(
            item_id="uv",
            label="uv",
            category="development",
            binary="uv",
            install_hint="curl -LsSf https://astral.sh/uv/install.sh | sh",
        ),
        _tool_record(
            item_id="docker",
            label="Docker",
            category="development",
            binary="docker",
            install_hint="./scripts/install-docker.sh",
        ),
        _tool_record(
            item_id="ruff",
            label="Ruff",
            category="development",
            binary="ruff",
            install_hint="pip install ruff (or use venv)",
        ),
        _tool_record(
            item_id="pytest",
            label="Pytest",
            category="development",
            binary="pytest",
            install_hint="pip install pytest",
        ),
        _tool_record(
            item_id="tesseract",
            label="Tesseract OCR",
            category="knowledge",
            binary="tesseract",
            install_hint="sudo apt install tesseract-ocr",
        ),
        _tool_record(
            item_id="pdftotext",
            label="pdftotext",
            category="knowledge",
            binary="pdftotext",
            install_hint="sudo apt install poppler-utils",
        ),
        _tool_record(
            item_id="espeak_ng",
            label="espeak-ng",
            category="voice",
            binary="espeak-ng",
            install_hint="sudo apt install espeak-ng",
        ),
        _tool_record(
            item_id="opencode",
            label="OpenCode",
            category="coding",
            binary="opencode",
            install_hint="npm install -g opencode-ai (optional)",
        ),
        _tool_record(
            item_id="claude",
            label="Claude Code CLI",
            category="coding",
            binary="claude",
            install_hint="https://docs.anthropic.com/claude-code",
        ),
        _tool_record(
            item_id="aiplatform",
            label="AI-Platform",
            category="platform",
            binary="python3",
            install_hint="./workstation install (with AI-Platform sibling repo)",
        ),
    ]


def _venv_record() -> InventoryRecord:
    venv_py = PROJECT_ROOT / "venv" / "bin" / "python"
    installed = venv_py.is_file()
    version = ""
    if installed:
        version = _command_version(str(venv_py), "-c", "import sys; print(sys.version.split()[0])")
    return InventoryRecord(
        id="aria_venv",
        label="Aria Python venv",
        category="development",
        installed=installed,
        version=version,
        running=installed,
        healthy=installed,
        configured=installed,
        data_location=str(PROJECT_ROOT / "venv"),
        install_hint="./workstation install",
        detail="ready" if installed else "missing",
    )


def _registry_records() -> list[InventoryRecord]:
    from jarvis.workstation.registry import all_components

    records: list[InventoryRecord] = []
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for comp in all_components():
        running = comp.healthy()
        installed = running
        if comp.id == "ollama":
            installed = bool(shutil.which("ollama"))
            version = _command_version("ollama", "--version")
        elif comp.docker_container:
            installed = bool(shutil.which("docker"))
            version = comp.docker_container if _docker_running(comp.docker_container) else ""
        else:
            version = comp.status_detail()

        if comp.id == "aria":
            installed = (PROJECT_ROOT / "main.py").is_file()

        records.append(
            InventoryRecord(
                id=comp.id,
                label=comp.label,
                category=comp.category,
                installed=installed,
                version=str(version)[:120],
                running=running,
                healthy=running,
                configured=_env_configured(*comp.config_keys) if comp.config_keys else installed,
                dependencies=[],
                data_location=str(PROJECT_ROOT / "data") if comp.id == "aria" else "",
                container=comp.docker_container,
                memory_usage_mb=_docker_container_memory(comp.docker_container)
                if comp.docker_container
                else None,
                last_verified=now,
                detail=comp.status_detail(),
                install_hint=f"./workstation up {comp.id}" if comp.managed else "",
            )
        )
    return records


def _docker_running(container: str) -> bool:
    if not container or not shutil.which("docker"):
        return False
    try:
        proc = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", container],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return proc.returncode == 0 and proc.stdout.strip() == "true"
    except Exception:
        return False


def _aiplatform_installed() -> bool:
    try:
        import aiplatform  # noqa: F401

        return True
    except ImportError:
        return False


def collect_inventory(*, persist: bool = True) -> dict[str, Any]:
    """Collect full workstation inventory."""
    items: list[InventoryRecord] = []
    items.append(_venv_record())
    items.extend(_catalog_tools())
    items.extend(_registry_records())

    # Fix aiplatform record
    for rec in items:
        if rec.id == "aiplatform":
            rec.installed = _aiplatform_installed()
            rec.healthy = rec.installed
            rec.running = rec.installed
            rec.configured = bool(os.getenv("AI_ROOT", "").strip()) or _aiplatform_installed()
            rec.data_location = os.getenv("AI_ROOT", "")
            rec.detail = "importable" if rec.installed else "not installed"

    payload = {
        "ok": True,
        "ts": time.time(),
        "items": [r.to_dict() for r in items],
        "summary": _summarize(items),
    }
    if persist:
        _INVENTORY_CACHE.parent.mkdir(parents=True, exist_ok=True)
        _INVENTORY_CACHE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _summarize(items: list[InventoryRecord]) -> dict[str, Any]:
    required_ids = {"aria_venv", "ollama", "aria", "workstation"}
    required = [i for i in items if i.id in required_ids]
    missing_required = [i.id for i in required if not i.installed or not i.healthy]
    return {
        "total": len(items),
        "installed": sum(1 for i in items if i.installed),
        "running": sum(1 for i in items if i.running),
        "healthy": sum(1 for i in items if i.healthy),
        "missing_required": missing_required,
        "ready": not missing_required,
    }


def verify_inventory() -> dict[str, Any]:
    """Verify workstation from inventory — returns blockers with install hints."""
    inv = collect_inventory(persist=True)
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    for item in inv.get("items") or []:
        iid = str(item.get("id") or "")
        if iid in ("aria_venv", "ollama", "aria") and not item.get("healthy"):
            blockers.append(
                {
                    "id": iid,
                    "message": f"{item.get('label')} not ready",
                    "fix": str(item.get("install_hint") or "./workstation install"),
                }
            )
        elif iid == "git" and not item.get("installed"):
            blockers.append(
                {"id": iid, "message": "git not installed", "fix": "sudo apt install git"}
            )
        elif iid == "docker" and not item.get("installed"):
            warnings.append(
                {
                    "id": iid,
                    "message": "docker not installed (optional databases)",
                    "fix": "./scripts/install-docker.sh",
                }
            )

    env_file = PROJECT_ROOT / "data" / "jarvis.env"
    if not env_file.is_file():
        warnings.append(
            {
                "id": "jarvis.env",
                "message": "data/jarvis.env missing",
                "fix": "./workstation configure",
            }
        )

    ready = not blockers
    return {
        "ready": ready,
        "blockers": blockers,
        "warnings": warnings,
        "inventory": inv,
    }


def format_inventory_text(inv: dict[str, Any] | None = None) -> str:
    data = inv or collect_inventory(persist=False)
    lines = ["## Workstation Inventory", ""]
    summary = data.get("summary") or {}
    lines.append(
        f"**{summary.get('healthy', 0)}/{summary.get('total', 0)} healthy** · "
        f"ready: {'yes' if summary.get('ready') else 'no'}"
    )
    lines.append("")
    for item in data.get("items") or []:
        mark = "●" if item.get("healthy") else "○"
        inst = "installed" if item.get("installed") else "missing"
        ver = item.get("version") or ""
        ver_suffix = f" ({ver})" if ver else ""
        lines.append(
            f"{mark} **{item.get('label')}** [{item.get('category')}] — {inst}{ver_suffix}"
        )
        if not item.get("installed") and item.get("install_hint"):
            lines.append(f"    → {item['install_hint']}")
    return "\n".join(lines)


def last_inventory() -> dict[str, Any]:
    if not _INVENTORY_CACHE.is_file():
        return {"ok": False, "message": "no inventory run yet"}
    try:
        return json.loads(_INVENTORY_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "message": "corrupt inventory cache"}
