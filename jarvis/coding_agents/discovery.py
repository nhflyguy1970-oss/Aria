"""Find the installed coding-agent CLIs and what they can verifiably do.

Everything here is read-only and local: ``--version``, ``--help`` and each
CLI's own auth-status command. Nothing sends a prompt. Credential files are
never read — at most their *existence* is noted — and auth output is reduced
to a method and a billing class before it leaves this module.

Billing is recorded per agent because a subscription login (ChatGPT, Claude,
Google account) is not an API key: ARIA's paid cloud adapters (Phase 4) never
use these logins, and an agent found to be authenticated with a paid API key
is refused rather than used silently.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CACHE_TTL_S = 600
READ_ONLY = "read_only"
WORKSPACE_WRITE = "workspace_write"

# Flags each adapter depends on. Discovery re-checks them against the
# installed version's --help, so an upgrade that drops one is detected.
REQUIRED_FLAGS: dict[str, dict[str, list[str]]] = {
    "codex": {
        "exec": ["--json", "--sandbox", "--cd", "--ephemeral", "--output-last-message", "--config"],
    },
    "claude_code": {
        "": ["--print", "--output-format", "--permission-mode", "--tools", "--no-session-persistence"],
    },
    "antigravity": {
        "": ["--print", "--output-format", "--mode", "--sandbox", "--print-timeout"],
    },
}

LABELS = {"codex": "Codex CLI", "claude_code": "Claude Code", "antigravity": "Google Antigravity (agy)"}
BINARIES = {"codex": ("codex",), "claude_code": ("claude",), "antigravity": ("agy", "antigravity")}
ALIASES = {
    "codex": ("codex", "openai codex"),
    "claude_code": ("claude", "claude code"),
    "antigravity": ("antigravity", "agy", "google antigravity"),
}


@dataclass
class AgentStatus:
    agent: str
    label: str
    installed: bool = False
    path: str = ""
    version: str = ""
    auth: dict[str, Any] = field(default_factory=dict)
    modes: list[str] = field(default_factory=list)
    capabilities: dict[str, Any] = field(default_factory=dict)
    unsupported: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    missing_flags: list[str] = field(default_factory=list)
    execution: dict[str, Any] = field(default_factory=dict)

    @property
    def usable(self) -> bool:
        return (
            self.installed
            and not self.missing_flags
            and self.auth.get("state") in ("logged_in", "unknown")
            and not self.auth.get("paid_api")
            and self.execution.get("state") == "verified"
        )

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "usable": self.usable}


def _search_path() -> list[str]:
    """PATH plus the user-level bin dirs a systemd service usually lacks."""
    home = Path.home()
    dirs = [d for d in os.environ.get("PATH", "").split(os.pathsep) if d]
    extra = [str(home / ".local" / "bin"), "/usr/local/bin"]
    extra += sorted(glob.glob(str(home / ".nvm" / "versions" / "node" / "*" / "bin")), reverse=True)
    return dirs + [d for d in extra if d not in dirs]


def _which(names: tuple[str, ...]) -> str:
    path = os.pathsep.join(_search_path())
    for name in names:
        found = shutil.which(name, path=path)
        if found:
            return found
    return ""


def _run(argv: list[str], timeout: int = 20) -> tuple[int, str]:
    from jarvis.coding_agents import workspace
    from jarvis.coding_agents.runs import _install_dirs
    from jarvis.security.owner.env_boundary import build_subprocess_env

    env = build_subprocess_env(extra={"PATH": os.pathsep.join(_search_path()), "NO_COLOR": "1"})
    env.pop("SSH_AUTH_SOCK", None)
    try:
        # Even help/auth probes are untrusted programs. They never see owner
        # histories, original credentials, production roots or host sockets.
        with tempfile.TemporaryDirectory(prefix="aria-agent-discovery-") as raw:
            root = Path(raw)
            ws = root / "workspace"
            ws.mkdir()
            name = Path(argv[0]).name
            agent = "codex" if name == "codex" else "claude_code" if "claude" in name else "antigravity"
            bindings = workspace.private_agent_state(agent, root, workspace.agent_state_dirs(agent))
            command = workspace.sandbox_argv(argv, str(ws), writable=[str(root)],
                readable=_install_dirs(argv[0]), network=False, read_only=True, state_bindings=bindings)
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env=env, cwd=ws, stdin=subprocess.DEVNULL, start_new_session=True)
            chunks = {"stdout": [], "stderr": []}
            count = {"bytes": 0}
            lock = threading.Lock()
            def pump(stream, kind):
                while chunk := stream.read(8192):
                    with lock:
                        count["bytes"] += len(chunk)
                        if count["bytes"] <= 1_000_000:
                            chunks[kind].append(chunk)
            readers = [threading.Thread(target=pump, args=(stream, kind), daemon=True)
                       for stream, kind in ((proc.stdout, "stdout"), (proc.stderr, "stderr"))]
            for reader in readers:
                reader.start()
            deadline = time.monotonic() + timeout
            refused = ""
            while proc.poll() is None:
                if time.monotonic() >= deadline or count["bytes"] > 1_000_000:
                    from jarvis.coding_agents.runs import _kill
                    refused = "timed out" if time.monotonic() >= deadline else "discovery output limit exceeded"
                    _kill(proc)
                    break
                time.sleep(.01)
            proc.wait()
            for reader in readers:
                reader.join(timeout=2)
            if refused:
                return 124, refused
            from jarvis.coding_agents.runs import _private_tokens
            output = "".join(chunks["stdout"]) + "".join(chunks["stderr"])
            for secret in _private_tokens(bindings):
                output = output.replace(secret, "<redacted>")
            return proc.returncode, redact(output)

    except (OSError, workspace.WorkspaceError) as exc:
        return 127, f"isolated discovery refused: {type(exc).__name__}: {exc}"


_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_TOKENISH = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{8,}|eyJ[A-Za-z0-9._-]{20,}|[A-Za-z0-9_-]{40,})\b")


def redact(text: str) -> str:
    return _TOKENISH.sub("<redacted>", _EMAIL.sub("<email>", text or ""))


def _claude_native(wrapper: str) -> str:
    """The platform binary npm ships next to a wrapper whose postinstall never ran."""
    real = Path(wrapper).resolve()
    pkg = real.parent.parent  # .../@anthropic-ai/claude-code
    for cand in sorted(pkg.glob("node_modules/@anthropic-ai/claude-code-linux-*/claude")):
        if os.access(cand, os.X_OK) and "musl" not in cand.parent.name:
            return str(cand)
    return ""


def _version(agent: str, path: str, notes: list[str]) -> tuple[str, str]:
    rc, out = _run([path, "--version"])
    # The npm wrapper whose postinstall never ran either prints "native binary
    # not installed" (run via a shell) or, exec'd directly, fails with ENOEXEC.
    if agent == "claude_code" and (rc != 0 or "native binary not installed" in out):
        native = _claude_native(path)
        if native:
            notes.append(
                "the `claude` npm wrapper is broken (native binary not linked); "
                f"using the platform binary it ships: {native}"
            )
            path = native
            rc, out = _run([path, "--version"])
    if rc != 0:
        return path, ""
    return path, redact(out.strip().splitlines()[0] if out.strip() else "")


def _help_text(path: str, sub: str) -> str:
    argv = [path] + ([sub] if sub else []) + ["--help"]
    return _run(argv)[1]


def _missing_flags(agent: str, path: str) -> list[str]:
    missing = []
    for sub, flags in REQUIRED_FLAGS.get(agent, {}).items():
        text = _help_text(path, sub)
        missing += [f"{sub + ' ' if sub else ''}{f}" for f in flags if f not in text]
    return missing


def _auth(agent: str, path: str) -> dict[str, Any]:
    """State + method + billing class. Never tokens, emails or org names."""
    if agent == "codex":
        rc, out = _run([path, "login", "status"])
        line = redact(out.strip().splitlines()[0] if out.strip() else "")
        low = line.lower()
        if "not logged in" in low:
            return {"state": "logged_out", "method": "", "billing": "", "evidence": "codex login status"}
        if "chatgpt" in low:
            return {"state": "logged_in", "method": "chatgpt", "billing": "chatgpt_subscription",
                    "paid_api": False, "evidence": "codex login status"}
        if "api key" in low:
            return {"state": "logged_in", "method": "api_key", "billing": "openai_api",
                    "paid_api": True, "evidence": "codex login status"}
        return {"state": "unknown", "detail": line[:120], "evidence": "codex login status"}
    if agent == "claude_code":
        rc, out = _run([path, "auth", "status", "--json"])
        try:
            data = json.loads(out[out.find("{"):]) if "{" in out else {}
        except json.JSONDecodeError:
            data = {}
        if not data:
            return {"state": "unknown", "evidence": "claude auth status"}
        if not data.get("loggedIn"):
            return {"state": "logged_out", "evidence": "claude auth status"}
        method = str(data.get("authMethod") or "")
        sub = str(data.get("subscriptionType") or "")
        api = method.lower() in ("apikey", "api_key", "console") or str(data.get("apiKeySource") or "")
        return {
            "state": "logged_in",
            "method": method,
            "billing": "anthropic_api" if api else f"claude_subscription{':' + sub if sub else ''}",
            "provider": str(data.get("apiProvider") or ""),
            "paid_api": bool(api),
            "evidence": "claude auth status --json (identity fields dropped)",
        }
    if agent == "antigravity":
        # agy 1.x has no auth-status command; a sign-in can only be confirmed by
        # running a task. Say so instead of guessing from credential files.
        state_dir = Path.home() / ".gemini" / "antigravity-cli"
        proof = _last_successful_run("antigravity")
        if proof:
            return {
                "state": "logged_in",
                "method": "google_account",
                "billing": "google_account",
                "paid_api": False,
                "evidence": f"no auth-status command; a run completed successfully at {proof}",
            }
        return {
            "state": "unknown",
            "method": "google_account",
            "billing": "google_account",
            "paid_api": False,
            "evidence": "agy has no auth-status command; "
            + ("CLI state directory present" if state_dir.is_dir() else "no CLI state directory"),
        }
    return {"state": "unknown"}


def _last_successful_run(agent: str, max_age_s: float = 30 * 86400) -> str:
    """When this agent last finished a run with a reply — proof it can sign in."""
    try:
        import sqlite3

        from jarvis.config import DATA_DIR

        db = DATA_DIR / "coding_agents.db"
        if not db.is_file():
            return ""
        with sqlite3.connect(str(db), timeout=5) as conn:
            row = conn.execute(
                "SELECT finished_at FROM runs WHERE agent=? AND status IN ('completed','verified','changes_unverified',"
                "'no_changes','tests_failed') AND finished_at>? ORDER BY finished_at DESC LIMIT 1",
                (agent, time.time() - max_age_s),
            ).fetchone()
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(row[0])) if row else ""
    except Exception:
        return ""


def _capabilities(agent: str) -> tuple[list[str], dict[str, Any], list[str]]:
    """Modes and capabilities the adapter uses — each backed by a --help flag."""
    if agent == "codex":
        return (
            [READ_ONLY, WORKSPACE_WRITE],
            {
                "headless": "codex exec",
                "structured_output": "JSONL events (--json) + last message file",
                "read_only": "--sandbox read-only",
                "workspace_write": "--sandbox workspace-write (Codex's own sandbox; no network)",
                "working_directory": "--cd",
                "session_persistence": "off (--ephemeral)",
                "reports_commands": True,
                "reports_file_changes": True,
                "token_usage": True,
                "runs_commands": True,
            },
            ["interactive approvals in headless mode", "per-run spending cap (subscription)",
             "nested vendor sandbox compatibility (ARIA always keeps its outer bwrap; no unsafe fallback)"],
        )
    if agent == "claude_code":
        return (
            [READ_ONLY, WORKSPACE_WRITE],
            {
                "headless": "claude -p",
                "structured_output": "stream-json events + final result",
                "read_only": "--permission-mode plan --tools Read,Glob,Grep",
                "workspace_write": "--permission-mode acceptEdits --tools Read,Glob,Grep,Edit,Write (no shell)",
                "runs_commands": False,
                "working_directory": "process cwd",
                "session_persistence": "off (--no-session-persistence)",
                "reports_commands": True,
                "reports_file_changes": True,
                "token_usage": True,
            },
            [
                "running tests or shell commands (Bash tool not granted; ARIA runs tests itself)",
                "--max-budget-usd (API billing only; this login is a subscription)",
                "--bare (forces API-key auth)",
            ],
        )
    if agent == "antigravity":
        return (
            [READ_ONLY, WORKSPACE_WRITE],
            {
                "headless": "agy --print",
                "structured_output": "--output-format json (schema undocumented; parsed defensively)",
                "read_only": "--mode plan",
                "workspace_write": "--mode accept-edits --sandbox",
                "working_directory": "process cwd",
                "time_limit": "--print-timeout",
                "reports_commands": True,
                "reports_file_changes": True,
                "runs_commands": False,
            },
            [
                "auth-status check (no such command; sign-in is inferred from a completed run)",
                "tool allow-listing per run (agy reports permission_mode 'always-proceed' from its own settings)",
                "shell commands under ARIA's sandbox (agy's own command sandbox cannot nest inside bwrap)",
                "the Antigravity IDE/GUI (not automated)",
            ],
        )
    return [], {}, []


_cache: dict[str, Any] = {"at": 0.0, "data": None}
_cache_lock = threading.Lock()


def discover(*, refresh: bool = False) -> dict[str, AgentStatus]:
    with _cache_lock:
        if not refresh and _cache["data"] and time.time() - _cache["at"] < CACHE_TTL_S:
            return _cache["data"]
    out: dict[str, AgentStatus] = {}
    for agent in ("codex", "claude_code", "antigravity"):
        status = AgentStatus(agent=agent, label=LABELS[agent])
        path = _which(BINARIES[agent])
        if not path:
            status.notes.append("not installed (searched PATH, ~/.local/bin, nvm node bins)")
            out[agent] = status
            continue
        path, version = _version(agent, path, status.notes)
        status.path = path
        status.version = version
        status.installed = bool(version)
        if not status.installed:
            status.notes.append("executable found but --version failed")
            out[agent] = status
            continue
        status.missing_flags = _missing_flags(agent, path)
        status.auth = _auth(agent, path)
        status.modes, status.capabilities, status.unsupported = _capabilities(agent)
        from jarvis.coding_agents import runtime

        status.execution = runtime.compatibility(agent, path, version)
        if status.execution.get("state") != "verified":
            status.notes.append(status.execution.get("reason", "execution compatibility unverified"))
        if status.auth.get("paid_api"):
            status.notes.append("authenticated with a paid API key — ARIA will not use it without a cloud authorization")
        out[agent] = status
    with _cache_lock:
        _cache.update(at=time.time(), data=out)
    return out


def resolve_agent_name(text: str) -> str:
    low = (text or "").lower()
    for agent, names in ALIASES.items():
        if any(re.search(rf"\b{re.escape(n)}\b", low) for n in names):
            return agent
    return ""


def set_discovery_for_tests(statuses: dict[str, AgentStatus] | None) -> None:
    with _cache_lock:
        _cache.update(at=time.time() if statuses else 0.0, data=statuses)
