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
    functional_verification: str = ""
    integration_ok: bool = False

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
    from jarvis.application.standalone.workstation_impl.registry import component

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
    env_configured = _env_any(*comp.config_keys) if comp.config_keys else True
    return {
        "installed": installed,
        "running": running,
        "healthy": running,
        "configured": env_configured or running,
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
    integration_ok = item.integration_ok if item.used_by_aria else True
    if item.healthy and item.configured and integration_ok:
        return AcceptanceStatus.READY.value
    return AcceptanceStatus.NEEDS_CONFIGURATION.value


def compute_score_gaps(
    items: list[AcceptanceItem],
    *,
    daily_ids: set[str],
    integration_ids: set[str],
) -> dict[str, Any]:
    """Explain why scores are below 100% and projected gain per fix."""
    daily_items = [i for i in items if i.id in daily_ids]
    integration_items = [i for i in items if i.id in integration_ids]

    def _weight(group: list[AcceptanceItem]) -> float:
        return 100.0 / len(group) if group else 0.0

    daily_w = _weight(daily_items)
    int_w = _weight(integration_items)

    gaps: list[dict[str, Any]] = []
    for item in daily_items:
        if item.status == AcceptanceStatus.READY.value and (
            not item.used_by_aria or item.integration_ok
        ):
            continue
        gain = daily_w if item.status == AcceptanceStatus.NOT_INSTALLED.value else daily_w * 0.5
        if item.used_by_aria and not item.integration_ok:
            gain = max(gain, int_w * 0.5)
        reason = item.fix_hint or item.functional_verification or item.detail or item.status
        human = any(
            x in (reason + item.functional_verification).lower()
            for x in ("login", "auth", "not logged", "api key")
        )
        gaps.append(
            {
                "id": item.id,
                "label": item.label,
                "missing": f"{item.label} — {reason[:100]}",
                "gain_daily": round(gain, 1),
                "gain_integration": round(int_w if not item.integration_ok else 0, 1),
                "fix": item.fix_hint or reason[:120],
                "human_required": human,
                "checked": False,
            }
        )

    for item in integration_items:
        if item.id in daily_ids or item.integration_ok:
            continue
        if item.status == AcceptanceStatus.NOT_INSTALLED.value:
            continue
        gaps.append(
            {
                "id": item.id,
                "label": item.label,
                "missing": f"{item.label} integration failed",
                "gain_daily": 0.0,
                "gain_integration": round(int_w, 1),
                "fix": item.fix_hint or item.functional_verification or "run workstation repair",
                "human_required": False,
                "checked": False,
            }
        )

    gaps.sort(key=lambda g: g["gain_daily"] + g["gain_integration"], reverse=True)
    daily_score = round(
        100.0 * sum(i.score_points for i in daily_items) / len(daily_items) if daily_items else 100,
        1,
    )
    projected = min(
        100.0,
        round(
            daily_score + sum(g["gain_daily"] for g in gaps if not g.get("human_required")),
            1,
        ),
    )
    return {
        "daily_score": daily_score,
        "projected_daily": projected,
        "gaps": gaps,
    }


def run_acceptance(*, persist: bool = True, live: bool = True) -> dict[str, Any]:
    """Run full workstation acceptance and compute score."""
    from jarvis.application.standalone.workstation_impl.integration_probes import (
        PROBE_MAP,
        run_probe,
    )

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
        if live and cid in PROBE_MAP and item.installed and item.healthy:
            probe_result = run_probe(cid)
            item.functional_verification = str(probe_result.get("detail") or "")[:200]
            item.integration_ok = bool(probe_result.get("ok"))
            item.verified = item.integration_ok
        elif item.installed and item.healthy:
            item.integration_ok = bool(raw.get("verified"))
            item.functional_verification = item.detail
        else:
            item.integration_ok = False
        item.status = _classify(item)
        items.append(item)

    daily_ids = {c[0] for c in _CATALOG if c[3]}
    daily_items = [i for i in items if i.id in daily_ids]
    optional_items = [i for i in items if i.id not in daily_ids]
    integration_items = [i for i in items if i.used_by_aria and i.id in PROBE_MAP]
    integration_ids = {i.id for i in integration_items}
    gap_analysis = compute_score_gaps(items, daily_ids=daily_ids, integration_ids=integration_ids)

    def _avg_score(group: list[AcceptanceItem]) -> float:
        if not group:
            return 100.0
        return round(100.0 * sum(i.score_points for i in group) / len(group), 1)

    def _integration_score(group: list[AcceptanceItem]) -> float:
        if not group:
            return 100.0
        ok = sum(1 for i in group if i.integration_ok)
        return round(100.0 * ok / len(group), 1)

    overall = _avg_score(items)
    daily_score = _avg_score(daily_items)
    integration_score = _integration_score(integration_items)
    hardware_score = 100.0
    try:
        from jarvis.application.standalone.workstation_impl.hardware_report import collect_hardware

        hw = collect_hardware(benchmark=False)
        if hw.get("gpus"):
            hardware_score = 85.0
        if hw.get("recommendations"):
            hardware_score = max(70.0, hardware_score - 5.0 * len(hw["recommendations"][:3]))
    except Exception:
        hardware_score = 0.0

    production_readiness = round(
        (daily_score * 0.45)
        + (integration_score * 0.35)
        + (overall * 0.1)
        + (hardware_score * 0.1),
        1,
    )
    ready = [i.id for i in items if i.status == AcceptanceStatus.READY.value]
    needs = [i.id for i in items if i.status == AcceptanceStatus.NEEDS_CONFIGURATION.value]
    missing = [i.id for i in items if i.status == AcceptanceStatus.NOT_INSTALLED.value]

    recommended_fixes = [
        {"id": i.id, "label": i.label, "fix": i.fix_hint or i.functional_verification}
        for i in items
        if i.status != AcceptanceStatus.READY.value and (i.fix_hint or i.functional_verification)
    ][:12]
    remaining_work = [
        {"id": i.id, "label": i.label, "status": i.status}
        for i in items
        if i.status != AcceptanceStatus.READY.value
    ]

    payload = {
        "ok": daily_score >= 100.0
        and integration_score >= 95.0
        and production_readiness >= 95.0
        and "aria" in ready
        and "ollama" in ready,
        "ts": time.time(),
        "verified_at": now,
        "score": {
            "overall": overall,
            "daily_required": daily_score,
            "optional": _avg_score(optional_items),
            "integration": integration_score,
            "production_readiness": production_readiness,
            "hardware_utilization": hardware_score,
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
        "daily_ready": daily_score >= 100.0,
        "acceptance_passed": daily_score >= 100.0
        and integration_score >= 95.0
        and production_readiness >= 95.0
        and "aria" in ready
        and "ollama" in ready,
        "remaining_work": remaining_work,
        "recommended_fixes": recommended_fixes,
        "known_issues": [f"{i['label']}: {i['status']}" for i in remaining_work[:8]],
        "gap_analysis": gap_analysis,
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
        f"**Integration score:** {scores.get('integration', 0)}%",
        f"**Production readiness:** {scores.get('production_readiness', 0)}%",
        f"**Passed:** {'YES' if data.get('acceptance_passed') else 'NO'}",
        "",
        f"Ready: **{summary.get('ready', 0)}** · "
        f"Needs configuration: **{summary.get('needs_configuration', 0)}** · "
        f"Not installed: **{summary.get('not_installed', 0)}**",
        "",
    ]
    gaps = data.get("gap_analysis") or {}
    if gaps.get("gaps") and not data.get("acceptance_passed"):
        lines.extend(
            [
                "### Why am I not at 100%?",
                "",
                f"**Daily score:** {gaps.get('daily_score', scores.get('daily_required', 0))}%",
                "",
                "**Missing:**",
            ]
        )
        for gap in gaps.get("gaps") or []:
            mark = "☐" if not gap.get("human_required") else "⚠"
            gain = gap.get("gain_daily") or gap.get("gain_integration") or 0
            lines.append(f"{mark} {gap.get('missing', gap.get('label'))} (+{gain:.0f}%)")
            if gap.get("fix"):
                lines.append(f"    fix: {gap['fix']}")
        lines.append("")
        lines.append(f"**Projected daily score:** {min(100, gaps.get('projected_daily', 0)):.0f}%")
        lines.append("")
    daily_ids = {c[0] for c in _CATALOG if c[3]}
    for item in data.get("items") or []:
        status = item.get("status", "")
        mark = "✓" if status == AcceptanceStatus.READY.value else "○"
        daily = " *" if item.get("id") in daily_ids else ""
        lines.append(f"{mark} **{item.get('label')}**{daily} — `{status}`")
        if item.get("version"):
            lines.append(f"    version: {item['version']}")
        if verbose and item.get("functional_verification"):
            lines.append(f"    verified: {item['functional_verification']}")
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
