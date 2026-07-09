"""Workstation repair — automatically fix common acceptance failures."""

from __future__ import annotations

import logging
import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

logger = logging.getLogger("jarvis.workstation.repair")

_HUMAN_REQUIRED = frozenset(
    {
        "claude_login",
        "gemini_auth",
        "api_keys",
    }
)


def _run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 300) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd or PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[:2000],
            "stderr": (proc.stderr or "")[:1000],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _ollama_model_names(limit: int = 12) -> list[str]:
    if not shutil.which("ollama"):
        return []
    proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=15)
    if proc.returncode != 0:
        return []
    names: list[str] = []
    for line in (proc.stdout or "").splitlines()[1:]:
        part = line.split()[0] if line.strip() else ""
        if part:
            names.append(part)
        if len(names) >= limit:
            break
    return names


def repair_litellm_routing() -> dict[str, Any]:
    """Rewrite LiteLLM config with real Ollama model names and restart container."""
    ai_root = Path(os.getenv("AI_ROOT", str(PROJECT_ROOT.parent)))
    cfg_path = ai_root / "compose" / "litellm" / "config.yaml"
    if not cfg_path.is_file():
        return {"ok": False, "detail": f"missing {cfg_path}"}

    models = _ollama_model_names()
    if not models:
        return {"ok": False, "detail": "no ollama models found"}

    preferred = os.getenv("JARVIS_GENERAL_MODEL", "").strip()
    default = preferred if preferred in models else ""
    if not default:
        for name in models:
            low = name.lower()
            if "embed" in low:
                continue
            if any(x in low for x in ("32b", "70b", "64k")):
                continue
            default = name
            break
    if not default:
        default = models[0]
    embed = next((m for m in models if "embed" in m.lower()), "")

    model_list: list[dict[str, Any]] = [
        {
            "model_name": "ollama",
            "litellm_params": {
                "model": f"ollama/{default}",
                "api_base": "http://host.docker.internal:11434",
            },
        },
        {
            "model_name": default.replace(":", "-"),
            "litellm_params": {
                "model": f"ollama/{default}",
                "api_base": "http://host.docker.internal:11434",
            },
        },
    ]
    for name in models[:8]:
        if name == default:
            continue
        model_list.append(
            {
                "model_name": name.replace(":", "-"),
                "litellm_params": {
                    "model": f"ollama/{name}",
                    "api_base": "http://host.docker.internal:11434",
                },
            }
        )
    if embed:
        model_list.append(
            {
                "model_name": "embeddings",
                "litellm_params": {
                    "model": f"ollama/{embed}",
                    "api_base": "http://host.docker.internal:11434",
                },
            }
        )

    content = {
        "model_list": model_list,
        "litellm_settings": {
            "drop_params": True,
            "set_verbose": False,
            "num_retries": 2,
        },
    }
    try:
        import yaml

        cfg_path.write_text(yaml.dump(content, default_flow_style=False, sort_keys=False))
    except Exception as exc:
        return {"ok": False, "detail": f"write failed: {exc}"}

    os.environ["JARVIS_PROBE_LITELLM_MODEL"] = "ollama"
    restart = _run(["docker", "restart", "ai-litellm"], timeout=60)
    import time

    time.sleep(10)
    return {
        "ok": restart.get("ok", False),
        "detail": f"default model ollama/{default}",
        "models": len(model_list),
        "restart": restart,
    }


def repair_permissions() -> dict[str, Any]:
    fixed: list[str] = []
    targets = [
        PROJECT_ROOT / "workstation",
        PROJECT_ROOT / "scripts" / "workstation-gui.sh",
        PROJECT_ROOT / "scripts" / "extend-workstation-compose.sh",
        PROJECT_ROOT / "scripts" / "launch-jarvis.sh",
        PROJECT_ROOT / "scripts" / "install-desktop-shortcuts.sh",
    ]
    for path in targets:
        if not path.is_file():
            continue
        mode = path.stat().st_mode
        if not (mode & stat.S_IXUSR):
            path.chmod(mode | stat.S_IXUSR)
            fixed.append(str(path.name))
    return {"ok": True, "fixed": fixed}


def repair_aria_service() -> dict[str, Any]:
    """Start Aria tray/server when the API is not responding."""
    try:
        from jarvis.application.desktop_launch import api_responsive, start_aria_server
    except ImportError as exc:
        return {"ok": False, "detail": str(exc)}

    if api_responsive(timeout=2):
        return {"ok": True, "detail": "already responsive"}
    started = start_aria_server()
    for _ in range(45):
        if api_responsive(timeout=2):
            return {"ok": True, "detail": "started", "started": started}
        import time

        time.sleep(1)
    return {"ok": False, "detail": "Aria API not responsive after start", "started": started}


def repair_desktop_shortcuts() -> dict[str, Any]:
    script = PROJECT_ROOT / "scripts" / "install-desktop-shortcuts.sh"
    global_script = PROJECT_ROOT / "scripts" / "install-global-commands.sh"
    if not script.is_file():
        return {"ok": False, "detail": "install-desktop-shortcuts.sh missing"}
    result = _run(["bash", str(script)])
    if global_script.is_file():
        global_result = _run(["bash", str(global_script)])
        result["global_commands"] = global_result
        result["ok"] = bool(result.get("ok")) and bool(global_result.get("ok"))
    return result


def repair_docker_services() -> dict[str, Any]:
    from jarvis.application.standalone.workstation_impl.startup import bootstrap_workstation

    return bootstrap_workstation(wait_timeout=90.0)


def repair_local_config() -> dict[str, Any]:
    from jarvis.application.standalone.workstation_impl.local_config import apply_local_defaults

    return apply_local_defaults()


def repair_compose_extension() -> dict[str, Any]:
    script = PROJECT_ROOT / "scripts" / "extend-workstation-compose.sh"
    if not script.is_file():
        return {"ok": False, "detail": "extend script missing"}
    return _run(["bash", str(script)])


def repair_python_deps() -> dict[str, Any]:
    py = PROJECT_ROOT / "venv" / "bin" / "pip"
    if not py.is_file():
        return {"ok": False, "detail": "venv pip missing"}
    return _run(
        [str(py), "install", "-q", "redis", "psycopg2-binary", "pymongo", "pyyaml"],
        timeout=180,
    )


def repair_acceptance_failures(report: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Map acceptance failures to targeted repair actions."""
    from jarvis.application.standalone.workstation_impl.acceptance import (
        last_acceptance,
        run_acceptance,
    )

    data = report or last_acceptance()
    if not data.get("items"):
        data = run_acceptance(persist=False, live=False)

    actions: list[dict[str, Any]] = []
    for item in data.get("items") or []:
        cid = item.get("id", "")
        if item.get("status") == "READY" and item.get("integration_ok", True):
            continue
        detail = (item.get("functional_verification") or item.get("detail") or "").lower()
        if cid == "litellm" or "invalid model" in detail or "litellm" in detail:
            actions.append({"id": cid, "action": "litellm_routing", "fn": repair_litellm_routing})
        elif cid in ("postgres", "redis", "qdrant", "n8n", "open_webui", "mongodb"):
            actions.append({"id": cid, "action": "docker_services", "fn": repair_docker_services})
        elif cid == "claude_code" and "login" in detail:
            actions.append(
                {
                    "id": cid,
                    "action": "human_required",
                    "detail": "Run: claude login",
                    "human": True,
                }
            )
        elif cid == "gemini_cli" and ("auth" in detail or "login" in detail):
            actions.append(
                {
                    "id": cid,
                    "action": "human_required",
                    "detail": "Run: gemini auth login",
                    "human": True,
                }
            )
        elif cid == "aria":
            actions.append({"id": cid, "action": "aria_service", "fn": repair_aria_service})
    return actions


def run_repair(*, rerun_acceptance: bool = True) -> dict[str, Any]:
    """Execute safe automatic repairs and optionally rerun acceptance."""
    try:
        from jarvis.application.standalone.workstation_impl.phase import (
            WorkstationPhase,
            set_phase,
        )

        set_phase(WorkstationPhase.RECOVERING, detail="repair in progress")
    except ImportError:
        pass

    steps: dict[str, Any] = {
        "permissions": repair_permissions(),
        "local_config": repair_local_config(),
        "compose": repair_compose_extension(),
        "python_deps": repair_python_deps(),
        "litellm": repair_litellm_routing(),
        "docker": repair_docker_services(),
        "aria": repair_aria_service(),
        "shortcuts": repair_desktop_shortcuts(),
    }

    human: list[str] = []
    for action in repair_acceptance_failures():
        if action.get("human"):
            human.append(action.get("detail") or action.get("action", ""))
            continue
        fn = action.get("fn")
        if callable(fn) and action.get("action") not in steps:
            steps[action["action"]] = fn()

    acceptance: dict[str, Any] | None = None
    if rerun_acceptance:
        from jarvis.application.standalone.workstation_impl.acceptance import run_acceptance

        acceptance = run_acceptance(persist=True)

    scores = (acceptance or {}).get("score") or {}
    ok = bool(
        acceptance and scores.get("daily_required", 0) >= 95 and scores.get("integration", 0) >= 90
    )
    try:
        from jarvis.application.standalone.workstation_impl.phase import mark_degraded, mark_ready

        if ok:
            mark_ready(detail="repair complete")
        else:
            mark_degraded(detail="repair finished with acceptance gaps")
    except ImportError:
        pass
    return {
        "ok": ok,
        "steps": steps,
        "human_required": human,
        "acceptance": acceptance,
    }


def format_repair_markdown(result: dict[str, Any]) -> str:
    lines = ["## Workstation Repair", ""]
    for name, step in (result.get("steps") or {}).items():
        mark = "✓" if step.get("ok") else "○"
        detail = step.get("detail") or step.get("stderr") or step.get("stdout") or ""
        lines.append(f"{mark} **{name}** — {str(detail)[:120]}")
    if result.get("human_required"):
        lines.append("")
        lines.append("**Human action required:**")
        for item in result["human_required"]:
            lines.append(f"- {item}")
    acc = result.get("acceptance") or {}
    scores = acc.get("score") or {}
    if scores:
        lines.append("")
        lines.append(
            f"After repair — daily: **{scores.get('daily_required', 0)}%**, "
            f"integration: **{scores.get('integration', 0)}%**, "
            f"production: **{scores.get('production_readiness', 0)}%**"
        )
    return "\n".join(lines)
