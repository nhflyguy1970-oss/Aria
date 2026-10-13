"""Owner-controlled task plans on the existing mission ledger.

This is operational context, not a second memory system. The mission remains
the source of truth for execution and checkpoints; ACM remains cognitive memory.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.missions import engine, store

APPROVAL_TTL_S = 24 * 3600
SAFE_INFO_ACTIONS = frozenset({
    "mission_status", "mission_list", "mission_worker_status",
    "workflow_status", "workflow_index", "research_status", "research_list",
    "research_report", "model_route", "model_health",
})
_SECRET_KEYS = frozenset({"password", "passwd", "secret", "token", "api_key", "credential"})


class TaskApprovalError(RuntimeError):
    pass


def _hash(objective: str, steps: list[dict[str, Any]], project: str) -> str:
    body = json.dumps({"objective": objective, "steps": steps, "project": project},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()


def _contains_secret(value: Any) -> bool:
    if isinstance(value, dict):
        return any(str(key).lower() in _SECRET_KEYS or _contains_secret(item)
                   for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_secret(item) for item in value)
    return False


def _auth(capability: str) -> None:
    from jarvis.security.owner.provider_credentials import bound_owner_service

    decision = bound_owner_service().authorize(capability, room="automation")
    if not decision.get("ok"):
        raise TaskApprovalError(decision.get("reason") or "owner authorization denied")


def _plan(mission_id: str) -> dict[str, Any] | None:
    store._init_db()
    with store._conn() as conn:
        row = conn.execute("SELECT * FROM agent_task_plans WHERE mission_id=?", (mission_id,)).fetchone()
    return dict(row) if row else None


def _artifact_paths(mission_id: str) -> tuple[Path, Path]:
    if not re.fullmatch(r"[0-9a-f]{12}", mission_id):
        raise ValueError("invalid task id")
    directory = DATA_DIR / "agent_task_artifacts" / mission_id
    return directory / "result.json", directory / "manifest.json"


def _atomic_bytes(path: Path, payload: bytes) -> None:
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        os.replace(tmp, path)
        directory_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def save_artifact(mission: dict[str, Any]) -> None:
    """Publish a completed result once, atomically, without overwriting history."""
    if mission["kind"] != "agent_task" or mission["state"] != store.COMPLETED:
        return
    result_path, manifest_path = _artifact_paths(mission["id"])
    result_path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps({"task_id": mission["id"], "objective": mission["objective"],
                           "result": mission["result"], "completed_at": mission["finished_at"]},
                          indent=2, sort_keys=True) + "\n").encode()
    digest = hashlib.sha256(payload).hexdigest()
    if result_path.exists():
        if hashlib.sha256(result_path.read_bytes()).hexdigest() != digest:
            raise RuntimeError("existing task artifact differs; refusing overwrite")
    else:
        _atomic_bytes(result_path, payload)
    manifest = {"sha256": digest, "bytes": len(payload), "task_id": mission["id"]}
    manifest_payload = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    if manifest_path.exists() and manifest_path.read_bytes() != manifest_payload:
        raise RuntimeError("existing task manifest differs; refusing overwrite")
    if not manifest_path.exists():
        _atomic_bytes(manifest_path, manifest_payload)


def artifact_path(mission_id: str) -> Path | None:
    result_path, manifest_path = _artifact_paths(mission_id)
    if not result_path.exists() or not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if hashlib.sha256(result_path.read_bytes()).hexdigest() != manifest.get("sha256"):
        raise RuntimeError("task artifact hash mismatch")
    return result_path


def propose_steps(objective: str) -> list[dict[str, Any]]:
    """Use the existing specialist composer; its proposal has no authority."""
    from jarvis.specialists.composer import compose_team

    team = compose_team(objective, use_llm=False)["team"]
    return [
        {"name": "Review specialist plan", "action": "specialists_propose",
         "params": {"goal": objective, "specialists": team}},
        {"name": "Run bounded specialists and self-check", "action": "specialists_run",
         "params": {"goal": objective, "specialists": team, "confirm": True,
                    "approve_writes": False, "parallel_readers": False, "critic_loop": True}},
    ]


def _ordered_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reuse the workflow dependency graph when a task has explicit edges."""
    if any(not isinstance(step, dict) for step in steps):
        raise ValueError("task steps must be objects")
    if not any(step.get("depends_on") for step in steps):
        return steps
    from jarvis.autonomous_workflows.definitions import WorkflowDefinition
    from jarvis.autonomous_workflows.graph import topological_order, validate_graph

    normalized = [{**step, "step_id": str(step.get("step_id") or f"step_{i}")}
                  for i, step in enumerate(steps)]
    definition = WorkflowDefinition.from_dict({"name": "task dependencies", "steps": normalized})
    report = validate_graph(definition)
    if not report["ok"]:
        raise ValueError("; ".join(report["problems"]))
    by_id = {step["step_id"]: step for step in normalized}
    return [by_id[step_id] for step_id in topological_order(definition)]


def create(objective: str, steps: list[dict[str, Any]] | None = None, *, project: str = "general",
           session_ref: str = "", scheduled_at: float | None = None) -> dict[str, Any]:
    """Create a non-runnable proposal; model output can never approve itself."""
    from jarvis.integration import policy

    objective = objective.strip()
    if len(objective) > 2000:
        raise ValueError("task objective is too long")
    project = project.strip().lower()
    if not objective or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", project):
        raise ValueError("objective and valid project are required")
    if steps is None:
        steps = propose_steps(objective)
    if not isinstance(steps, list) or not 1 <= len(steps) <= policy.bounds_for()["max_steps"]:
        raise ValueError("task needs a bounded nonempty step list")
    steps = _ordered_steps(steps)
    if scheduled_at is not None and (scheduled_at < time.time() or scheduled_at > time.time() + 365 * 86400):
        raise ValueError("scheduled time must be within the next year")
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import get_spec

    ensure_handlers_loaded()
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or not isinstance(step.get("params", {}), dict):
            raise ValueError(f"step {index} must have object params")
        if _contains_secret(step.get("params") or {}):
            raise ValueError("task steps must reference vault capabilities, not contain credentials")
        action = str(step.get("action") or "")
        spec = get_spec(action)
        if not spec or not spec.handler:
            raise ValueError(f"step {index} has no registered executable action")
    mission_id = engine.create_mission(objective, steps, kind="agent_task", start_paused=True)
    now = time.time()
    with store._conn() as conn:
        conn.execute("""INSERT INTO agent_task_plans
            (mission_id,project,session_ref,plan_hash,approval_state,approval_expires_at,scheduled_at,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (mission_id, project, session_ref[:200], _hash(objective, steps, project),
             "proposed", now + APPROVAL_TTL_S, scheduled_at, now, now))
    store.record_event(mission_id, "approval:proposed", "exact task plan awaiting owner approval")
    return status(mission_id)  # type: ignore[return-value]


def status(mission_id: str) -> dict[str, Any] | None:
    plan = _plan(mission_id)
    mission = engine.status(mission_id)
    if not plan or not mission:
        return None
    approval = plan["approval_state"]
    if approval == "proposed" and time.time() > plan["approval_expires_at"]:
        approval = "expired"
    mission.update({
        "project": plan["project"], "session_ref": plan["session_ref"],
        "plan_hash": plan["plan_hash"], "approval": approval,
        "approval_expires_at": plan["approval_expires_at"],
        "scheduled_at": plan["scheduled_at"],
        "steps": (store.get(mission_id) or {}).get("steps", []),
        "current_step": [] if mission["state"] in store.TERMINAL_STATES else
        (store.get(mission_id) or {}).get("steps", [])[mission["progress"]["completed_steps"]:mission["progress"]["completed_steps"] + 1],
    })
    result_path, manifest_path = _artifact_paths(mission_id)
    if result_path.exists() and manifest_path.exists():
        mission["artifact_url"] = f"/api/agent-tasks/{mission_id}/artifact"
    events = store.history(mission_id)
    mission["status_message"] = events[-1]["detail"] if events else ""
    elapsed_end = mission.get("updated_at") if mission["state"] in store.TERMINAL_STATES else time.time()
    mission["elapsed_seconds"] = round((elapsed_end or time.time()) -
                                       (mission.get("created_at") or time.time()), 1)
    if mission["state"] == store.PENDING and plan["scheduled_at"] and plan["scheduled_at"] > time.time():
        mission["display_state"] = "scheduled"
    elif mission["state"] == store.PAUSED and (approval == "proposed" or mission.get("error_kind") == "awaiting_approval"):
        mission["display_state"] = "awaiting_approval"
    else:
        mission["display_state"] = mission["state"]
    return mission


def list_tasks(*, project: str = "", query: str = "", limit: int = 100) -> list[dict[str, Any]]:
    store._init_db()
    with store._conn() as conn:
        rows = conn.execute("""SELECT p.mission_id FROM agent_task_plans p JOIN missions m ON m.id=p.mission_id
            WHERE (?='' OR p.project=?) AND (?='' OR m.objective LIKE ?)
            ORDER BY m.updated_at DESC LIMIT ?""",
            (project, project, query, f"%{query}%", max(1, min(limit, 500)))).fetchall()
    return [item for row in rows if (item := status(row["mission_id"]))]


def approve(mission_id: str) -> dict[str, Any]:
    _auth("automation.modify")  # fresh owner step-up, checked again at execution
    plan = _plan(mission_id)
    mission = store.get(mission_id)
    if not plan or not mission or plan["approval_state"] != "proposed" or mission["state"] != store.PAUSED:
        raise TaskApprovalError("no pending task approval")
    if time.time() > plan["approval_expires_at"]:
        raise TaskApprovalError("task approval request expired")
    if plan["plan_hash"] != _hash(mission["objective"], mission["steps"], plan["project"]):
        raise TaskApprovalError("task plan changed after proposal")
    with store._conn() as conn:
        changed = conn.execute("""UPDATE agent_task_plans SET approval_state='approved',approved_at=?,updated_at=?
            WHERE mission_id=? AND approval_state='proposed'""",
            (time.time(), time.time(), mission_id)).rowcount
    if changed != 1:
        raise TaskApprovalError("task approval was consumed")
    store.record_event(mission_id, "approval:approved", "owner approved exact plan hash")
    store.clear_pause(mission_id)
    store.make_runnable(mission_id, detail="approved task queued")
    from jarvis.missions import worker
    worker.wake()
    return status(mission_id)  # type: ignore[return-value]


def deny(mission_id: str) -> dict[str, Any]:
    _auth("automation.read")
    plan = _plan(mission_id)
    if not plan or plan["approval_state"] != "proposed":
        raise TaskApprovalError("no pending task approval")
    with store._conn() as conn:
        conn.execute("UPDATE agent_task_plans SET approval_state='denied',updated_at=? WHERE mission_id=?",
                     (time.time(), mission_id))
    store.request_cancel(mission_id)
    store.record_event(mission_id, "approval:denied", "owner denied plan")
    return status(mission_id)  # type: ignore[return-value]


def authorize_step(mission: dict[str, Any], step_index: int) -> None:
    """Execution boundary: persisted approval, exact plan, then fresh authority."""
    from jarvis.integration import policy

    plan = _plan(mission["id"])
    if not plan or plan["approval_state"] != "approved":
        raise TaskApprovalError("task has no approved plan")
    if plan["plan_hash"] != _hash(mission["objective"], mission["steps"], plan["project"]):
        raise TaskApprovalError("approved task plan hash no longer matches")
    if step_index >= policy.bounds_for()["max_steps"]:
        raise TaskApprovalError("autonomy step budget exhausted")
    started = mission.get("started_at")
    if started and time.time() - started >= policy.bounds_for()["max_runtime_s"]:
        raise TaskApprovalError("autonomy runtime budget exhausted")
    action = mission["steps"][step_index].get("action")
    if action not in SAFE_INFO_ACTIONS:
        _auth("automation.modify")


def pause(mission_id: str) -> dict[str, Any]:
    _auth("automation.read")
    if not _plan(mission_id):
        raise TaskApprovalError("no such task")
    engine.pause(mission_id)
    return status(mission_id)  # type: ignore[return-value]


def resume(mission_id: str) -> dict[str, Any]:
    _auth("automation.read")
    plan = _plan(mission_id)
    mission = store.get(mission_id)
    if not plan or not mission or plan["approval_state"] != "approved":
        raise TaskApprovalError("task is not approved")
    if mission.get("error_kind") == "uncertain_effect":
        raise TaskApprovalError("reconcile the uncertain operation first")
    if mission["state"] != store.PAUSED:
        raise TaskApprovalError("task is not paused")
    store.clear_pause(mission_id)
    store.make_runnable(mission_id, detail="owner resumed task")
    from jarvis.missions import worker
    worker.wake()
    return status(mission_id)  # type: ignore[return-value]


def cancel(mission_id: str) -> dict[str, Any]:
    _auth("automation.read")
    if not _plan(mission_id):
        raise TaskApprovalError("no such task")
    if not engine.cancel(mission_id):
        raise TaskApprovalError("task already finished; nothing to cancel")
    return status(mission_id)  # type: ignore[return-value]


def redirect(mission_id: str, *, objective: str, steps: list[dict[str, Any]]) -> dict[str, Any]:
    _auth("automation.modify")
    mission = store.get(mission_id)
    plan = _plan(mission_id)
    if not mission or not plan or mission["state"] != store.PAUSED:
        raise TaskApprovalError("pause the task at a step boundary before redirecting")
    if mission.get("error_kind") == "uncertain_effect":
        raise TaskApprovalError("reconcile the in-flight operation before redirecting")
    completed = mission["completed_steps"]
    if steps[:completed] != mission["steps"][:completed]:
        raise TaskApprovalError("completed steps are immutable")
    if len(steps) <= completed:
        raise TaskApprovalError("redirect needs unfinished work")
    from jarvis.integration import policy
    if len(steps) > policy.bounds_for()["max_steps"]:
        raise TaskApprovalError("redirect exceeds autonomy step budget")
    objective = objective.strip()
    if not objective:
        raise TaskApprovalError("redirect needs a goal")
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import get_spec
    ensure_handlers_loaded()
    if any(not isinstance(s, dict) or not (get_spec(s.get("action") or "") and get_spec(s.get("action") or "").handler)
           for s in steps[completed:]):
        raise TaskApprovalError("redirect contains an unknown action")
    if any(_contains_secret(s.get("params") or {}) for s in steps[completed:]):
        raise TaskApprovalError("redirect steps may not contain credentials")
    new_hash = _hash(objective, steps, plan["project"])
    with store._conn() as conn:
        conn.execute("UPDATE missions SET objective=?,steps=?,total_steps=?,updated_at=? WHERE id=? AND state=?",
                     (objective[:2000], json.dumps(steps), len(steps), time.time(), mission_id, store.PAUSED))
        conn.execute("""UPDATE agent_task_plans SET plan_hash=?,approval_state='proposed',
            approval_expires_at=?,approved_at=NULL,updated_at=? WHERE mission_id=?""",
            (new_hash, time.time() + APPROVAL_TTL_S, time.time(), mission_id))
    store.record_event(mission_id, "task:redirected", "owner changed goal; new exact-plan approval required")
    return status(mission_id)  # type: ignore[return-value]
