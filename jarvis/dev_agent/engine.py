"""Coding agent development loop — plan, inspect, implement, test, diagnose, fix, review.

Bounded by construction: iterations, test runs, files changed and commands are
all counted, and exhausting any limit stops the task in a `bounded` state with
the reason preserved rather than looping.

An `editor` is injectable. Tests drive it deterministically; in production it is
backed by ARIA's existing CodingAgent/model path. Nothing here writes a model's
output straight to disk — every edit goes through the workspace, which confines
paths and refuses to clobber the user's own modifications.

A task cannot reach `completed` unless its tests actually passed. That is the
single most important rule in this module.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from jarvis.dev_agent import commands, store, workspace

log = logging.getLogger("jarvis.dev_agent")

# editor(task, ws, context) -> {"files": [{"path", "content"}], "summary": str}
Editor = Callable[[dict[str, Any], workspace.Workspace, dict[str, Any]], dict[str, Any]]


class CodingAgentError(RuntimeError):
    pass


def resolve_model() -> str:
    try:
        from jarvis.config import MODELS

        return MODELS.get("coder", "") or MODELS.get("general", "")
    except Exception:  # noqa: BLE001 - model config must not break the loop
        return ""


def create_task(
    objective: str,
    workspace_root: str,
    *,
    mission_id: str = "",
    create_mission: bool = False,
) -> dict[str, Any]:
    """Create a durable coding task, locking its workspace."""
    if not (objective or "").strip():
        raise CodingAgentError("A coding task needs an objective")
    ws = workspace.open_workspace(workspace_root)
    task_id = store.create(objective, str(ws.root), mission_id=mission_id, model=resolve_model())

    if not store.acquire_lock(str(ws.root), task_id):
        holder = store.lock_holder(str(ws.root))
        store.update(
            task_id,
            phase=store.FAILED,
            error=f"workspace locked by {holder}",
            stop_reason="workspace_locked",
        )
        store.record_event(task_id, "lock:denied", holder)
        raise CodingAgentError(f"Workspace already has an active coding task: {holder}")

    state = workspace.repo_state(ws)
    store.update(
        task_id,
        baseline_dirty=state["dirty"],
        branch=state["branch"],
        head_commit=state["head"],
    )

    if create_mission:
        from jarvis import missions

        mid = missions.create_mission(
            f"Coding: {objective}",
            steps=[
                {
                    "name": f"coding {phase}",
                    "action": "dev_step",
                    "params": {"task_id": task_id, "phase": phase},
                }
                for phase in ("plan", "inspect", "implement", "test", "review")
            ],
            kind="coding",
        )
        store.update(task_id, mission_id=mid)
        missions.worker.wake()

    return store.get(task_id)  # type: ignore[return-value]


def _bounds_exhausted(task: dict[str, Any]) -> str:
    if task["iterations"] >= store.BOUNDS["max_iterations"]:
        return f"max_iterations ({store.BOUNDS['max_iterations']})"
    if task["test_runs"] >= store.BOUNDS["max_test_runs"]:
        return f"max_test_runs ({store.BOUNDS['max_test_runs']})"
    if len(task["files_changed"]) >= store.BOUNDS["max_files_changed"]:
        return f"max_files_changed ({store.BOUNDS['max_files_changed']})"
    if task["commands"] >= store.BOUNDS["max_commands"]:
        return f"max_commands ({store.BOUNDS['max_commands']})"
    if time.time() - task["created_at"] > store.BOUNDS["max_runtime_s"]:
        return f"max_runtime_s ({store.BOUNDS['max_runtime_s']})"
    return ""


def _stop_bounded(task_id: str, reason: str) -> dict[str, Any]:
    store.update(task_id, stop_reason=reason)
    store.record_event(task_id, "bounded", reason)
    store.set_phase(task_id, store.BOUNDED, detail=reason)
    return store.get(task_id)  # type: ignore[return-value]


def _ws(task: dict[str, Any]) -> workspace.Workspace:
    ws = workspace.open_workspace(task["workspace"], task_id=task["id"])
    ws.baseline_dirty = tuple(task["baseline_dirty"])
    return ws


# ------------------------------------------------------------------- phases


def phase_plan(task_id: str) -> dict[str, Any]:
    task = store.get(task_id)
    if not task:
        raise CodingAgentError(f"No such coding task: {task_id}")
    store.set_phase(task_id, store.PLANNING)
    plan = [
        "inspect repository and existing tests",
        "implement the requested change",
        "run focused tests",
        "diagnose and fix failures",
        "review the diff and complete",
    ]
    store.update(task_id, plan=plan)
    store.record_event(task_id, "plan", f"{len(plan)} steps", store.PLANNING)
    return {"plan": plan}


def phase_inspect(task_id: str, *, test_cmd: list[str] | None = None) -> dict[str, Any]:
    """Inspect the repo and record which tests already fail (pre-existing)."""
    task = store.get(task_id)
    if not task:
        raise CodingAgentError(f"No such coding task: {task_id}")
    store.set_phase(task_id, store.INSPECTING)
    ws = _ws(task)
    state = workspace.repo_state(ws)
    files = ws.list_files(limit=200)

    baseline_failures: list[str] = []
    if test_cmd:
        result = commands.run(test_cmd, ws)
        store.bump(task_id, "commands")
        summary = commands.parse_test_output(result["output"])
        baseline_failures = summary["failing_tests"]
        store.update(task_id, baseline_failures=baseline_failures)
        store.record_event(
            task_id,
            "baseline_tests",
            f"{summary['passed']} passed, {summary['failed']} failed (pre-existing)",
            store.INSPECTING,
        )
    store.record_event(task_id, "inspect", f"{len(files)} files", store.INSPECTING)
    return {"files": len(files), "repo": state, "baseline_failures": baseline_failures}


def phase_implement(
    task_id: str, editor: Editor, *, context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Apply the editor's changes through the confined workspace."""
    task = store.get(task_id)
    if not task:
        raise CodingAgentError(f"No such coding task: {task_id}")
    bound = _bounds_exhausted(task)
    if bound:
        return {"bounded": bound, "task": _stop_bounded(task_id, bound)}

    store.set_phase(task_id, store.IMPLEMENTING)
    ws = _ws(task)
    proposal = editor(task, ws, dict(context or {})) or {}
    written = []
    for change in proposal.get("files") or []:
        path = str(change.get("path") or "")
        # Every write is path-validated; a model cannot escape the workspace.
        info = ws.write(path, str(change.get("content") or ""))
        store.add_changed_file(task_id, info["path"])
        written.append(info)
    store.bump(task_id, "iterations")
    store.record_event(
        task_id,
        "implement",
        f"{len(written)} file(s): {proposal.get('summary', '')[:120]}",
        store.IMPLEMENTING,
    )
    return {"files_written": written, "summary": proposal.get("summary", "")}


def phase_test(task_id: str, test_cmd: list[str], *, cancel_check=None) -> dict[str, Any]:
    task = store.get(task_id)
    if not task:
        raise CodingAgentError(f"No such coding task: {task_id}")
    bound = _bounds_exhausted(task)
    if bound:
        return {"bounded": bound, "task": _stop_bounded(task_id, bound)}

    store.set_phase(task_id, store.TESTING)
    ws = _ws(task)
    result = commands.run(test_cmd, ws, cancel_check=cancel_check)
    store.bump(task_id, "test_runs")
    store.bump(task_id, "commands")
    if result.get("error_kind") == "cancelled":
        return {"cancelled": True, "result": result}
    summary = commands.parse_test_output(result["output"])
    store.update(
        task_id,
        last_test={**summary, "exit_code": result["exit_code"], "error": result.get("error")},
    )
    store.record_event(
        task_id,
        "test",
        f"{summary['passed']} passed, {summary['failed']} failed",
        store.TESTING,
    )
    return {"summary": summary, "command": result}


def phase_diagnose(task_id: str) -> dict[str, Any]:
    """Separate failures the agent caused from failures that were already there."""
    task = store.get(task_id)
    if not task:
        raise CodingAgentError(f"No such coding task: {task_id}")
    store.set_phase(task_id, store.DIAGNOSING)
    last = task.get("last_test") or {}
    failing = set(last.get("failing_tests") or [])
    baseline = set(task.get("baseline_failures") or [])
    caused = sorted(failing - baseline)
    pre_existing = sorted(failing & baseline)
    diagnosis = {
        "failing": sorted(failing),
        "caused_by_task": caused,
        "pre_existing": pre_existing,
        "verdict": "caused_by_task" if caused else ("pre_existing" if pre_existing else "clean"),
    }
    store.record_event(
        task_id,
        "diagnose",
        f"{len(caused)} caused, {len(pre_existing)} pre-existing",
        store.DIAGNOSING,
    )
    return diagnosis


def phase_review(task_id: str) -> dict[str, Any]:
    """Verify the diff, confirm unrelated work survived, and gate completion on tests."""
    task = store.get(task_id)
    if not task:
        raise CodingAgentError(f"No such coding task: {task_id}")
    store.set_phase(task_id, store.REVIEWING)
    ws = _ws(task)
    preserved = workspace.unrelated_changes_preserved(ws)
    diff = commands.run(["git", "diff"], ws)
    store.bump(task_id, "commands")

    last = task.get("last_test") or {}
    diagnosis = phase_diagnose(task_id) if last.get("failing_tests") else {"verdict": "clean"}
    store.set_phase(task_id, store.REVIEWING)

    review = {
        "files_changed": task["files_changed"],
        "unrelated_preserved": preserved["preserved"],
        "unrelated_lost": preserved["lost"],
        "tests": last,
        "diagnosis": diagnosis,
        "diff_chars": len(diff.get("output") or ""),
    }
    store.record_event(task_id, "review", f"{len(task['files_changed'])} file(s)", store.REVIEWING)
    return review


def complete(task_id: str, review: dict[str, Any]) -> dict[str, Any]:
    """Only a task with genuinely passing tests may complete."""
    task = store.get(task_id)
    if not task:
        raise CodingAgentError(f"No such coding task: {task_id}")
    tests = review.get("tests") or {}
    caused = (review.get("diagnosis") or {}).get("caused_by_task") or []

    if not tests:
        reason = "no tests were run"
        store.update(
            task_id, error=reason, stop_reason=reason, result={"review": review, "completed": False}
        )
        store.set_phase(task_id, store.FAILED, detail=reason)
        return store.get(task_id)  # type: ignore[return-value]
    if tests.get("exit_code") is None:
        reason = f"test command could not run ({tests.get('error') or 'runner unavailable'})"
        store.update(
            task_id, error=reason, stop_reason=reason, result={"review": review, "completed": False}
        )
        store.record_event(task_id, "completion:refused", reason, store.REVIEWING)
        store.set_phase(task_id, store.FAILED, detail=reason)
        return store.get(task_id)  # type: ignore[return-value]
    if not tests.get("green"):
        reason = "required tests did not pass"
        store.update(
            task_id, error=reason, stop_reason=reason, result={"review": review, "completed": False}
        )
        store.record_event(task_id, "completion:refused", reason, store.REVIEWING)
        store.set_phase(task_id, store.FAILED, detail=reason)
        return store.get(task_id)  # type: ignore[return-value]
    if caused:
        reason = f"task caused {len(caused)} test failure(s)"
        store.update(
            task_id, error=reason, stop_reason=reason, result={"review": review, "completed": False}
        )
        store.set_phase(task_id, store.FAILED, detail=reason)
        return store.get(task_id)  # type: ignore[return-value]
    if not review.get("unrelated_preserved", True):
        reason = f"unrelated user work was lost: {review.get('unrelated_lost')}"
        store.update(task_id, error=reason, stop_reason=reason)
        store.set_phase(task_id, store.FAILED, detail=reason)
        return store.get(task_id)  # type: ignore[return-value]

    store.update(task_id, result={"review": review, "completed": True})
    store.set_phase(task_id, store.COMPLETED, detail="tests passed, diff reviewed")
    store.release_lock(task["workspace"], task_id)
    return store.get(task_id)  # type: ignore[return-value]


def commit_task(task_id: str, message: str = "") -> dict[str, Any]:
    """Commit only this task's files, never a blanket commit of the tree."""
    task = store.get(task_id)
    if not task:
        raise CodingAgentError(f"No such coding task: {task_id}")
    files = task["files_changed"]
    if not files:
        return {"ok": False, "error": "no files to commit"}
    ws = _ws(task)
    add = commands.run(["git", "add", *files], ws)
    store.bump(task_id, "commands")
    if not add["ok"]:
        return {"ok": False, "error": add["error"], "output": add["output"]}
    msg = message or f"coding task {task_id}: {task['objective'][:60]}"
    done = commands.run(["git", "commit", "-m", msg], ws)
    store.bump(task_id, "commands")
    sha = workspace.head_commit(ws.root) if done["ok"] else ""
    if sha:
        store.update(task_id, commit_sha=sha)
    store.record_event(task_id, "commit", f"{len(files)} file(s) -> {sha[:10]}", task["phase"])
    return {"ok": done["ok"], "commit": sha, "files": files, "output": done["output"]}


def cancel(task_id: str) -> dict[str, Any]:
    task = store.get(task_id)
    if not task:
        raise CodingAgentError(f"No such coding task: {task_id}")
    if task["phase"] in store.TERMINAL:
        return task
    store.update(task_id, stop_reason="cancelled by request")
    store.set_phase(task_id, store.CANCELLED, detail="cancelled")
    store.release_lock(task["workspace"], task_id)
    return store.get(task_id)  # type: ignore[return-value]


def recover() -> list[str]:
    return store.recover_interrupted()


def run_loop(
    task_id: str,
    editor: Editor,
    test_cmd: list[str],
    *,
    max_iterations: int | None = None,
    cancel_check=None,
) -> dict[str, Any]:
    """The bounded development loop: implement → test → diagnose → fix → retest → review."""
    task = store.get(task_id)
    if not task:
        raise CodingAgentError(f"No such coding task: {task_id}")

    phase_plan(task_id)
    phase_inspect(task_id, test_cmd=test_cmd)

    limit = max_iterations or store.BOUNDS["max_iterations"]
    for _ in range(limit):
        if cancel_check is not None and cancel_check():
            return {"cancelled": True, "task": cancel(task_id)}

        implemented = phase_implement(task_id, editor)
        if implemented.get("bounded"):
            return implemented

        tested = phase_test(task_id, test_cmd, cancel_check=cancel_check)
        if tested.get("cancelled"):
            return {"cancelled": True, "task": cancel(task_id)}
        if tested.get("bounded"):
            return tested

        if tested["summary"]["green"]:
            review = phase_review(task_id)
            return {"task": complete(task_id, review), "review": review}

        diagnosis = phase_diagnose(task_id)
        # Keep iterating regardless of verdict: a "pre-existing" failure may be
        # exactly what this task was asked to fix, and bailing out here would
        # hand a red tree to complete(), which reports it as a task failure.
        # Completion is gated on genuinely green tests, so continuing cannot
        # manufacture a false success.
        detail = (
            f"{len(diagnosis['caused_by_task'])} caused, "
            f"{len(diagnosis['pre_existing'])} pre-existing"
        )
        store.set_phase(task_id, store.FIXING, detail=detail)

    reason = f"max_iterations ({limit}) without passing tests"
    return {"task": _stop_bounded(task_id, reason), "stop_reason": reason}


def status(task_id: str) -> dict[str, Any] | None:
    task = store.get(task_id)
    if not task:
        return None
    from jarvis import missions

    mission = missions.status(task["mission_id"]) if task.get("mission_id") else None
    return {
        "task_id": task["id"],
        "objective": task["objective"],
        "workspace": task["workspace"],
        "branch": task["branch"],
        "head_commit": task["head_commit"],
        "phase": task["phase"],
        "plan": task["plan"],
        "iterations": task["iterations"],
        "test_runs": task["test_runs"],
        "commands": task["commands"],
        "files_changed": task["files_changed"],
        "last_test": task["last_test"],
        "commit": task["commit_sha"],
        "model": task["model"],
        "error": task["error"],
        "stop_reason": task["stop_reason"],
        "bounds": dict(store.BOUNDS),
        "mission": mission,
        "result": task["result"],
        "elapsed_s": round(time.time() - task["created_at"], 1),
    }
