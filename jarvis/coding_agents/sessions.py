"""Private Codex continuations; scope-bound to a new, single-use owner approval."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
from jarvis.coding_agents import contract, workspace


def process_identity(pid: int) -> dict:
    try:
        proc = Path("/proc") / str(pid)
        return {
            "pid": pid,
            "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
            "start_ticks": (proc / "stat").read_text().rsplit(")", 1)[1].split()[19],
        }
    except (OSError, IndexError):
        return {}


def tree_hash(root: Path) -> str:
    """Hash metadata and regular files, rejecting links instead of following them."""
    if root.is_symlink() or not root.is_dir():
        raise workspace.WorkspaceError("private session state is missing or redirected")
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not workspace._inside(path, root):
            raise workspace.WorkspaceError("private session state contains a redirected path")
        if path.is_file():
            content = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    content.update(chunk)
            digest.update(json.dumps([str(path.relative_to(root)), path.stat().st_mode & 0o777, content.hexdigest()]).encode() + b"\n")
    return digest.hexdigest()


def resume_scope(run: dict) -> dict:
    if run.get("agent") != "codex" or run.get("status") not in contract.TERMINAL:
        raise workspace.WorkspaceError("only a stopped Codex run can be continued")
    if run["status"] in (contract.VIOLATION, contract.REFUSED):
        raise workspace.WorkspaceError("a refused or boundary-violating run cannot be continued")
    receipt = run.get("receipt") or {}
    thread = receipt.get("session_id") or (run.get("result") or {}).get("session_id")
    if not thread or not receipt.get("private_state"):
        raise workspace.WorkspaceError("this run has no durable private Codex session")
    root = workspace.workspaces_root()
    ws = Path(run.get("workspace") or "")
    if not ws.is_dir() or ws.is_symlink() or not workspace._inside(ws, root) or ws == root:
        raise workspace.WorkspaceError("continuation workspace is missing or outside the approved root")
    state = []
    for source, target in receipt["private_state"]:
        path = Path(source)
        if not workspace._inside(path, root) or path == root:
            raise workspace.WorkspaceError("private session state is outside the workspace root")
        state.append({"source": source, "target": target, "sha256": tree_hash(path)})
    if not any(
        list((Path(item["source"]) / "sessions").rglob("*.jsonl")) or list((Path(item["source"]) / "archived_sessions").rglob("*.jsonl"))
        for item in state
    ):
        raise workspace.WorkspaceError("the Codex thread has no saved turn history to resume")
    snapshot = workspace.snapshot(str(ws))
    if receipt.get("workspace_snapshot") and snapshot != receipt["workspace_snapshot"]:
        raise workspace.WorkspaceError("continuation workspace changed after its recorded outcome")
    return {
        "run_id": run["id"],
        "thread_id": thread,
        "workspace": str(ws),
        "base_commit": run["base_commit"],
        "mode": run["mode"],
        "workspace_snapshot": snapshot,
        "private_state": state,
    }
