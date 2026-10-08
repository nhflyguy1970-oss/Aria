"""Disposable workspaces and ARIA's own evidence collection.

An agent never works in a project's real checkout. Each run gets a shallow
``git clone`` of the project's committed HEAD in a directory outside ARIA's
data and code, whose push URL is unusable, and runs inside a bubblewrap
sandbox in which everything except that workspace and the agent's own state
directory is read-only. Production data (FTR, BlackFly) is therefore not
writable by the agent at all — not merely "asked not to be written".

Evidence comes from ARIA, not from the agent: the diff is ``git diff``
against the base commit, tests are run by ARIA in a no-network sandbox, and
protected paths are fingerprinted before and after.
"""

from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

NO_PUSH_URL = "no-push://aria-blocked"
DIFF_EXCERPT_CHARS = 6000
TEST_OUTPUT_CHARS = 3000


class WorkspaceError(RuntimeError):
    pass


def workspaces_root() -> Path:
    raw = os.environ.get("JARVIS_AGENT_WORKSPACES", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    from jarvis.config import PROJECT_ROOT

    return (PROJECT_ROOT.resolve().parent / "aria-agent-workspaces").resolve()


def _git(args: list[str], cwd: Path | str, timeout: int = 120) -> subprocess.CompletedProcess:
    from jarvis.security.owner.env_boundary import build_subprocess_env

    env = build_subprocess_env(extra={"GIT_TERMINAL_PROMPT": "0", "GIT_SSH_COMMAND": "false"})
    env.pop("SSH_AUTH_SOCK", None)
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=timeout, env=env)


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def prepare(project_path: str, run_id: str) -> dict[str, Any]:
    """Clone the project's HEAD into a fresh workspace. Writes nothing to the project."""
    src = Path(project_path).expanduser().resolve()
    if not (src / ".git").exists():
        raise WorkspaceError(f"not a git repository: {src}")
    root = workspaces_root()
    from jarvis.config import DATA_DIR, PROJECT_ROOT

    for forbidden in (DATA_DIR, PROJECT_ROOT, src):
        if _inside(root, Path(forbidden)):
            raise WorkspaceError(f"workspace root {root} must not be inside {forbidden}")
    root.mkdir(parents=True, exist_ok=True)
    ws = root / f"run-{run_id}"
    if ws.exists():
        raise WorkspaceError(f"workspace already exists: {ws}")
    proc = _git(["clone", "--quiet", "--no-hardlinks", "--depth", "1", src.as_uri(), str(ws)], root, timeout=600)
    if proc.returncode != 0:
        raise WorkspaceError(f"clone failed: {(proc.stderr or proc.stdout).strip()[:300]}")
    _git(["remote", "set-url", "--push", "origin", NO_PUSH_URL], ws)
    _git(["config", "user.name", "ARIA agent workspace"], ws)
    _git(["config", "user.email", "aria-agent@localhost"], ws)
    base = _git(["rev-parse", "HEAD"], ws).stdout.strip()
    dirty = _git(["status", "--porcelain"], src, timeout=60).stdout.strip()
    return {
        "workspace": str(ws),
        "base_commit": base,
        "source": str(src),
        "source_uncommitted_changes": bool(dirty),
    }


def collect_changes(ws: str, base: str) -> dict[str, Any]:
    """What actually changed, according to git — committed or not."""
    w = Path(ws)
    _git(["add", "-A"], w)
    names = _git(["diff", "--cached", "--name-status", base], w).stdout.strip().splitlines()
    stat = _git(["diff", "--cached", "--stat", base], w).stdout.strip()
    diff = _git(["diff", "--cached", base], w).stdout
    commits = _git(["rev-list", "--count", f"{base}..HEAD"], w).stdout.strip()
    files = []
    for line in names:
        parts = line.split("\t")
        if len(parts) >= 2:
            files.append({"status": parts[0], "path": parts[-1]})
    return {
        "files": files,
        "stat": stat[-2000:],
        "diff_excerpt": diff[:DIFF_EXCERPT_CHARS],
        "diff_truncated": len(diff) > DIFF_EXCERPT_CHARS,
        "diff_sha256": hashlib.sha256(diff.encode()).hexdigest() if diff else "",
        "agent_commits": int(commits or 0),
        "push_url": _git(["remote", "get-url", "--push", "origin"], w).stdout.strip(),
    }


def fingerprint(paths: list[str], *, max_files: int = 5000) -> dict[str, Any]:
    """Size + mtime (+ hash for small files) of protected paths, to prove they were not touched."""
    out: dict[str, Any] = {}
    for raw in paths:
        p = Path(raw).expanduser()
        if not p.exists():
            out[raw] = None
            continue
        entries = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file())[:max_files]
        h = hashlib.sha256()
        for f in entries:
            try:
                st = f.stat()
            except OSError:
                continue
            h.update(f"{f}|{st.st_size}|{st.st_mtime_ns}".encode())
        out[raw] = {"files": len(entries), "digest": h.hexdigest()}
    return out


def bwrap_available() -> bool:
    return bool(shutil.which("bwrap"))


def sandbox_argv(argv: list[str], ws: str, *, writable: list[str] | None = None, readable: list[str] | None = None,
                 network: bool = True) -> list[str]:
    """Read-only root, writable workspace (+ agent state dirs), private /tmp."""
    bw = shutil.which("bwrap")
    if not bw:
        raise WorkspaceError("bubblewrap (bwrap) is not installed; refusing to run an agent unsandboxed")
    args = [bw, "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp"]
    for extra in readable or []:  # e.g. the agent binary's dir, if it lives under /tmp
        if Path(extra).exists():
            args += ["--ro-bind", extra, extra]
    for extra in writable or []:
        if Path(extra).exists():
            args += ["--bind", extra, extra]
    args += ["--bind", ws, ws, "--die-with-parent", "--new-session", "--chdir", ws]
    if not network:
        args.append("--unshare-net")
    return args + ["--", *argv]


def run_tests(ws: str, command: str, *, timeout: int = 600) -> dict[str, Any]:
    """Run the project's owner-configured test command, sandboxed, no network."""
    from jarvis.security.owner.env_boundary import build_subprocess_env

    if not command.strip():
        return {"ran": False, "reason": "no test command configured for this project"}
    argv = sandbox_argv(["sh", "-c", command], ws, network=False)
    started = time.time()
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, env=build_subprocess_env(), cwd=ws,
            stdin=subprocess.DEVNULL,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return {
            "ran": True,
            "command": command,
            "exit_code": proc.returncode,
            "passed": proc.returncode == 0,
            "seconds": round(time.time() - started, 1),
            "output_tail": out[-TEST_OUTPUT_CHARS:],
            "ran_by": "aria",
            "sandbox": "bwrap: read-only root, writable workspace, no network",
        }
    except subprocess.TimeoutExpired:
        return {"ran": True, "command": command, "exit_code": None, "passed": False,
                "error": f"timed out after {timeout}s", "ran_by": "aria"}


def agent_state_dirs(agent: str) -> list[str]:
    """Where each CLI keeps its login/session state — writable inside the sandbox."""
    home = Path.home()
    dirs = {
        "codex": [home / ".codex"],
        "claude_code": [home / ".claude", home / ".claude.json", home / ".cache" / "claude"],
        "antigravity": [home / ".gemini", home / ".cache" / "agy", home / ".config" / "agy"],
    }.get(agent, [])
    return [str(d) for d in dirs if d.exists()]


def quote(argv: list[str]) -> str:
    return " ".join(shlex.quote(a) for a in argv)
