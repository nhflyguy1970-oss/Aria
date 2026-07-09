"""Tool runner — launch CLIs, monitor runs, collect results."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.tools.runner")

RUNS_DIR = DATA_DIR / "tools" / "runs"
_active: dict[str, subprocess.Popen[str]] = {}
_lock = threading.Lock()


@dataclass
class ToolRun:
    id: str
    tool_id: str
    task: str
    cwd: str = ""
    status: str = "pending"
    pid: int = 0
    started_at: float = field(default_factory=time.time)
    finished_at: float = 0.0
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run_path(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}.json"


def save_run(run: ToolRun) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    _run_path(run.id).write_text(json.dumps(run.to_dict(), indent=2), encoding="utf-8")


def load_run(run_id: str) -> ToolRun | None:
    path = _run_path(run_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ToolRun(**data)
    except (json.JSONDecodeError, TypeError):
        return None


def list_runs(*, tool_id: str = "", limit: int = 20) -> list[ToolRun]:
    if not RUNS_DIR.is_dir():
        return []
    runs: list[ToolRun] = []
    for path in sorted(RUNS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        run = load_run(path.stem)
        if run and (not tool_id or run.tool_id == tool_id):
            runs.append(run)
        if len(runs) >= limit:
            break
    return runs


def build_command(tool_id: str, params: dict[str, Any]) -> tuple[list[str], str] | None:
    """Return argv and cwd for a tool invocation."""
    import shutil

    task = str(params.get("task") or params.get("prompt") or "").strip()
    cwd = str(params.get("cwd") or os.getcwd())
    if not task:
        return None

    binary_map = {
        "claude_code": "claude",
        "gemini_cli": "gemini",
        "opencode": "opencode",
        "goose": "goose",
        "hermes": "hermes",
        "continue": shutil.which("cn") or shutil.which("continue") or "cn",
        "openhands": "openhands",
    }
    binary = binary_map.get(tool_id, "")
    if not binary or not shutil.which(binary):
        return None

    if tool_id == "claude_code":
        args = [binary, "-p", task, "--output-format", "text"]
        if params.get("dangerous"):
            args.insert(1, "--dangerously-skip-permissions")
        return args, cwd

    if tool_id == "gemini_cli":
        return [binary, task], cwd

    if tool_id == "goose":
        return [binary, "run", task], cwd

    if tool_id == "continue":
        return [binary, "--prompt", task], cwd

    if tool_id == "opencode":
        subcmd = str(params.get("subcommand") or "run").strip()
        if subcmd == "serve":
            return [binary, "serve"], cwd
        return [binary, subcmd, task], cwd

    return [binary, task], cwd


def run_sync(tool_id: str, params: dict[str, Any], *, timeout: int = 600) -> dict[str, Any]:
    built = build_command(tool_id, params)
    if not built:
        from jarvis.tools.registry import get_tool

        tool = get_tool(tool_id)
        if tool and tool.run:
            return tool.run(params)
        return {"ok": False, "error": f"Cannot build command for {tool_id}"}

    args, cwd = built
    try:
        proc = subprocess.run(
            args,
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[:8000],
            "stderr": (proc.stderr or "")[:2000],
            "command": args,
            "cwd": cwd,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timed out after {timeout}s", "command": args}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "command": args}


def start_background(tool_id: str, params: dict[str, Any]) -> ToolRun:
    built = build_command(tool_id, params)
    task = str(params.get("task") or params.get("prompt") or "")
    cwd = str(params.get("cwd") or os.getcwd())
    run = ToolRun(
        id=uuid.uuid4().hex[:12], tool_id=tool_id, task=task[:500], cwd=cwd, status="running"
    )
    save_run(run)

    if not built:
        run.status = "failed"
        run.error = f"Cannot build command for {tool_id}"
        save_run(run)
        return run

    args, workdir = built

    def _watch(proc: subprocess.Popen[str], tool_run: ToolRun) -> None:
        try:
            stdout, stderr = proc.communicate(timeout=int(params.get("timeout") or 3600))
            tool_run.returncode = proc.returncode
            tool_run.stdout = (stdout or "")[:8000]
            tool_run.stderr = (stderr or "")[:2000]
            tool_run.status = "completed" if proc.returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            proc.kill()
            tool_run.status = "failed"
            tool_run.error = "timeout"
        except Exception as exc:
            tool_run.status = "failed"
            tool_run.error = str(exc)[:300]
        finally:
            tool_run.finished_at = time.time()
            save_run(tool_run)
            with _lock:
                _active.pop(tool_run.id, None)
            if tool_run.status == "completed":
                try:
                    from jarvis.personalization.learner import learn_from_tool_result

                    learn_from_tool_result(tool_id, {"ok": True, "stdout": tool_run.stdout})
                    if tool_id == "opencode":
                        _remember_opencode_result(tool_run)
                except Exception:
                    pass

    try:
        proc = subprocess.Popen(
            args,
            cwd=workdir or None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy(),
        )
        run.pid = proc.pid or 0
        save_run(run)
        with _lock:
            _active[run.id] = proc
        threading.Thread(
            target=_watch, args=(proc, run), daemon=True, name=f"tool-{run.id}"
        ).start()
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)[:300]
        run.finished_at = time.time()
        save_run(run)

    return run


def _remember_opencode_result(run: ToolRun) -> None:
    if not run.stdout:
        return
    try:
        from jarvis.assistant_instance import get_assistant

        assistant = get_assistant()
        if hasattr(assistant, "memory") and assistant.memory:
            assistant.memory.add(
                f"[opencode:{run.id}] {run.task}\n{run.stdout[:600]}",
                entry_type="tool_result",
                namespace="opencode",
                tags=["opencode", "coding"],
            )
    except Exception:
        pass


def run_status(run_id: str) -> dict[str, Any]:
    run = load_run(run_id)
    if not run:
        return {"ok": False, "error": "run not found"}
    with _lock:
        active = run_id in _active
    return {"ok": True, "run": run.to_dict(), "active": active}
