"""Git helpers for coding module."""

import shutil
import subprocess
from pathlib import Path

from jarvis.config import PROJECT_ROOT


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd,
            cwd=str(cwd or PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 1, str(e)


def is_repo(path: Path | None = None) -> bool:
    code, _ = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=path or PROJECT_ROOT)
    return code == 0


def status(path: Path | None = None) -> str:
    if not is_repo(path):
        return "Not a git repository."
    _, out = _run(["git", "status", "-sb"], cwd=path or PROJECT_ROOT)
    return out.strip() or "Clean working tree."


def diff(path: Path | None = None, file: str | None = None) -> str:
    if not is_repo(path):
        return "Not a git repository."
    cmd = ["git", "diff"]
    if file:
        cmd.append(file)
    _, out = _run(cmd, cwd=path or PROJECT_ROOT)
    return out.strip() or "No changes."


def log_oneline(limit: int = 10, path: Path | None = None) -> str:
    if not is_repo(path):
        return "Not a git repository."
    _, out = _run(["git", "log", f"-{limit}", "--oneline"], cwd=path or PROJECT_ROOT)
    return out.strip()


def commit(message: str, path: Path | None = None, files: list[str] | None = None) -> str:
    if not is_repo(path):
        return "ERROR: Not a git repository."
    cwd = path or PROJECT_ROOT
    if files:
        for f in files:
            code, out = _run(["git", "add", f], cwd=cwd)
            if code != 0:
                return f"ERROR: git add {f} failed: {out}"
    else:
        code, out = _run(["git", "add", "-A"], cwd=cwd)
        if code != 0:
            return f"ERROR: git add failed: {out}"
    code, out = _run(["git", "commit", "-m", message], cwd=cwd)
    if code != 0:
        return f"ERROR: {out}"
    return out.strip() or "Committed."


def create_branch(name: str, path: Path | None = None) -> str:
    if not is_repo(path):
        return "ERROR: Not a git repository."
    cwd = path or PROJECT_ROOT
    code, out = _run(["git", "checkout", "-b", name], cwd=cwd)
    if code != 0:
        return f"ERROR: {out}"
    return f"Created and switched to branch `{name}`."


def current_branch(path: Path | None = None) -> str:
    if not is_repo(path):
        return ""
    _, out = _run(["git", "branch", "--show-current"], cwd=path or PROJECT_ROOT)
    return out.strip()


def summarize_diff(path: Path | None = None, file: str | None = None) -> str:
    """Return diff text for LLM summarization."""
    return diff(path=path, file=file)


def create_pull_request(
    title: str,
    body: str = "",
    *,
    base: str = "main",
    path: Path | None = None,
) -> str:
    """Create a GitHub PR via gh CLI (branch must be pushed first)."""
    if not shutil.which("gh"):
        return "ERROR: GitHub CLI (`gh`) not installed. Install it and run `gh auth login`."
    if not is_repo(path):
        return "ERROR: Not a git repository."
    cwd = path or PROJECT_ROOT
    cmd = ["gh", "pr", "create", "--title", title, "--base", base]
    if body.strip():
        cmd.extend(["--body", body])
    code, out = _run(cmd, cwd=cwd)
    if code != 0:
        return f"ERROR: {out.strip()}"
    return out.strip() or "Pull request created."
