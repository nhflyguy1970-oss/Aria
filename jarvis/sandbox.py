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


def run_sandboxed(
    cmd: Sequence[str],
    *,
    cwd: str | None = None,
    timeout: int = 30,
    network: bool = False,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        wrap_command(cmd, network=network),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )
