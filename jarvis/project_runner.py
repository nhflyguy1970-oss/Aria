"""Sandboxed project runner — venv-aware python/pytest in firejail or docker."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from jarvis.sandbox import firejail_available, run_sandboxed, sandbox_enabled

_PYTHON = sys.executable


def find_venv_python(base: Path) -> Path | None:
    """Locate project venv python (./venv, ./.venv)."""
    for name in ("venv", ".venv", "env"):
        candidate = base / name / "bin" / "python"
        if candidate.exists():
            return candidate
        candidate = base / name / "Scripts" / "python.exe"
        if candidate.exists():
            return candidate
    return None


def project_python(base: Path) -> str:
    venv_py = find_venv_python(base)
    return str(venv_py) if venv_py else _PYTHON


def docker_available() -> bool:
    return os.getenv("JARVIS_DOCKER", "").lower() in ("1", "true", "yes") and shutil.which("docker") is not None


def _docker_run(cmd: list[str], *, cwd: Path, timeout: int = 120, shell: bool = False) -> subprocess.CompletedProcess:
    mount = f"{cwd.resolve()}:/work"
    image = os.getenv("JARVIS_DOCKER_IMAGE", "python:3.12-slim")
    if shell:
        script = " ".join(cmd)
        full = ["docker", "run", "--rm", "-v", mount, "-w", "/work", image, "sh", "-c", script]
    else:
        full = ["docker", "run", "--rm", "-v", mount, "-w", "/work", image, *cmd]
    return subprocess.run(full, capture_output=True, text=True, timeout=timeout)


def run_script(path: Path, base: Path, *, timeout: int = 60, network: bool = False) -> subprocess.CompletedProcess:
    """Run a script with project venv + optional firejail/docker."""
    py = project_python(base)
    rel = path if path.is_absolute() else base / path
    cmd = [py, str(rel)]

    if docker_available():
        return _docker_run(["python", str(rel.relative_to(base))], cwd=base, timeout=timeout)

    return run_sandboxed(cmd, cwd=str(base), timeout=timeout, network=network)


def run_pytest(
    target: Path | str,
    base: Path,
    *,
    timeout: int = 120,
    extra_args: list[str] | None = None,
    sandbox: bool | None = None,
) -> subprocess.CompletedProcess:
    """Run pytest on target using project venv (unsandboxed by default — clearer output)."""
    py = project_python(base)
    args = extra_args or []
    target_path = Path(target)
    rel = str(target_path.relative_to(base)) if target_path.is_relative_to(base) else str(target_path)
    cmd = [py, "-m", "pytest", rel, *args]

    if docker_available():
        # Avoid shell=True: install pytest then run argv list inside container.
        return _docker_run(
            ["bash", "-lc", f"pip install -q pytest && python -m pytest {shlex.quote(rel)} -q --tb=short"],
            cwd=base,
            timeout=timeout,
            shell=False,
        )

    use_sandbox = sandbox
    if use_sandbox is None:
        use_sandbox = os.getenv("JARVIS_PYTEST_SANDBOX", "").lower() in ("1", "true", "yes")

    if use_sandbox:
        return run_sandboxed(cmd, cwd=str(base), timeout=timeout)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(base),
    )


def runner_info(base: Path) -> dict:
    venv = find_venv_python(base)
    return {
        "python": project_python(base),
        "venv": str(venv) if venv else None,
        "firejail": firejail_available() if sandbox_enabled() else False,
        "docker": docker_available(),
        "sandbox": sandbox_enabled(),
    }


_ALLOWED_CMD_PREFIXES = (
    "pytest", "python", "python3", "ruff", "mypy", "pyright",
    "npm test", "npm run", "node --check", "npx tsc",
    "cargo test", "cargo check", "go test", "go build",
)


def run_project_command(command: str, base: Path, *, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run an allowlisted project command (sandboxed when firejail enabled)."""
    cmd = command.strip()
    if not cmd:
        raise ValueError("Empty command")
    lower = cmd.lower()
    if not any(lower.startswith(p) for p in _ALLOWED_CMD_PREFIXES):
        raise ValueError(
            f"Command not allowed. Prefix must be one of: {', '.join(_ALLOWED_CMD_PREFIXES[:6])}…"
        )
    if any(ch in cmd for ch in (";", "|", "&", "`", "$(", "\n")):
        raise ValueError("Shell chaining is not allowed.")

    py = project_python(base)
    if lower.startswith("python ") or lower.startswith("python3 "):
        parts = cmd.split(maxsplit=1)
        rest = parts[1] if len(parts) > 1 else ""
        run_cmd = [py, *rest.split()]
    elif lower.startswith("pytest"):
        run_cmd = [py, "-m", "pytest", *cmd.split()[1:]]
    else:
        run_cmd = cmd.split()

    return run_sandboxed(run_cmd, cwd=str(base), timeout=timeout)
