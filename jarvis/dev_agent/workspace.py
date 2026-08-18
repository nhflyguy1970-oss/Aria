"""Authorized development workspace — path confinement and repository safety.

The coding agent may only touch files inside an explicitly authorized root.
Confinement is enforced by resolving the real path and checking containment, so
symlinks and `..` cannot walk out. This is the boundary that keeps an
autonomous loop from editing the live ARIA tree by accident.

Repository safety is the second half: before the agent changes anything it
records which files the user already had modified, and it refuses operations
that would discard that work.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class WorkspaceError(RuntimeError):
    """The requested path or repository operation is not permitted."""


class PathEscape(WorkspaceError):
    """A path resolved outside the authorized workspace."""


@dataclass
class Workspace:
    """An authorized development root, usually a git repository."""

    root: Path
    task_id: str = ""
    branch: str = ""
    allow_untracked_delete: bool = False
    baseline_dirty: tuple[str, ...] = field(default_factory=tuple)

    def resolve(self, relative: str) -> Path:
        """Resolve a workspace-relative path, refusing anything outside it."""
        raw = (relative or "").strip()
        if not raw:
            raise PathEscape("Empty path")
        if os.path.isabs(raw):
            candidate = Path(raw)
        else:
            candidate = self.root / raw
        # resolve() follows symlinks, so a symlinked escape is caught too.
        real = candidate.resolve()
        root = self.root.resolve()
        if real != root and root not in real.parents:
            raise PathEscape(f"Path escapes workspace: {relative!r} -> {real}")
        return real

    def contains(self, path: str | Path) -> bool:
        try:
            self.resolve(str(path))
            return True
        except PathEscape:
            return False

    # ------------------------------------------------------------- file ops

    def read(self, relative: str, *, max_bytes: int = 400_000) -> str:
        target = self.resolve(relative)
        if not target.is_file():
            raise WorkspaceError(f"Not a file: {relative}")
        return target.read_text(encoding="utf-8", errors="replace")[:max_bytes]

    def write(self, relative: str, content: str) -> dict[str, Any]:
        target = self.resolve(relative)
        existed = target.is_file()
        before = target.read_text(encoding="utf-8", errors="replace") if existed else ""
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "path": str(target.relative_to(self.root.resolve())),
            "created": not existed,
            "modified": existed and before != content,
            "bytes": len(content.encode("utf-8")),
        }

    def delete(self, relative: str) -> dict[str, Any]:
        target = self.resolve(relative)
        if not target.is_file():
            raise WorkspaceError(f"Not a file: {relative}")
        rel = str(target.relative_to(self.root.resolve()))
        if rel in self.baseline_dirty and not self.allow_untracked_delete:
            raise WorkspaceError(f"Refusing to delete a file the user had modified: {rel}")
        target.unlink()
        return {"path": rel, "deleted": True}

    def list_files(self, *, limit: int = 500) -> list[str]:
        root = self.root.resolve()
        out = []
        for p in sorted(root.rglob("*")):
            if p.is_dir():
                continue
            if any(
                part in (".git", "__pycache__", ".pytest_cache", "node_modules") for part in p.parts
            ):
                continue
            out.append(str(p.relative_to(root)))
            if len(out) >= limit:
                break
        return out


def open_workspace(root: str | Path, *, task_id: str = "") -> Workspace:
    """Authorize a workspace and snapshot pre-existing user modifications."""
    path = Path(root).expanduser()
    if not path.is_dir():
        raise WorkspaceError(f"Workspace root does not exist: {root}")
    ws = Workspace(root=path.resolve(), task_id=task_id)
    ws.baseline_dirty = tuple(dirty_files(ws.root))
    ws.branch = current_branch(ws.root)
    return ws


# ----------------------------------------------------------- repository state


def _git(args: list[str], cwd: Path) -> tuple[int, str]:
    import subprocess

    try:
        proc = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=30
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except Exception as exc:  # noqa: BLE001
        return 1, str(exc)


def is_repo(root: Path) -> bool:
    code, _ = _git(["rev-parse", "--is-inside-work-tree"], root)
    return code == 0


def current_branch(root: Path) -> str:
    code, out = _git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    return out.strip() if code == 0 else ""


def head_commit(root: Path) -> str:
    code, out = _git(["rev-parse", "HEAD"], root)
    return out.strip() if code == 0 else ""


def dirty_files(root: Path) -> list[str]:
    """Files the user already had modified/untracked before the agent started."""
    code, out = _git(["status", "--porcelain"], root)
    if code != 0:
        return []
    files = []
    for line in out.splitlines():
        if len(line) > 3:
            files.append(line[3:].strip())
    return files


def repo_state(ws: Workspace) -> dict[str, Any]:
    return {
        "root": str(ws.root),
        "is_repo": is_repo(ws.root),
        "branch": current_branch(ws.root),
        "head": head_commit(ws.root),
        "dirty": dirty_files(ws.root),
        "baseline_dirty": list(ws.baseline_dirty),
    }


def unrelated_changes_preserved(ws: Workspace) -> dict[str, Any]:
    """Confirm the files the user had modified are still modified (not reverted)."""
    now = set(dirty_files(ws.root))
    missing = [f for f in ws.baseline_dirty if f not in now]
    return {"preserved": not missing, "lost": missing, "baseline": list(ws.baseline_dirty)}
