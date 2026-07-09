"""First-run workstation setup — install, configure, bootstrap, verify."""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

from jarvis.env_loader import PROJECT_ROOT


def _run(cmd: list[str], *, timeout: int = 600) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
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


def install_optional_clis() -> list[dict[str, Any]]:
    """Install coding CLIs Jeff uses when npm is available."""
    results: list[dict[str, Any]] = []
    if not shutil.which("npm"):
        return [{"tool": "npm", "ok": False, "detail": "npm missing"}]

    packages = [
        ("gemini_cli", "@google/gemini-cli"),
    ]
    for tool_id, package in packages:
        binary = {"gemini_cli": "gemini"}.get(tool_id, tool_id)
        if shutil.which(binary):
            results.append({"tool": tool_id, "ok": True, "detail": "already installed"})
            continue
        res = _run(["npm", "install", "-g", package], timeout=300)
        results.append(
            {
                "tool": tool_id,
                "ok": res.get("ok", False) or bool(shutil.which(binary)),
                "detail": res.get("stderr") or res.get("stdout") or res.get("error", ""),
            }
        )
    return results


def run_first_run_setup(*, pull_models: bool = True) -> dict[str, Any]:
    """End-to-end first-run: configure, CLIs, compose, bootstrap, acceptance."""
    from jarvis.application.standalone.workstation_impl.local_config import apply_local_defaults
    from jarvis.application.standalone.workstation_impl.startup import bootstrap_workstation

    steps: dict[str, Any] = {}
    steps["configure"] = apply_local_defaults()

    py = PROJECT_ROOT / "venv" / "bin" / "python"
    if py.is_file():
        steps["platform_init"] = _run([str(py), "-m", "aiplatform.cli", "init"])
        steps["compose_extend"] = _run(["bash", "scripts/extend-workstation-compose.sh"])

    steps["optional_clis"] = install_optional_clis()

    if pull_models and os.getenv("JARVIS_FIRST_RUN_MODELS", "1") != "0":
        try:
            from jarvis.first_run_models import ensure_optional_models

            ensure_optional_models()
            steps["models"] = {"ok": True}
        except Exception as exc:
            steps["models"] = {"ok": False, "error": str(exc)}

    steps["bootstrap"] = bootstrap_workstation()
    from jarvis.application.standalone.workstation_impl.acceptance import run_acceptance

    steps["acceptance"] = run_acceptance()
    return {
        "ok": bool(steps["acceptance"].get("acceptance_passed")),
        "steps": steps,
    }
