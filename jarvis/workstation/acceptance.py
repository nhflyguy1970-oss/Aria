"""Workstation acceptance — complete stack validation for Jeff's daily environment."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

_ACCEPTANCE_CACHE = PROJECT_ROOT / "data" / "automation" / "acceptance_last.json"


class AcceptanceStatus(StrEnum):
    READY = "READY"
    NEEDS_CONFIGURATION = "INSTALLED_BUT_NEEDS_CONFIGURATION"
    NOT_INSTALLED = "NOT_INSTALLED"


@dataclass
class AcceptanceItem:
    id: str
    label: str
    category: str
    status: str
    installed: bool
    configured: bool
    running: bool
    healthy: bool
    version: str = ""
    verified: bool = False
    used_by_aria: bool = False
    autostart_enabled: bool = False
    data_location: str = ""
    dependencies: list[str] = field(default_factory=list)
    detail: str = ""
    fix_hint: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def score_points(self) -> float:
        if self.status == AcceptanceStatus.READY.value:
            return 1.0
        if self.status == AcceptanceStatus.NEEDS_CONFIGURATION.value:
            return 0.5
        return 0.0


ProbeFn = Callable[[], dict[str, Any]]


def _http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _which_version(binary: str, *version_args: str) -> tuple[bool, str]:
    if not shutil.which(binary):
        return False, ""
    try:
        proc = subprocess.run(
            [binary, *version_args],
            capture_output=True,
            text=True,
            timeout=8,
        )
        line = (proc.stdout or proc.stderr or "").strip().splitlines()
        return proc.returncode == 0 or bool(line), (line[0][:120] if line else "")
    except Exception:
        return bool(shutil.which(binary)), ""


def _venv_python() -> str:
    py = PROJECT_ROOT / "venv" / "bin" / "python"
    return str(py) if py.is_file() else "python3"


def _probe_registry(component_id: str) -> dict[str, Any]:
    from jarvis.workstation.registry import component

    comp = component(component_id)
    if comp is None:
        return {"installed": False, "running": False, "healthy": False, "configured": False}
    running = comp.healthy()
    if component_id == "ollama":
        installed = bool(shutil.which("ollama"))
    elif comp.docker_container:
        installed = bool(shutil.which("docker"))
    elif component_id in ("workstation", "scheduler"):
        installed = True
    else:
        installed = running or bool(comp.status_detail())
    return {
        "installed": installed,
        "running": running,
        "healthy": running,
        "configured": _env_any(*comp.config_keys) if comp.config_keys else installed,
        "version": comp.status_detail(),
        "verified": running,
        "autostart_enabled": comp.autostart,
        "data_location": str(PROJECT_ROOT / "data") if component_id == "aria" else "",
        "detail": comp.status_detail(),
    }


def _env_any(*keys: str) -> bool:
    return any(os.getenv(k, "").strip() for k in keys)


def _probe_aria_api() -> dict[str, Any]:
    host = os.getenv("JARVIS_HOST", "127.0.0.1")
    if host in ("0.0.0.0", "::", "::0"):
        host = "127.0.0.1"
    port = os.getenv("JARVIS_PORT", "8765")
    url = f"http://{host}:{port}/api/health"
    ok = _http_ok(url)
    return {
        "installed": True,
        "running": ok,
        "healthy": ok,
        "configured": (PROJECT_ROOT / "data" / "jarvis.env").is_file(),
        "version": f"{host}:{port}",
        "verified": ok,
        "detail": "API healthy" if ok else "API not responding — run ./workstation start",
        "fix_hint": "./workstation start",
    }


def _probe_tool(tool_id: str) -> dict[str, Any]:
    from jarvis.tools.registry import get_tool

    tool = get_tool(tool_id)
    if tool is None:
        return {"installed": False, "verified": False}
    installed = bool(tool.binary and shutil.which(tool.binary))
    healthy = tool.available()
    return {
        "installed": installed,
        "running": installed,
        "healthy": healthy,
        "configured": installed,
        "version": tool.binary,
        "verified": healthy,
        "used_by_aria": True,
        "detail": tool.label,
        "fix_hint": f"Install {tool.binary} or see DEPENDENCIES.md",
    }


def _probe_python_pkg(import_name: str, label: str) -> dict[str, Any]:
    py = _venv_python()
    try:
        proc = subprocess.run(
            [py, "-c", f"import {import_name}; print(getattr({import_name}, '__version__', 'ok'))"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        ok = proc.returncode == 0
        ver = (proc.stdout or "").strip().splitlines()[-1] if ok else ""
        return {
            "installed": ok,
            "healthy": ok,
            "running": ok,
            "configured": ok,
            "version": ver[:80],
            "verified": ok,
            "detail": label,
            "fix_hint": f"{py} -m pip install {import_name.replace('.', '-')}",
        }
    except Exception as exc:
        return {"installed": False, "detail": str(exc)[:120]}


def _probe_piper() -> dict[str, Any]:
    from jarvis.config import piper_ready, piper_voice_label

    ready = piper_ready()
    return {
        "installed": ready or bool(shutil.which("piper")),
        "healthy": ready,
        "running": ready,
        "configured": ready,
        "verified": ready,
        "version": piper_voice_label(),
        "used_by_aria": True,
        "detail": "TTS ready" if ready else "Configure JARVIS_PIPER_MODEL",
        "fix_hint": "./scripts/install-dependencies.sh",
    }


def _probe_whisper() -> dict[str, Any]:
    model = os.getenv("JARVIS_WHISPER_MODEL", "base")
    py = _venv_python()
    try:
        proc = subprocess.run(
            [py, "-c", "import faster_whisper; print('ok')"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        ok = proc.returncode == 0
    except Exception:
        ok = False
    return {
        "installed": ok or bool(shutil.which("whisper")),
        "healthy": ok,
        "configured": bool(model),
        "verified": ok,
        "version": model,
        "used_by_aria": True,
        "detail": "faster-whisper importable" if ok else "Install faster-whisper",
        "fix_hint": "pip install faster-whisper",
    }


def _probe_platform() -> dict[str, Any]:
    try:
        import aiplatform  # noqa: F401

        ok = True
        ver = getattr(aiplatform, "__version__", "installed")
    except ImportError:
        ok = False
        ver = ""
    return {
        "installed": ok,
        "healthy": ok,
        "configured": bool(os.getenv("AI_ROOT", "").strip()) or ok,
        "verified": ok,
        "version": str(ver),
        "used_by_aria": True,
        "data_location": os.getenv("AI_ROOT", ""),
        "fix_hint": "./workstation install --developer",
    }


def _probe_compose() -> dict[str, Any]:
    ok = bool(shutil.which("docker")) and (shutil.which("docker-compose") or shutil.which("docker"))
    return {
        "installed": ok,
        "healthy": ok,
        "configured": ok,
        "verified": ok,
        "version": _which_version("docker", "compose", "version")[1],
        "fix_hint": "./scripts/install-docker.sh",
    }


def _which_probe(item_id: str, binary: str, *args: str) -> dict[str, Any]:
    installed, version = _which_version(binary, *args)
    return {
        "installed": installed,
        "healthy": installed,
        "running": installed,
        "configured": installed,
        "version": version,
        "verified": installed,
        "detail": version or binary,
        "fix_hint": f"sudo apt install {binary}" if not installed else "",
    }


def _probe_venv() -> dict[str, Any]:
    py = PROJECT_ROOT / "venv" / "bin" / "python"
    installed = py.is_file()
    version = ""
    if installed:
        _, version = _which_version(str(py), "-c", "import sys; print(sys.version.split()[0])")
    return {
        "installed": installed,
        "healthy": installed,
        "configured": installed,
        "verified": installed,
        "version": version,
        "data_location": str(PROJECT_ROOT / "venv"),
        "fix_hint": "./workstation install",
    }


def _probe_venv_pkg(pkg: str) -> dict[str, Any]:
    py = _venv_python()
    try:
        proc = subprocess.run(
            [py, "-m", pkg, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        ok = proc.returncode == 0
        ver = (proc.stdout or proc.stderr or "").strip().splitlines()[0] if ok else ""
    except Exception:
        ok = False
        ver = ""
    return {
        "installed": ok,
        "healthy": ok,
        "configured": ok,
        "verified": ok,
        "version": ver[:80],
        "fix_hint": f"{py} -m pip install {pkg}",
    }


# id, label, category, daily_required, used_by_aria, autostart, deps, probe
_CATALOG: list[tuple[str, str, str, bool, bool, bool, list[str], ProbeFn]] = [
    ("ollama", "Ollama", "ai_runtime", True, True, True, [], lambda: _probe_registry("ollama")),
    (
        "litellm",
        "LiteLLM",
        "ai_runtime",
        False,
        True,
        False,
        ["docker"],
        lambda: _probe_registry("litellm"),
    ),
    (
        "lmstudio",
        "LM Studio",
        "ai_runtime",
        False,
        False,
        False,
        [],
        lambda: _probe_registry("lmstudio"),
    ),
    ("aria", "Aria", "interfaces", True, True, True, ["ollama"], _probe_aria_api),
    (
        "open_webui",
        "Open WebUI",
        "interfaces",
        False,
        False,
        False,
        ["docker"],
        lambda: _probe_registry("open_webui"),
    ),
    ("opencode", "OpenCode", "coding", True, True, False, [], lambda: _probe_tool("opencode")),
    (
        "claude_code",
        "Claude Code CLI",
        "coding",
        True,
        True,
        False,
        [],
        lambda: _probe_tool("claude_code"),
    ),
    (
        "gemini_cli",
        "Gemini CLI",
        "coding",
        False,
        True,
        False,
        [],
        lambda: _probe_tool("gemini_cli"),
    ),
    ("goose", "Goose", "coding", False, True, False, [], lambda: _probe_tool("goose")),
    ("hermes", "Hermes", "coding", False, True, False, [], lambda: _probe_tool("hermes")),
    ("continue", "Continue", "coding", False, True, False, [], lambda: _probe_tool("continue")),
    ("openhands", "OpenHands", "coding", False, True, False, [], lambda: _probe_tool("openhands")),
    (
        "tesseract",
        "Tesseract",
        "knowledge",
        True,
        True,
        False,
        [],
        lambda: _which_probe("tesseract", "tesseract", "--version"),
    ),
    (
        "pdftotext",
        "pdftotext",
        "knowledge",
        True,
        True,
        False,
        [],
        lambda: _which_probe("pdftotext", "pdftotext", "-v"),
    ),
    ("searxng", "SearXNG", "knowledge", False, True, False, [], lambda: _probe_registry("searxng")),
    (
        "postgres",
        "PostgreSQL",
        "databases",
        False,
        True,
        False,
        ["docker"],
        lambda: _probe_registry("postgres"),
    ),
    (
        "redis",
        "Redis",
        "databases",
        False,
        True,
        False,
        ["docker"],
        lambda: _probe_registry("redis"),
    ),
    (
        "mongodb",
        "MongoDB",
        "databases",
        False,
        True,
        False,
        ["docker"],
        lambda: _probe_registry("mongodb"),
    ),
    (
        "qdrant",
        "Qdrant",
        "databases",
        False,
        True,
        False,
        ["docker"],
        lambda: _probe_registry("qdrant"),
    ),
    ("whisper", "Whisper", "voice", True, True, False, [], _probe_whisper),
    ("piper", "Piper TTS", "voice", True, True, False, [], _probe_piper),
    ("comfyui", "ComfyUI", "vision", False, True, False, [], lambda: _probe_registry("comfyui")),
    ("n8n", "n8n", "automation", False, True, False, ["docker"], lambda: _probe_registry("n8n")),
    (
        "prometheus",
        "Prometheus",
        "monitoring",
        False,
        True,
        False,
        ["docker"],
        lambda: _probe_registry("prometheus"),
    ),
    (
        "grafana",
        "Grafana",
        "monitoring",
        False,
        True,
        False,
        ["docker"],
        lambda: _probe_registry("grafana"),
    ),
    (
        "git",
        "Git",
        "development",
        True,
        False,
        False,
        [],
        lambda: _which_probe("git", "git", "--version"),
    ),
    ("python", "Python venv", "development", True, True, False, [], _probe_venv),
    (
        "uv",
        "uv",
        "development",
        False,
        False,
        False,
        [],
        lambda: _which_probe("uv", "uv", "--version"),
    ),
    (
        "docker",
        "Docker",
        "development",
        False,
        True,
        False,
        [],
        lambda: _which_probe("docker", "docker", "--version"),
    ),
    (
        "docker_compose",
        "Docker Compose",
        "development",
        False,
        True,
        False,
        ["docker"],
        _probe_compose,
    ),
    (
        "ruff",
        "Ruff",
        "development",
        True,
        True,
        False,
        [],
        lambda: _which_probe("ruff", "ruff", "--version"),
    ),
    ("pytest", "Pytest", "development", True, True, False, [], lambda: _probe_venv_pkg("pytest")),
    (
        "pytorch",
        "PyTorch",
        "training",
        False,
        True,
        False,
        [],
        lambda: _probe_python_pkg("torch", "PyTorch"),
    ),
    (
        "transformers",
        "Transformers",
        "training",
        False,
        False,
        False,
        [],
        lambda: _probe_python_pkg("transformers", "Transformers"),
    ),
    ("aiplatform", "AI-Platform", "platform", True, True, False, [], _probe_platform),
    (
        "scheduler",
        "Proactive Scheduler",
        "automation",
        True,
        True,
        True,
        ["aria"],
        lambda: _probe_registry("scheduler"),
    ),
    (
        "workstation",
        "Workstation Bootstrap",
        "automation",
        True,
        True,
        True,
        ["ollama", "aria"],
        lambda: _probe_registry("workstation"),
    ),
]


def _classify(item: AcceptanceItem) -> str:
    if not item.installed:
        return AcceptanceStatus.NOT_INSTALLED.value
    integration_ok = item.verified if item.used_by_aria else True
    if item.healthy and item.configured and integration_ok:
        return AcceptanceStatus.READY.value
    return AcceptanceStatus.NEEDS_CONFIGURATION.value


def run_acceptance(*, persist: bool = True) -> dict[str, Any]:
    """Run full workstation acceptance and compute score."""
    items: list[AcceptanceItem] = []
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for cid, label, category, daily, used, autostart, deps, probe in _CATALOG:
        raw = probe() or {}
        item = AcceptanceItem(
            id=cid,
            label=label,
            category=category,
            status="",
            installed=bool(raw.get("installed")),
            configured=bool(raw.get("configured")),
            running=bool(raw.get("running")),
            healthy=bool(raw.get("healthy")),
            version=str(raw.get("version") or "")[:120],
            verified=bool(raw.get("verified")),
            used_by_aria=bool(raw.get("used_by_aria", used)),
            autostart_enabled=bool(raw.get("autostart_enabled", autostart)),
            data_location=str(raw.get("data_location") or ""),
            dependencies=list(deps),
            detail=str(raw.get("detail") or ""),
            fix_hint=str(raw.get("fix_hint") or ""),
        )
        item.status = _classify(item)
        items.append(item)

    daily_ids = {c[0] for c in _CATALOG if c[3]}
    daily_items = [i for i in items if i.id in daily_ids]
    optional_items = [i for i in items if i.id not in daily_ids]

    def _avg_score(group: list[AcceptanceItem]) -> float:
        if not group:
            return 100.0
        return round(100.0 * sum(i.score_points for i in group) / len(group), 1)

    overall = _avg_score(items)
    daily_score = _avg_score(daily_items)
    ready = [i.id for i in items if i.status == AcceptanceStatus.READY.value]
    needs = [i.id for i in items if i.status == AcceptanceStatus.NEEDS_CONFIGURATION.value]
    missing = [i.id for i in items if i.status == AcceptanceStatus.NOT_INSTALLED.value]

    payload = {
        "ok": daily_score >= 80.0 and "aria" in ready and "ollama" in ready,
        "ts": time.time(),
        "verified_at": now,
        "score": {
            "overall": overall,
            "daily_required": daily_score,
            "optional": _avg_score(optional_items),
        },
        "summary": {
            "total": len(items),
            "ready": len(ready),
            "needs_configuration": len(needs),
            "not_installed": len(missing),
            "ready_ids": ready,
            "needs_ids": needs,
            "missing_ids": missing,
        },
        "items": [i.to_dict() for i in items],
        "daily_ready": daily_score >= 80.0,
        "acceptance_passed": daily_score >= 80.0 and "aria" in ready and "ollama" in ready,
    }
    if persist:
        _ACCEPTANCE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        _ACCEPTANCE_CACHE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def format_acceptance_markdown(
    report: dict[str, Any] | None = None, *, verbose: bool = False
) -> str:
    data = report or run_acceptance(persist=False)
    scores = data.get("score") or {}
    summary = data.get("summary") or {}
    lines = [
        "## Workstation Acceptance Report",
        "",
        f"**Overall score:** {scores.get('overall', 0)}%",
        f"**Daily-required score:** {scores.get('daily_required', 0)}%",
        f"**Passed:** {'YES' if data.get('acceptance_passed') else 'NO'}",
        "",
        f"Ready: **{summary.get('ready', 0)}** · "
        f"Needs configuration: **{summary.get('needs_configuration', 0)}** · "
        f"Not installed: **{summary.get('not_installed', 0)}**",
        "",
    ]
    daily_ids = {c[0] for c in _CATALOG if c[3]}
    for item in data.get("items") or []:
        status = item.get("status", "")
        mark = "✓" if status == AcceptanceStatus.READY.value else "○"
        daily = " *" if item.get("id") in daily_ids else ""
        lines.append(f"{mark} **{item.get('label')}**{daily} — `{status}`")
        if item.get("version"):
            lines.append(f"    version: {item['version']}")
        if verbose:
            lines.append(
                f"    installed={item.get('installed')} configured={item.get('configured')} "
                f"running={item.get('running')} healthy={item.get('healthy')} "
                f"verified={item.get('verified')} aria={item.get('used_by_aria')} "
                f"autostart={item.get('autostart_enabled')}"
            )
            if item.get("data_location"):
                lines.append(f"    data: {item['data_location']}")
            if item.get("dependencies"):
                lines.append(f"    deps: {', '.join(item['dependencies'])}")
        if status != AcceptanceStatus.READY.value and item.get("fix_hint"):
            lines.append(f"    fix: {item['fix_hint']}")
    lines.append("")
    lines.append("*Items marked * are required for daily use.")
    if not data.get("acceptance_passed"):
        lines.append("")
        lines.append(
            "**Next step:** Click **Start AI Workstation** (desktop icon) or run `./workstation start`."
        )
    return "\n".join(lines)


def last_acceptance() -> dict[str, Any]:
    if not _ACCEPTANCE_CACHE.is_file():
        return {"ok": False, "message": "no acceptance run yet"}
    try:
        return json.loads(_ACCEPTANCE_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "message": "corrupt acceptance cache"}
