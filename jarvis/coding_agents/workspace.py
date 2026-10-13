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
import json
import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

NO_PUSH_URL = "no-push://aria-blocked"
ARTIFACT_PATTERNS = ["__pycache__/", "*.py[cod]", ".pytest_cache/", ".mypy_cache/", ".ruff_cache/", ".coverage"]
# Hidden inside the agent sandbox: other projects, production data, the owner's home.
HIDDEN_ROOTS = ["/home", "/media", "/mnt", "/root", "/srv", "/run"]
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


def _git(args: list[str], cwd: Path | str, timeout: int = 120, *, untrusted: bool = False) -> subprocess.CompletedProcess:
    from jarvis.security.owner.env_boundary import build_subprocess_env

    env = build_subprocess_env(extra={"GIT_TERMINAL_PROMPT": "0", "GIT_SSH_COMMAND": "false", "GIT_OPTIONAL_LOCKS": "0"})
    env.pop("SSH_AUTH_SOCK", None)
    env.pop("GIT_EXTERNAL_DIFF", None)
    if args and args[0] in ("diff", "show"):
        args = [args[0], "--no-ext-diff", "--no-textconv", *args[1:]]
    argv = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args]
    # Repository config/attributes are agent-controlled executable inputs.
    # Collect evidence under the boundary too, even after the agent has exited.
    if untrusted or (_inside(Path(cwd), workspaces_root()) and Path(cwd) != workspaces_root()):
        argv = sandbox_argv(argv, str(cwd), network=False)
    return subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, timeout=timeout, env=env)


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
    # Interpreter/test byproducts are not changes (and are never promoted).
    exclude = ws / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text(exclude.read_text() + "\n" + "\n".join(ARTIFACT_PATTERNS) + "\n" if exclude.exists()
                       else "\n".join(ARTIFACT_PATTERNS) + "\n")
    # Owner-configured verification sometimes invokes <checkout>/venv. Keep
    # that toolchain available in every verification clone, not just inventory
    # dry runs. Agent sandboxes hide its source; verification binds root read-only.
    toolchains = []
    for name in ("venv", ".venv"):
        runtime, target = src / name, ws / name
        if runtime.is_dir() and not target.exists() and not target.is_symlink():
            target.symlink_to(runtime, target_is_directory=True)
            toolchains.append(str(runtime))
            with exclude.open("a") as handle:
                handle.write(f"/{name}\n")
    # Python project suites can inspect their JS downloader/runtime flags.
    # Expose only the installed executable, never the surrounding home tree.
    node = shutil.which("node")
    if node and Path(node).is_file():
        toolchains.append(node)
    _git(["config", "user.name", "ARIA agent workspace"], ws)
    _git(["config", "user.email", "aria-agent@localhost"], ws)
    base = _git(["rev-parse", "HEAD"], ws).stdout.strip()
    dirty = _git(["status", "--porcelain"], src, timeout=60).stdout.strip()
    # Keep trusted toolchain roots outside the agent-writable clone. An agent
    # may replace a venv symlink, but cannot authorize that new target for reads.
    toolchain_record = ws.parent / f"{ws.name}.toolchains.json"
    toolchain_record.write_text(json.dumps(toolchains))
    toolchain_record.chmod(0o600)
    return {
        "workspace": str(ws),
        "base_commit": base,
        "source": str(src),
        "source_uncommitted_changes": bool(dirty),
        "verification_toolchains": toolchains,
    }


def collect_changes(ws: str, base: str) -> dict[str, Any]:
    """What actually changed, according to git — committed or not."""
    w = Path(ws)
    def git(args):
        result = _git(args, w, untrusted=True)
        if result.returncode:
            raise WorkspaceError('git evidence collection failed: ' + ' '.join(args[:2]))
        return result
    git(["add", "-A"])
    names = git(["diff", "--cached", "--name-status", base]).stdout.strip().splitlines()
    stat = git(["diff", "--cached", "--stat", base]).stdout.strip()
    diff = git(["diff", "--binary", "--cached", base]).stdout
    commits = git(["rev-list", "--count", f"{base}..HEAD"]).stdout.strip()
    files = []
    for line in names:
        parts = line.split("\t")
        if len(parts) >= 2:
            files.append({"status": parts[0], "path": parts[-1]})
    return {
        "files": files,
        "stat": stat[-2000:],
        "patch": diff,
        "diff_excerpt": diff[:DIFF_EXCERPT_CHARS],
        "diff_truncated": len(diff) > DIFF_EXCERPT_CHARS,
        "diff_sha256": hashlib.sha256(diff.encode()).hexdigest() if diff else "",
        "agent_commits": int(commits or 0),
        "push_url": git(["remote", "get-url", "--push", "origin"]).stdout.strip(),
    }


def bwrap_available() -> bool:
    return bool(shutil.which("bwrap"))


def sandbox_argv(argv: list[str], ws: str, *, writable: list[str] | None = None, readable: list[str] | None = None,
                 network: bool = False, hide_roots: bool = True, read_only: bool = False,
                 state_bindings: list[tuple[str, str]] | None = None, readonly: list[str] | None = None) -> list[str]:
    """Read-only root, writable workspace (+ agent state dirs), private /tmp."""
    bw = shutil.which("bwrap")
    if not bw:
        raise WorkspaceError("bubblewrap (bwrap) is not installed; refusing to run an agent unsandboxed")
    args = [bw, "--ro-bind", "/", "/", "--unshare-pid", "--unshare-ipc", "--unshare-uts",
            "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp", "--tmpfs", "/run",
            "--tmpfs", f"/run/user/{os.getuid()}"]
    # Reads are confined too: an agent working on one project must not read the
    # owner's home (shell history, other projects) or production data elsewhere.
    for root in (r for r in HIDDEN_ROOTS if r != "/run") if hide_roots else []:
        if Path(root).is_dir():
            args += ["--tmpfs", root]
    for extra in readable or []:  # the agent's own installation, read-only
        if Path(extra).exists():
            args += ["--ro-bind", extra, extra]
    for extra in writable or []:
        if Path(extra).exists():
            args += ["--bind", extra, extra]
    for source, target in state_bindings or []:
        args += ["--bind", source, target]
    for extra in readonly or []:
        if Path(extra).is_file():
            args += ["--ro-bind", extra, extra]
    args += ["--ro-bind" if read_only else "--bind", ws, ws,
             "--die-with-parent", "--new-session", "--chdir", ws]
    if not network:
        args.append("--unshare-net")
    return args + ["--", *argv]


_SCOPE_OK: bool | None = None


def scope_available() -> bool:
    """Can we put a run in a transient systemd scope with resource limits?"""
    global _SCOPE_OK
    if _SCOPE_OK is None:
        from jarvis.security.owner.env_boundary import build_subprocess_env

        try:
            _SCOPE_OK = shutil.which("systemd-run") is not None and subprocess.run(
                ["systemd-run", "--user", "--scope", "--quiet", "--", "true"],
                capture_output=True, timeout=15, env=build_subprocess_env(),
            ).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            _SCOPE_OK = False
    return _SCOPE_OK


LIMITS = {"MemoryMax": "6G", "CPUQuota": "400%", "TasksMax": "512"}


def limit_argv(argv: list[str]) -> tuple[list[str], dict[str, str]]:
    """Memory/CPU/process caps via a transient user scope (no root, no services)."""
    if not scope_available():
        return argv, {}
    props = [x for k, v in LIMITS.items() for x in ("-p", f"{k}={v}")]
    return ["systemd-run", "--user", "--scope", "--quiet", "--collect", *props, "--", *argv], dict(LIMITS)


def verification_readables(ws: str, command: str, *, in_place: bool = False) -> list[str]:
    """Only ARIA-recorded toolchains and the owner's explicit interpreter root."""
    root = Path(ws).resolve()
    record = root.parent / f"{root.name}.toolchains.json"
    sources = json.loads(record.read_text()) if record.is_file() else []
    for token in shlex.split(command):
        executable = Path(token)
        if executable.is_absolute() and executable.parent.name == "bin" and executable.parent.parent.name in ("venv", ".venv"):
            runtime = executable.parent.parent
            if not _inside(runtime, root):
                sources.append(str(runtime))
    if in_place:
        # Existing owner toolchains are trusted in the reviewed destination;
        # promoted symlinks are rejected by the promotion manifest checks.
        sources.extend(str((root / name).resolve()) for name in ("venv", ".venv")
                       if (root / name).is_symlink() and (root / name).is_dir())
    # A trusted toolchain may link its interpreter through another venv before
    # reaching /usr. Preserve that declared chain without following clone links.
    index = 0
    while index < len(sources) and index < 32:
        runtime = Path(sources[index])
        index += 1
        for name in ("python", "python3"):
            executable = runtime / "bin" / name
            if executable.is_symlink():
                target = executable.readlink()
                target = target if target.is_absolute() else executable.parent / target
                if target.parent.name == "bin" and target.parent.parent.name in ("venv", ".venv"):
                    linked = str(target.parent.parent)
                    if linked not in sources:
                        sources.append(linked)
    return sorted({str(Path(p)) for p in sources if Path(p).is_dir() or Path(p).is_file()})


def _terminate(proc) -> None:
    import signal

    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)
    except ProcessLookupError:
        pass


def run_tests(ws: str, command: str, *, timeout: float = 600, cancel_check=None) -> dict[str, Any]:
    """Bounded, cancellable independent verification inside the existing sandbox."""
    import threading
    from jarvis.security.owner.env_boundary import build_subprocess_env

    if not command.strip():
        return {"ran": False, "reason": "no test command configured for this project"}
    if cancel_check and cancel_check():
        return {"ran": False, "passed": False, "cancelled": True, "reason": "cancelled before verification"}
    toolchains = verification_readables(ws, command)
    argv = sandbox_argv(["sh", "-c", command], ws, network=False, readable=toolchains)
    started = time.monotonic()
    log_dir = Path(ws).parent / f"{Path(ws).name}.verification"
    log_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    log_path = log_dir / f"tests-{time.time_ns()}.log"
    cap = 4_000_000
    size = 0
    tail = ""
    overflow = threading.Event()
    proc = subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=build_subprocess_env(),
        cwd=ws,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )

    def pump():
        nonlocal size, tail
        with log_path.open("w") as log:
            log_path.chmod(0o600)
            while chunk := proc.stdout.read(8192):
                size += len(chunk.encode())
                if size > cap:
                    overflow.set()
                    continue
                log.write(chunk)
                log.flush()
                tail = (tail + chunk)[-TEST_OUTPUT_CHARS:]

    thread = threading.Thread(target=pump, daemon=True)
    thread.start()
    cancelled = timed_out = False
    try:
        while proc.poll() is None:
            cancelled = bool(cancel_check and cancel_check())
            timed_out = time.monotonic() - started >= max(0, timeout)
            if cancelled or timed_out or overflow.is_set():
                _terminate(proc)
                break
            time.sleep(0.05)
        proc.wait()
        thread.join(timeout=5)
        if thread.is_alive():
            raise WorkspaceError("verification output did not close")
    finally:
        if proc.poll() is None:
            _terminate(proc)
        proc.stdout.close()
    cancelled = cancelled or bool(cancel_check and cancel_check())
    return {
        "ran": True,
        "command": command,
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0 and not (cancelled or timed_out or overflow.is_set()),
        "cancelled": cancelled,
        "timed_out": timed_out,
        "output_limit_exceeded": overflow.is_set(),
        "seconds": round(time.monotonic() - started, 1),
        "output_tail": tail,
        "output_log": str(log_path),
        "ran_by": "aria",
        "sandbox": "bwrap: private roots/PID/IPC, writable workspace, trusted toolchains read-only, no network",
    }


def snapshot(ws: str) -> str:
    """Bind verification and continuation to actual code bytes, including untracked files."""
    root = Path(ws)
    proc = _git(["ls-files", "-z", "--cached", "--others", "--exclude-standard"], root, untrusted=True)
    if proc.returncode:
        raise WorkspaceError("workspace inventory failed")
    digest = hashlib.sha256()
    for name in sorted(set(filter(None, proc.stdout.split("\0")))):
        path = root / name
        if not _inside(path.parent, root):
            raise WorkspaceError("workspace inventory escaped its root")
        if path.is_symlink():
            entry = [name, "link", os.readlink(path)]
        elif path.is_file():
            content = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    content.update(chunk)
            entry = [name, "file", path.stat().st_mode & 0o777, content.hexdigest()]
        elif not path.exists():
            entry = [name, "missing"]
        else:
            raise WorkspaceError("unsupported workspace inventory path")
        digest.update(json.dumps(entry).encode() + b"\n")
    return digest.hexdigest()


def agent_state_dirs(agent: str) -> list[str]:
    """Where each CLI keeps its login/session state — writable inside the sandbox."""
    home = Path.home()
    dirs = {
        "codex": [home / ".codex"],
        "claude_code": [home / ".claude", home / ".claude.json", home / ".cache" / "claude"],
        "antigravity": [home / ".gemini", home / ".cache" / "agy", home / ".config" / "agy"],
    }.get(agent, [])
    return [str(d) for d in dirs if d.exists()]


def private_agent_state(agent: str, out_dir: Path, state_dirs: list[str], *, resume_state: list[dict] | None = None) -> list[tuple[str, str]]:
    """A run may use sign-in material, never the owner's shared session/history store.

    Only named sign-in files are copied into private writable state; permission
    configuration is overlaid read-only by the caller. Credentials are never
    returned in a receipt. Refreshes remain in the disposable state directory.
    """
    auth_names = {
        "codex": ("auth.json",),
        "claude_code": (".credentials.json",),
        "antigravity": ("oauth_creds.json", "google_accounts.json", "antigravity-cli/auth.json", "antigravity-cli/antigravity-oauth-token"),
    }.get(agent, ())
    if resume_state:
        from jarvis.coding_agents.sessions import tree_hash
        bindings = []
        for index, record in enumerate(resume_state):
            source = Path(record['source'])
            if tree_hash(source) != record['sha256']:raise WorkspaceError('private session changed after approval')
            private = out_dir / 'state' / str(index)
            private.mkdir(parents=True, mode=0o700)
            for path in source.iterdir():
                if path.name in ('auth.json', 'sessions', 'archived_sessions') or path.name.startswith('state_') and '.sqlite' in path.name:
                    dest = private / path.name
                    if path.is_dir():shutil.copytree(path, dest)
                    elif path.is_file():shutil.copy2(path, dest)
            bindings.append((str(private), record['target']))
        return bindings
    bindings = []
    for index, raw in enumerate(state_dirs):
        source = Path(raw)
        private = out_dir / "state" / str(index)
        private.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if source.is_file():
            # Only account/onboarding metadata is needed for subscription auth.
            # Owner hooks, permissions, MCP servers and project histories stay hidden.
            if agent == "claude_code" and source.name == ".claude.json" and not source.is_symlink():
                data = json.loads(source.read_text())
                private.write_text(json.dumps({k: data[k] for k in
                    ("oauthAccount", "hasCompletedOnboarding", "lastOnboardingVersion") if k in data}))
                private.chmod(0o600)
                bindings.append((str(private), str(source)))
            continue
        private.mkdir(mode=0o700)
        for rel in auth_names:
            src = source / rel
            if src.is_file() and not src.is_symlink():
                dst = private / rel
                dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                shutil.copyfile(src, dst)
                dst.chmod(0o600)
        bindings.append((str(private), str(source)))
    return bindings


def quote(argv: list[str]) -> str:
    return " ".join(shlex.quote(a) for a in argv)
