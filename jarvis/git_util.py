"""Git helpers for Jarvis — status, diff, commit, branches, PRs."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from jarvis.config import PROJECT_ROOT


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd or PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)


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
    cmd = ["git", "diff", "HEAD"]
    if file:
        cmd.extend(["--", file])
    _, out = _run(cmd, cwd=path or PROJECT_ROOT)
    return out.strip() or "(no diff)"


def log_oneline(limit: int = 10, path: Path | None = None) -> str:
    if not is_repo(path):
        return "Not a git repository."
    _, out = _run(["git", "log", f"-{max(1, limit)}", "--oneline"], cwd=path or PROJECT_ROOT)
    return out.strip() or "(empty log)"


def commit(message: str, path: Path | None = None, files: list[str] | None = None) -> str:
    if not is_repo(path):
        return "ERROR: Not a git repository."
    cwd = path or PROJECT_ROOT
    if files:
        for rel in files:
            code, out = _run(["git", "add", "--", rel], cwd=cwd)
            if code != 0:
                return f"ERROR: git add failed: {out}"
    else:
        code, out = _run(["git", "add", "-A"], cwd=cwd)
        if code != 0:
            return f"ERROR: git add failed: {out}"
    code, out = _run(["git", "commit", "-m", message], cwd=cwd)
    if code != 0:
        return f"ERROR: {out or 'commit failed'}"
    return out.strip() or "Committed."


def create_branch(name: str, path: Path | None = None) -> str:
    if not is_repo(path):
        return "ERROR: Not a git repository."
    code, out = _run(["git", "checkout", "-b", name], cwd=path or PROJECT_ROOT)
    if code != 0:
        return f"ERROR: {out or 'branch create failed'}"
    return out.strip() or f"Created branch `{name}`."


def current_branch(path: Path | None = None) -> str:
    if not is_repo(path):
        return ""
    _, out = _run(["git", "branch", "--show-current"], cwd=path or PROJECT_ROOT)
    return out.strip()


def has_local_changes(path: Path | None = None) -> bool:
    """True when tracked files differ from HEAD (ignores untracked files)."""
    if not is_repo(path):
        return False
    root = path or PROJECT_ROOT
    for args in (["git", "diff", "--quiet", "HEAD"], ["git", "diff", "--cached", "--quiet"]):
        code, _ = _run(args, cwd=root)
        if code != 0:
            return True
    return False


def checkout_branch(name: str, path: Path | None = None) -> tuple[bool, str]:
    if not is_repo(path):
        return False, "Not a git repository."
    code, out = _run(["git", "checkout", name], cwd=path or PROJECT_ROOT)
    return code == 0, out.strip()


def merge_branch(
    branch: str,
    *,
    base: str | None = None,
    path: Path | None = None,
) -> tuple[bool, str]:
    if not is_repo(path):
        return False, "Not a git repository."
    cwd = path or PROJECT_ROOT
    if base:
        ok, msg = checkout_branch(base, cwd)
        if not ok:
            return False, msg
    code, out = _run(["git", "merge", branch], cwd=cwd)
    return code == 0, out.strip() or f"Merged `{branch}`."


def delete_branch(name: str, *, force: bool = False, path: Path | None = None) -> tuple[bool, str]:
    if not is_repo(path):
        return False, "Not a git repository."
    flag = "-D" if force else "-d"
    code, out = _run(["git", "branch", flag, name], cwd=path or PROJECT_ROOT)
    return code == 0, out.strip() or f"Deleted branch `{name}`."


def summarize_diff(path: Path | None = None, file: str | None = None) -> str:
    return diff(path=path, file=file)


def create_pull_request(
    title: str,
    body: str = "",
    *,
    base: str = "main",
    path: Path | None = None,
) -> str:
    if not shutil.which("gh"):
        return "ERROR: GitHub CLI (`gh`) not installed. Install it and run `gh auth login`."
    if not is_repo(path):
        return "ERROR: Not a git repository."
    cmd = ["gh", "pr", "create", "--title", title, "--base", base]
    if body.strip():
        cmd.extend(["--body", body])
    code, out = _run(cmd, cwd=path or PROJECT_ROOT)
    if code != 0:
        return f"ERROR: {out or 'gh pr create failed'}"
    return out.strip() or "Pull request created."
