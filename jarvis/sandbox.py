"""Optional firejail sandbox for code execution."""

import os
import shutil
import subprocess
from typing import Sequence


def sandbox_enabled() -> bool:
    return os.getenv("JARVIS_SANDBOX", "firejail").lower() not in ("0", "false", "no", "off", "none")


def firejail_available() -> bool:
    return shutil.which("firejail") is not None


def wrap_command(cmd: Sequence[str], *, network: bool = False) -> list[str]:
    """Wrap command with firejail if enabled and available."""
    if not sandbox_enabled() or not firejail_available():
        return list(cmd)
    flags = ["firejail", "--private", "--seccomp"]
    if not network:
        flags.append("--net=none")
    flags.extend(["--", *cmd])
    return flags


def _pruned_env() -> dict[str, str]:
    """Firejail rejects oversized environments (MAX_ENVS >= 256). Keep essentials."""
    keep = {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TERM",
        "TMPDIR",
        "TMP",
        "TEMP",
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "PYTHONHOME",
        "JARVIS_SANDBOX",
        "DISPLAY",
        "XDG_RUNTIME_DIR",
        "XDG_DATA_HOME",
        "XDG_CONFIG_HOME",
    }
    env = {k: v for k, v in os.environ.items() if k in keep and v}
    if "PATH" not in env:
        env["PATH"] = "/usr/bin:/bin"
    return env


def run_sandboxed(
    cmd: Sequence[str],
    *,
    cwd: str | None = None,
    timeout: int = 30,
    network: bool = False,
) -> subprocess.CompletedProcess:
    # Always prune env when firejail wraps — parent shells often exceed MAX_ENVS.
    use_pruned = sandbox_enabled() and firejail_available()
    return subprocess.run(
        wrap_command(cmd, network=network),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
        env=_pruned_env() if use_pruned else None,
    )
