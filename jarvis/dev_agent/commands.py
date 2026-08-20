"""Development command policy — classification and bounded execution.

Commands are matched against an allowlist by argv[0] plus a subcommand, not by
scanning a shell string: an autonomous agent must not be able to smuggle
`rm -rf` through a pipe or `;`. Anything not explicitly allowed is denied, and
high-impact git operations are denied outright even though git itself is
allowed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from typing import Any

from jarvis.dev_agent.workspace import Workspace

READ_ONLY = "read_only"
DEVELOPMENT = "development"
HIGH_IMPACT = "high_impact"

# argv[0] -> (impact, allowed subcommands or None for any)
POLICY: dict[str, tuple[str, tuple[str, ...] | None]] = {
    "git": (READ_ONLY, ("status", "diff", "log", "branch", "show", "rev-parse", "ls-files")),
    "ls": (READ_ONLY, None),
    "cat": (READ_ONLY, None),
    "pytest": (DEVELOPMENT, None),
    "python": (DEVELOPMENT, None),
    "python3": (DEVELOPMENT, None),
    "ruff": (DEVELOPMENT, None),
    "mypy": (DEVELOPMENT, None),
    "black": (DEVELOPMENT, None),
    "make": (DEVELOPMENT, None),
    "npm": (DEVELOPMENT, ("test", "run", "ci")),
}

# git subcommands the autonomous agent may run as development work.
GIT_DEVELOPMENT = ("add", "commit", "checkout", "switch", "restore", "stash")

# Never available autonomously, whatever else is configured.
FORBIDDEN_BINARIES = (
    "rm",
    "rmdir",
    "mv",
    "dd",
    "mkfs",
    "shutdown",
    "reboot",
    "systemctl",
    "sudo",
    "su",
    "chown",
    "chmod",
    "kill",
    "pkill",
    "killall",
    "curl",
    "wget",
    "ssh",
    "scp",
    "nc",
    "apt",
    "apt-get",
    "pip",
    "pip3",
    "docker",
    "sh",
    "bash",
    "zsh",
    "eval",
    "env",
)
FORBIDDEN_GIT = ("push", "reset", "clean", "rebase", "filter-branch", "gc", "prune", "remote")

# The interpreter is allowed so the agent can run tests and project scripts.
# Left unrestricted it also reinstates every forbidden binary: `python -c` runs
# arbitrary code, and `python -m pip install` walks straight past the pip ban.
# So inline code is refused, and -m is limited to development tooling.
PY_ALLOWED_MODULES = (
    "pytest",
    "unittest",
    "ruff",
    "mypy",
    "black",
    "compileall",
    "doctest",
    "json.tool",
    "venv",
)

LIMITS = {
    "timeout_s": 300,
    "max_output_chars": 40000,
    "max_commands_per_task": 200,
}


class CommandDenied(PermissionError):
    """The command is not permitted for the autonomous coding agent."""


def classify(argv: list[str]) -> str:
    if not argv:
        raise CommandDenied("Empty command")
    binary = argv[0]
    if binary in FORBIDDEN_BINARIES:
        raise CommandDenied(f"Command not permitted: {binary!r}")
    spec = POLICY.get(binary)
    if not spec:
        raise CommandDenied(f"Command not on the development allowlist: {binary!r}")
    impact, allowed_sub = spec
    sub = argv[1] if len(argv) > 1 else ""

    if binary == "git":
        if sub in FORBIDDEN_GIT:
            raise CommandDenied(f"git {sub} is a high-impact operation and is denied")
        if any(a in ("--force", "-f", "--hard") for a in argv):
            raise CommandDenied("Forced/destructive git flags are denied")
        if sub in GIT_DEVELOPMENT:
            return DEVELOPMENT
        if allowed_sub and sub not in allowed_sub:
            raise CommandDenied(f"git {sub!r} is not permitted")
        return READ_ONLY

    if binary in ("python", "python3"):
        _check_python(argv)

    if allowed_sub and sub and sub not in allowed_sub:
        raise CommandDenied(f"{binary} {sub!r} is not permitted")
    return impact


def _check_python(argv: list[str]) -> None:
    """Keep the interpreter from becoming a way around every other rule."""
    args = argv[1:]
    if not args:
        raise CommandDenied("An interactive interpreter is not permitted")
    first = args[0]
    if first in ("-c", "--command"):
        raise CommandDenied("python -c runs arbitrary code and is denied")
    if first == "-m":
        module = args[1] if len(args) > 1 else ""
        if module not in PY_ALLOWED_MODULES:
            raise CommandDenied(f"python -m {module!r} is not on the development allowlist")
        return
    if first.startswith("-"):
        raise CommandDenied(f"python {first!r} is not permitted")
    if not first.endswith(".py"):
        raise CommandDenied(f"python may only run a .py file from the workspace, not {first!r}")


# Python tooling is frequently absent from PATH while importable, so it is run
# as a module rather than a binary. Without this the agent reports "tests did
# not pass" when the truth is that the runner was never found.
PY_MODULE_TOOLS = {"pytest": "pytest", "ruff": "ruff", "mypy": "mypy", "black": "black"}


def resolve_argv(argv: list[str]) -> list[str]:
    """Make a permitted command runnable regardless of PATH."""
    if not argv:
        return argv
    binary = argv[0]
    if shutil.which(binary):
        return argv
    module = PY_MODULE_TOOLS.get(binary)
    if module:
        return [sys.executable, "-m", module, *argv[1:]]
    if binary in ("python", "python3"):
        return [sys.executable, *argv[1:]]
    return argv


def run(
    argv: list[str],
    ws: Workspace,
    *,
    timeout_s: int | None = None,
    cancel_check=None,
) -> dict[str, Any]:
    """Run an allowed command inside the workspace, bounded and observable."""
    impact = classify(argv)
    if cancel_check is not None and cancel_check():
        return {
            "ok": False,
            "argv": argv,
            "impact": impact,
            "exit_code": None,
            "output": "",
            "error": "cancelled before execution",
            "error_kind": "cancelled",
            "duration_ms": 0.0,
        }
    started = time.perf_counter()
    resolved = resolve_argv(argv)
    try:
        proc = subprocess.run(
            resolved,
            cwd=str(ws.root),
            capture_output=True,
            text=True,
            timeout=timeout_s or LIMITS["timeout_s"],
        )
        output = ((proc.stdout or "") + (proc.stderr or ""))[: LIMITS["max_output_chars"]]
        return {
            "ok": proc.returncode == 0,
            "argv": argv,
            "impact": impact,
            "exit_code": proc.returncode,
            "output": output,
            "truncated": len((proc.stdout or "") + (proc.stderr or ""))
            > LIMITS["max_output_chars"],
            "error": None if proc.returncode == 0 else f"exit {proc.returncode}",
            "error_kind": None if proc.returncode == 0 else "command_failed",
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "argv": argv,
            "impact": impact,
            "exit_code": None,
            "output": "",
            "error": f"timed out after {timeout_s or LIMITS['timeout_s']}s",
            "error_kind": "timeout",
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "argv": argv,
            "impact": impact,
            "exit_code": None,
            "output": "",
            "error": f"binary not found: {argv[0]}",
            "error_kind": "not_found",
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        }


def parse_test_output(output: str) -> dict[str, Any]:
    """Extract a structured summary from pytest output."""
    import re

    m = re.search(r"(\d+) failed", output or "")
    failed = int(m.group(1)) if m else 0
    m = re.search(r"(\d+) passed", output or "")
    passed = int(m.group(1)) if m else 0
    m = re.search(r"(\d+) error", output or "")
    errors = int(m.group(1)) if m else 0
    names = re.findall(r"^FAILED (\S+)", output or "", re.M)
    return {
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "failing_tests": names,
        "green": failed == 0 and errors == 0 and passed > 0,
    }
