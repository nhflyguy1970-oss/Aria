"""Plans, approvals and supervised runs of coding agents.

Lifecycle::

    plan (proposed) --owner approves--> approved --execute--> consumed
                                                     |
                                       mission (kind coding_agent) -> run

* A plan is what the owner sees and approves: agent, project, mode, task,
  time limit. Its hash is fixed at creation; approval is single-use, expires,
  and carries a nonce that only the owner's confirmation path holds, so a
  router guess, an agent's output or a replayed request cannot start work.
* Execution goes through the mission engine, so Phase 1's execution policy
  (safe mode, autonomy level) is checked on the one path every run takes,
  and a mission checkpoint plus ``runs.plan_id UNIQUE`` make a second
  execution of the same approval impossible.
* A run that ARIA loses track of (restart) becomes ``interrupted`` and is
  never re-run automatically.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import signal
import sqlite3
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.coding_agents import adapters, boundary, contract, discovery, workspace
from jarvis.config import DATA_DIR

DB_PATH = DATA_DIR / "coding_agents.db"
APPROVAL_TTL_S = 30 * 60
DEFAULT_TIMEOUT_S = 900
MAX_OUTPUT_BYTES = 4_000_000
MAX_EVENTS = 300
MAX_DELEGATION_DEPTH = 1
MAX_CONCURRENT = 1

PROPOSED, APPROVED, REJECTED, CONSUMED, EXPIRED = "proposed", "approved", "rejected", "consumed", "expired"
PENDING, RUNNING = "pending", "running"

_lock = threading.Lock()
_procs: dict[str, subprocess.Popen] = {}
_containers: dict[str, str] = {}
_container_lock = threading.Lock()
_owned: set[str] = set()  # runs this ARIA process started and is still supervising


class AgentRunError(RuntimeError):
    pass


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY, created_at REAL, agent TEXT, project TEXT, mode TEXT,
            task TEXT, timeout_s INTEGER, plan_hash TEXT, status TEXT, nonce TEXT,
            approved_at REAL, approved_via TEXT, expires_at REAL, parent_run TEXT,
            depth INTEGER DEFAULT 0, source TEXT, rationale TEXT, project_scope TEXT
        );
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY, plan_id TEXT UNIQUE, mission_id TEXT, agent TEXT, project TEXT,
            mode TEXT, task TEXT, status TEXT, pid INTEGER, owner_pid INTEGER, started_at REAL,
            finished_at REAL, exit_code INTEGER, workspace TEXT, base_commit TEXT,
            cancel_requested INTEGER DEFAULT 0, result TEXT, receipt TEXT
        );
        CREATE TABLE IF NOT EXISTS events (
            run_id TEXT, ts REAL, kind TEXT, detail TEXT
        );
        """
    )
    if "project_scope" not in {r[1] for r in conn.execute("PRAGMA table_info(plans)")}:
        # Existing approvals have no reviewed scope. Preserve them as history,
        # but require a new proposal rather than retroactively granting scope.
        try:
            conn.execute("ALTER TABLE plans ADD COLUMN project_scope TEXT")
        except sqlite3.OperationalError:
            # Another controller can migrate the legacy database concurrently.
            # Accept only a completed migration, never a missing scope column.
            if "project_scope" not in {r[1] for r in conn.execute("PRAGMA table_info(plans)")}:
                conn.close()
                raise
    if "resume_run" not in {r[1] for r in conn.execute("PRAGMA table_info(plans)")}:
        try:conn.execute("ALTER TABLE plans ADD COLUMN resume_run TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            if "resume_run" not in {r[1] for r in conn.execute("PRAGMA table_info(plans)")}:
                conn.close();raise
    return conn


# ---------------------------------------------------------------- plans


def _project_scope(project: str, resume_run: str = "") -> str:
    from jarvis.coding_agents import projects

    record = projects.get(project)
    if not record:
        raise AgentRunError(f"project {project!r} is not registered")
    scope = {
        "path": str(Path(record["path"]).expanduser().resolve()),
        "test_command": record.get("test_command") or "",
        "protected_paths": record.get("protected_paths") or [],
        "allowed_agents": record.get("allowed_agents") or [],
    }
    if resume_run:
        from jarvis.coding_agents.sessions import resume_scope
        try:scope['resume'] = resume_scope(get_run(resume_run) or {})
        except workspace.WorkspaceError as exc:raise AgentRunError(str(exc)) from exc
    return json.dumps(scope, sort_keys=True)


def _check_project_scope(plan) -> None:
    if not plan["project_scope"] or plan["project_scope"] != _project_scope(plan["project"], dict(plan).get("resume_run") or ""):
        raise AgentRunError("project scope changed or was not reviewed; propose the plan again")


def _hash(agent: str, project: str, mode: str, task: str, timeout_s: int, project_scope=None) -> str:
    return hashlib.sha256(json.dumps([agent, project, mode, task, timeout_s, project_scope]).encode()).hexdigest()[:16]


def create_plan(*, agent: str, project: str, mode: str, task: str, timeout_s: int = DEFAULT_TIMEOUT_S,
                source: str = "chat", rationale: str = "", parent_run: str = "", resume_run: str = "") -> dict[str, Any]:
    from jarvis.integration import policy

    if mode not in (discovery.READ_ONLY, discovery.WORKSPACE_WRITE):
        raise AgentRunError(f"unknown mode {mode!r}")
    ceiling = int(policy.bounds_for().get("max_runtime_s") or DEFAULT_TIMEOUT_S)
    timeout_s = max(30, min(int(timeout_s or DEFAULT_TIMEOUT_S), ceiling))
    task = task.strip()[:4000]
    if not task:raise AgentRunError("a coding task is required")
    depth = 0
    if parent_run:
        parent = get_run(parent_run)
        parent_plan = get_plan(parent["plan_id"]) if parent else None
        depth = int((parent_plan or {}).get("depth") or 0) + 1
        if depth > MAX_DELEGATION_DEPTH:
            raise AgentRunError("delegation depth limit reached: an agent's recommendation cannot start another chain")
    pid = "plan_" + uuid.uuid4().hex[:10]
    project_scope = _project_scope(project, resume_run)
    if resume_run:
        previous = get_run(resume_run)
        if agent != 'codex' or previous['agent'] != agent or previous['project'] != project or previous['mode'] != mode:
            raise AgentRunError('continuation cannot change the agent, project or permission mode')
    row = {
        "id": pid, "created_at": time.time(), "agent": agent, "project": project, "mode": mode,
        "task": task.strip()[:4000], "timeout_s": timeout_s,
        "project_scope": project_scope,
        "plan_hash": _hash(agent, project, mode, task, timeout_s, project_scope),
        "status": PROPOSED, "nonce": secrets.token_urlsafe(16), "approved_at": None, "approved_via": "",
        "expires_at": None, "parent_run": parent_run, "depth": depth, "source": source, "rationale": rationale[:500], "resume_run": resume_run,
    }
    with _lock, _conn() as conn:
        conn.execute(f"INSERT INTO plans ({','.join(row)}) VALUES ({','.join('?' * len(row))})", tuple(row.values()))
    _continuity_plan(row)
    return public_plan(row)


def create_resume_plan(run_id: str, *, task: str, timeout_s: int = DEFAULT_TIMEOUT_S) -> dict:
    previous = get_run(run_id)
    if not previous:
        raise AgentRunError("no such run")
    return create_plan(
        agent=previous["agent"],
        project=previous["project"],
        mode=previous["mode"],
        task=task,
        timeout_s=timeout_s,
        resume_run=run_id,
        source="owner_continuation",
        rationale="Continue the recorded private Codex session and workspace; fresh owner approval required.",
    )


def get_plan(plan_id: str, *, with_nonce: bool = False) -> dict[str, Any] | None:
    with _conn() as conn:
        r = conn.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    return d if with_nonce else public_plan(d)


def public_plan(row: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in row.items() if k != "nonce"}


def approval_token(plan_id: str) -> str:
    """The nonce, for the owner-confirmation path only (pending chat choice / owner API)."""
    plan = get_plan(plan_id, with_nonce=True)
    return str(plan["nonce"]) if plan else ""


def approve(plan_id: str, *, token: str, via: str) -> dict[str, Any]:
    plan = get_plan(plan_id, with_nonce=True)
    if not plan:
        raise AgentRunError("no such plan")
    if not token or not secrets.compare_digest(str(plan["nonce"]), str(token)):
        raise AgentRunError("approval refused: missing or wrong approval token")
    if plan["status"] != PROPOSED:
        raise AgentRunError(f"plan is {plan['status']}, not awaiting approval")
    if plan["plan_hash"] != _hash(plan["agent"], plan["project"], plan["mode"], plan["task"], plan["timeout_s"], plan["project_scope"]):
        raise AgentRunError("plan changed after it was proposed")
    _check_project_scope(plan)
    now = time.time()
    with _lock, _conn() as conn:
        cur = conn.execute(
            "UPDATE plans SET status=?, approved_at=?, approved_via=?, expires_at=? WHERE id=? AND status=?",
            (APPROVED, now, via, now + APPROVAL_TTL_S, plan_id, PROPOSED),
        )
        if cur.rowcount != 1:
            raise AgentRunError("plan was approved or changed concurrently")
    _continuity_update(f"coding_plan:{plan_id}", "accepted")
    return get_plan(plan_id) or {}


def reject(plan_id: str, *, via: str = "chat") -> None:
    with _lock, _conn() as conn:
        conn.execute("UPDATE plans SET status=?, approved_via=? WHERE id=? AND status IN (?,?)",
                     (REJECTED, via, plan_id, PROPOSED, APPROVED))
    _continuity_update(f"coding_plan:{plan_id}", "rejected")


def _consume(plan_id: str, *, run_id: str = "") -> dict[str, Any]:
    now = time.time()
    with _lock, _conn() as conn:
        plan = conn.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
        if plan and plan["plan_hash"] != _hash(plan["agent"], plan["project"], plan["mode"], plan["task"], plan["timeout_s"], plan["project_scope"]):
            raise AgentRunError("plan changed after approval")
        if plan:
            _check_project_scope(plan)
        cur = conn.execute(
            "UPDATE plans SET status=? WHERE id=? AND status=? AND expires_at>?",
            (CONSUMED, plan_id, APPROVED, now),
        )
        if cur.rowcount != 1:
            r = conn.execute("SELECT status, expires_at FROM plans WHERE id=?", (plan_id,)).fetchone()
            if r and r["status"] == APPROVED:
                conn.execute("UPDATE plans SET status=? WHERE id=?", (EXPIRED, plan_id))
                raise AgentRunError("approval expired; propose the plan again")
            raise AgentRunError(f"plan is not approved (status: {r['status'] if r else 'missing'})")
        if run_id:
            # Approval consumption and durable launch intent are one commit.
            # A crash cannot strand a consumed approval without its run record.
            from jarvis.coding_agents.sessions import process_identity
            conn.execute(
                "INSERT INTO runs (id, plan_id, agent, project, mode, task, status, owner_pid, started_at, receipt) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (run_id, plan_id, plan["agent"], plan["project"], plan["mode"], plan["task"], PENDING,
                 os.getpid(), now, json.dumps({"owner_identity": process_identity(os.getpid())})),
            )
    return get_plan(plan_id) or {}


# ---------------------------------------------------------------- runs


def get_run(run_id: str) -> dict[str, Any] | None:
    with _conn() as conn:
        r = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    for k in ("result", "receipt"):
        d[k] = json.loads(d[k]) if d.get(k) else {}
    return d


def run_for_plan(plan_id: str) -> dict[str, Any] | None:
    with _conn() as conn:
        r = conn.execute("SELECT id FROM runs WHERE plan_id=?", (plan_id,)).fetchone()
    return get_run(r["id"]) if r else None


def list_runs(*, since: float = 0.0, project: str = "", limit: int = 50) -> list[dict[str, Any]]:
    recover_interrupted()
    q, args = "SELECT id FROM runs WHERE COALESCE(started_at,0)>=?", [since]
    if project:
        q += " AND project=?"
        args.append(project)
    q += " ORDER BY started_at DESC LIMIT ?"
    args.append(limit)
    with _conn() as conn:
        ids = [r["id"] for r in conn.execute(q, args).fetchall()]
    return [r for r in (get_run(i) for i in ids) if r]


def events(run_id: str, limit: int = 100) -> list[dict[str, Any]]:
    with _conn() as conn:
        rows = conn.execute("SELECT ts, kind, detail FROM events WHERE run_id=? ORDER BY ts DESC LIMIT ?",
                            (run_id, limit)).fetchall()
    return [dict(r) for r in reversed(rows)]


def _event(run_id: str, kind: str, detail: str = "") -> None:
    with _conn() as conn:
        n = conn.execute("SELECT COUNT(*) FROM events WHERE run_id=?", (run_id,)).fetchone()[0]
        if n < MAX_EVENTS or kind in ("finished", "error", "cancel", "timeout"):
            conn.execute("INSERT INTO events VALUES (?,?,?,?)", (run_id, time.time(), kind, detail[:500]))


def _update(run_id: str, **fields: Any) -> None:
    for k in ("result", "receipt"):
        if k in fields and not isinstance(fields[k], str):
            fields[k] = json.dumps(fields[k], default=str)
    with _conn() as conn:
        conn.execute(f"UPDATE runs SET {', '.join(f'{k}=?' for k in fields)} WHERE id=?", (*fields.values(), run_id))


def _alive(pid: int) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def recover_interrupted() -> list[str]:
    """Runs left 'running' by a previous ARIA process are interrupted — not resumed."""
    lost = []
    with _conn() as conn:
        rows = conn.execute("SELECT id, owner_pid, pid FROM runs WHERE status IN (?,?)", (PENDING, RUNNING)).fetchall()
    for r in rows:
        if r["id"] in _owned:
            continue  # supervised by a live thread in this process
        from jarvis.coding_agents.sessions import process_identity
        prior = get_run(r['id']) or {}
        identity = (prior.get('receipt') or {}).get('owner_identity')
        owner_alive = (process_identity(r['owner_pid']) == identity) if identity else _alive(r['owner_pid'])
        if not owner_alive:
            prior = get_run(r["id"]) or {}
            cid = (prior.get("receipt") or {}).get("container_id")
            if cid:
                from jarvis.coding_agents import oci
                try:
                    oci.remove(cid, r["id"])
                except Exception as exc:
                    _event(r["id"], "error", f"interrupted container cleanup failed: {exc}")
                    continue  # fail closed: retain the concurrency reservation
            receipt = prior.get('receipt') or {}
            if prior.get('workspace'):
                try:receipt['workspace_snapshot'] = workspace.snapshot(prior['workspace'])
                except workspace.WorkspaceError as exc:
                    _event(r['id'], 'error', f'restart workspace inspection failed: {exc}')
                    continue
            _update(r["id"], receipt=receipt, status=contract.INTERRUPTED, finished_at=time.time(),
                    result={"status": contract.INTERRUPTED, "success": False,
                            "reason": "ARIA stopped while this run was in progress; it was not re-run",
                            "verified": [], "unverified": []})
            _event(r["id"], "error", "interrupted by ARIA restart")
            lost.append(r["id"])
    return lost


def start(plan_id: str, *, token: str = "", via: str = "", background: bool = True,
          assistant: Any = None) -> dict[str, Any]:
    """Approve (if a token is given) and launch a plan as a coding-agent mission."""
    from jarvis.integration import policy
    from jarvis.missions import engine

    existing = run_for_plan(plan_id)
    if existing:
        return existing  # one approval, one execution
    for cap in ("mission", "coding"):
        reason = policy.refusal(cap)
        if reason:
            raise AgentRunError(reason)
    if token:
        plan = get_plan(plan_id)
        if plan and plan["status"] == PROPOSED:
            approve(plan_id, token=token, via=via or "chat_confirmation")
    reserved = _reserve_run(plan_id, engine)
    if reserved.get("existing"):
        return reserved["existing"]
    run_id, mission_id = reserved["run_id"], reserved["mission_id"]

    def _go() -> None:
        try:
            outcome = engine.run(mission_id, runner=lambda step, ctx: execute_step(step["params"]["run_id"]))
            # The mission engine persists step exceptions and returns instead
            # of raising. Do not strand the agent run or erase its evidence.
            run = get_run(run_id)
            if run and run["status"] in (PENDING, RUNNING):
                state = (outcome or {}).get("state")
                _finish(run_id, {"status": contract.CANCELLED if state == "cancelled" else contract.FAILED,
                                 "success": False, "reason": f"supervising mission ended {state}: "
                                 + str((outcome or {}).get("last_error") or (outcome or {}).get("error") or "step did not finish"),
                                 "verified": [], "unverified": []}, receipt=run.get("receipt") or {})
        except Exception as exc:  # noqa: BLE001 — recorded on the run
            run = get_run(run_id)
            if run and run["status"] in (PENDING, RUNNING):
                _finish(run_id, {"status": contract.REFUSED if "policy" in type(exc).__name__.lower() else contract.FAILED,
                                 "success": False, "reason": f"{type(exc).__name__}: {exc}",
                                 "verified": [], "unverified": []}, receipt=run.get("receipt") or {})
        finally:
            try:
                _stop_container(run_id)
            except Exception as exc:
                current = get_run(run_id) or {}
                receipt = current.get("receipt") or {}
                receipt["cleanup_error"] = str(exc)
                _update(run_id, status=RUNNING, receipt=receipt)
                _event(run_id, "error", "container cleanup failed; further execution remains blocked")
            _owned.discard(run_id)

    if background:
        threading.Thread(target=_go, name=f"coding-agent-{run_id}", daemon=True).start()
    else:
        _go()
    return get_run(run_id) or {}


def _reserve_run(plan_id: str, engine) -> dict[str, Any]:
    """Serialize launch reservations across threads and ARIA processes."""
    import fcntl

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH.with_suffix(".launch.lock"), "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise AgentRunError("another coding-agent run is in progress") from exc
        existing = run_for_plan(plan_id)
        if existing:
            return {"existing": existing}
        recover_interrupted()
        with _conn() as conn:
            active = conn.execute("SELECT COUNT(*) FROM runs WHERE status IN (?,?)", (PENDING, RUNNING)).fetchone()[0]
        if active >= MAX_CONCURRENT:
            raise AgentRunError("another coding-agent run is in progress; wait for it or cancel it")
        run_id = "run_" + uuid.uuid4().hex[:10]
        plan = _consume(plan_id, run_id=run_id)
        try:
            mission_id = engine.create_mission(
                f"[{plan['agent']}] {plan['task'][:120]}",
                steps=[{"name": "coding agent run", "action": "coding_agent_run_step", "params": {"run_id": run_id}}],
                kind="coding_agent",
            )
        except Exception as exc:
            _finish(run_id, {'status': contract.FAILED, 'success': False,
                'reason': 'mission reservation failed: ' + str(exc), 'verified': [], 'unverified': []},
                receipt=(get_run(run_id) or {}).get('receipt') or {})
            raise AgentRunError('mission reservation failed; approval is consumed and the failure is recorded') from exc
        _update(run_id, mission_id=mission_id)
        _event(run_id, "queued", f"mission {mission_id}")
        _owned.add(run_id)
        return {"run_id": run_id, "mission_id": mission_id}


def cancel(run_id: str) -> dict[str, Any]:
    run = get_run(run_id)
    if not run:
        raise AgentRunError("no such run")
    if run['status'] in contract.TERMINAL:
        return run
    with _conn() as conn:
        changed = conn.execute(
            "UPDATE runs SET cancel_requested=1 WHERE id=? AND status IN (?,?)",
            (run_id, PENDING, RUNNING),
        ).rowcount
    if not changed:
        return get_run(run_id) or {}
    _event(run_id, "cancel", "owner requested cancellation")
    if run.get("mission_id"):
        try:
            from jarvis.missions import store as mission_store

            mission_store.request_cancel(run["mission_id"])
        except Exception:
            pass
    _stop_container(run_id)
    proc = _procs.get(run_id)
    if proc and proc.poll() is None:
        _kill(proc)
    return get_run(run_id) or {}


def _stop_container(run_id: str) -> None:
    with _container_lock:
        cid = _containers.get(run_id)
        if cid:
            from jarvis.coding_agents import oci
            oci.remove(cid, run_id)
            _containers.pop(run_id, None)


def _kill(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except OSError:
        return
    try:
        # bwrap does not exit on SIGTERM; --die-with-parent takes the agent down with it.
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass


def execute_step(run_id: str) -> dict[str, Any]:
    """Mission step: run the agent once. Idempotent — a finished run is returned, not repeated."""
    run = get_run(run_id)
    if not run:
        return {"ok": False, "error": "no such run"}
    if run["status"] in contract.TERMINAL:
        return {"ok": bool(run["result"].get("success")), "run_id": run_id, "status": run["status"]}
    if run["status"] == RUNNING:
        return {"ok": False, "error": "run already in progress", "run_id": run_id}
    result = _execute(run)
    return {"ok": bool(result.get("success")), "run_id": run_id, "status": result.get("status"),
            "message": result.get("reason", "")}


def _execute(run: dict[str, Any]) -> dict[str, Any]:
    from jarvis.coding_agents import projects
    from jarvis.integration import policy
    from jarvis.security.owner.env_boundary import build_subprocess_env

    run_id = run["id"]
    plan = get_plan(run["plan_id"]) or {}
    receipt: dict[str, Any] = {**(run.get("receipt") or {}), "plan_id": run["plan_id"], "plan_hash": plan.get("plan_hash"),
                               "approved_via": plan.get("approved_via"), "mission_id": run.get("mission_id")}
    _update(run_id, receipt=receipt)

    def refuse(reason: str) -> dict[str, Any]:
        return _finish(run_id, {"status": contract.REFUSED, "success": False, "reason": reason,
                                "verified": [], "unverified": []}, receipt=receipt)

    if run.get('cancel_requested'):
        return _finish(run_id, {'status': contract.CANCELLED, 'success': False,
            'reason': 'cancelled before launch', 'verified': [], 'unverified': []}, receipt=receipt)
    for cap in ("mission", "coding"):
        if reason := policy.refusal(cap):
            return refuse(reason)
    status = discovery.discover().get(run["agent"])
    if status:
        from jarvis.coding_agents import runtime
        status.execution = runtime.compatibility(status.agent, status.path, status.version)
    if not status or not status.usable:
        return refuse(f"{run['agent']} is not usable: {(status.notes if status else ['unknown agent'])}")
    if run["mode"] not in status.modes:
        return refuse(f"{run['agent']} does not support {run['mode']}")
    proj = projects.get(run["project"])
    if not proj:
        return refuse(f"project {run['project']!r} is not registered")
    try:
        _check_project_scope(plan)
    except AgentRunError as exc:
        return refuse(str(exc))
    approved_scope = json.loads(plan["project_scope"])
    receipt["project_scope"] = approved_scope
    allowed = ((proj.get("agent_settings") or {}).get("allowed_agents") or proj.get("allowed_agents") or [])
    if allowed and run["agent"] not in allowed:
        return refuse(f"{run['agent']} is not allowed for this project")
    receipt.update(agent_version=status.version, auth_method=status.auth.get("method"),
                   billing=status.auth.get("billing"), project_path=proj["path"])
    _update(run_id, receipt=receipt)

    try:
        resumed = approved_scope.get('resume')
        ws = ({'workspace': resumed['workspace'], 'base_commit': resumed['base_commit'],
               'source_uncommitted_changes': True} if resumed else workspace.prepare(approved_scope["path"], run_id))
    except (workspace.WorkspaceError, subprocess.TimeoutExpired) as exc:
        return refuse(f"workspace: {exc}")
    out_dir = Path(ws["workspace"]).parent / f"run-{run_id}.out"
    out_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    receipt.update(workspace=ws["workspace"], base_commit=ws["base_commit"],
                   source_uncommitted_changes=ws["source_uncommitted_changes"])
    _update(run_id, workspace=ws["workspace"], base_commit=ws["base_commit"], receipt=receipt)

    argv = adapters.build_argv(run["agent"], status.path, task=run["task"], mode=run["mode"],
                               workspace=ws["workspace"], out_dir=str(out_dir), timeout_s=plan.get("timeout_s") or DEFAULT_TIMEOUT_S)
    state_dirs = workspace.agent_state_dirs(run["agent"])
    config_files = [p for p in _agent_config_files(run["agent"]) if Path(p).is_file()]
    state_bindings = workspace.private_agent_state(run["agent"], out_dir, state_dirs,
        resume_state=(approved_scope.get('resume') or {}).get('private_state'))
    receipt['private_state'] = state_bindings
    if plan.get('resume_run'):receipt['resume_run'] = plan['resume_run']
    control_dir = out_dir.parent / f"{run_id}.control"
    control_dir.mkdir(mode=0o700)
    protected = [str(p if p.is_absolute() else Path(proj["path"]) / p)
                 for p in (Path(raw).expanduser() for raw in proj.get("protected_paths") or [])]
    broker = None
    cid = ""
    try:
        if status.execution.get("backend") == "oci":
            from jarvis.coding_agents import oci, transport
            broker = transport.Broker(run["agent"], control_dir / "network.jsonl")
            request = {"agent": run["agent"], "binary": status.path, "argv": argv,
                       "cwd": ws["workspace"], "out_dir": str(out_dir),
                       "prompt": adapters.prompt_for(run["task"], run["mode"]),
                       "timeout_s": int(plan.get("timeout_s") or DEFAULT_TIMEOUT_S),
                       "resume_thread_id": (approved_scope.get('resume') or {}).get('thread_id')}
            cid = oci.create(run_id=run_id, image=status.execution["image"], ws=ws["workspace"],
                out_dir=str(out_dir), request=request, installations=_install_dirs(status.path),
                bindings=state_bindings, socket_path=broker.path,
                read_only=run["mode"] == discovery.READ_ONLY)
            _containers[run_id] = cid
            sandboxed = [*oci.DOCKER, "start", "--attach", cid]
            receipt.update(container_id=cid, sandbox=oci.SCHEME, image=status.execution["image"],
                execution_certificate=status.execution, network_log=str(control_dir / "network.jsonl"),
                limits={"memory_bytes": 6*1024**3, "pids": 512, "cpus": 4})
        elif status.execution.get("backend") == "offline_fixture":
            # Only test-injected certificates can reach this backend. The real
            # certificate loader accepts the measured OCI backend exclusively.
            sandboxed = workspace.sandbox_argv(argv, ws["workspace"], writable=[str(out_dir)],
                readable=_install_dirs(status.path), network=False,
                read_only=run["mode"] == discovery.READ_ONLY, state_bindings=state_bindings, readonly=config_files)
            receipt["sandbox"] = "bwrap: offline fixture, private roots, private PID/IPC, network disabled"
            sandboxed, limits = workspace.limit_argv(sandboxed)
            receipt["limits"] = limits or "none (systemd user scope unavailable)"
        else:
            raise workspace.WorkspaceError("no certified execution backend")
        mounted = (oci.mount_paths(cid) if cid else
                   [ws["workspace"], str(out_dir), *(path for pair in state_bindings for path in pair)])
        exposure = boundary.exposed(mounted, protected)
        if exposure:
            raise workspace.WorkspaceError("protected path mounted into the sandbox: " + "; ".join(exposure))
        receipt["protected_mounts"] = "none (checked against the sandbox's actual mounts)"
    except Exception as exc:
        if cid:
            _stop_container(run_id)
        if broker:
            broker.close()
        return refuse(f"isolation refused: {type(exc).__name__}: {exc}")
    receipt["argv"] = ([status.path, "app-server", "--listen", "stdio://", "-c", "memories.use_memories=false",
                         "-c", "memories.generate_memories=false"] if cid and run["agent"] == "codex" else
                       [a if a != adapters.prompt_for(run["task"], run["mode"]) else "<prompt>" for a in argv])
    if cid and run["agent"] == "codex":
        receipt["protocol"] = {"transport": "JSON-RPC stdio", "sandboxPolicy": "externalSandbox",
                               "approvalPolicy": "never", "subscription_account_required": True}
    try:
        before_snapshot = boundary.snapshot(protected, data_dir=DATA_DIR, run_id=run_id) if protected else None
    except boundary.BoundaryError as exc:
        _stop_container(run_id)
        if broker:
            broker.close()
        return refuse(str(exc))
    before_protected = boundary.summary(before_snapshot) if before_snapshot else None
    receipt["protected_before"] = before_protected
    _update(run_id, receipt=receipt)
    before_config = {p: _read(p) for p in config_files} if config_files else None

    from jarvis.coding_agents.discovery import _search_path

    env = build_subprocess_env(extra={"PATH": os.pathsep.join(_search_path()), "NO_COLOR": "1",
                                      "GIT_TERMINAL_PROMPT": "0"})
    env.pop("SSH_AUTH_SOCK", None)
    timeout_s = int(plan.get("timeout_s") or DEFAULT_TIMEOUT_S)
    started = time.time()
    if (get_run(run_id) or {}).get('cancel_requested'):
        _stop_container(run_id)
        if broker:broker.close()
        return _finish(run_id, {'status': contract.CANCELLED, 'success': False,
            'reason': 'cancelled before launch', 'verified': [], 'unverified': []}, receipt=receipt)
    _update(run_id, status=RUNNING, started_at=started)
    _event(run_id, "started", f"{run['agent']} in {ws['workspace']}")
    try:
        proc = subprocess.Popen(sandboxed, cwd=ws["workspace"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.DEVNULL, text=True, start_new_session=True)
    except OSError as exc:
        _stop_container(run_id)
        if broker:
            broker.close()
        return refuse(f"sandbox launch failed: {exc}")
    _procs[run_id] = proc
    _update(run_id, pid=proc.pid)
    out_chunks: list[str] = []
    err_chunks: list[str] = []
    size = {"n": 0}
    output_lock = threading.Lock()
    secrets_to_hide = _private_tokens(state_bindings)
    log_paths = {"stdout": control_dir / "stdout.jsonl", "stderr": control_dir / "stderr.log"}
    for path in log_paths.values():
        path.touch(mode=0o600)
    receipt["output_logs"] = {key: str(path) for key, path in log_paths.items()}
    _update(run_id, receipt=receipt)

    def clean(text):
        for secret in secrets_to_hide:
            text = text.replace(secret, "<redacted>")
        return discovery.redact(text)

    def _pump(stream, sink: list[str], progress: bool) -> None:
        # Bound individual lines as well as the total. An untrusted process
        # cannot allocate an unlimited line before supervision sees its size.
        with log_paths["stdout" if progress else "stderr"].open("a") as log:
            while line := stream.readline(MAX_OUTPUT_BYTES + 1):
                with output_lock:
                    size["n"] += len(line)
                    retain = size["n"] <= MAX_OUTPUT_BYTES
                if retain:
                    line = clean(line)
                    sink.append(line)
                    log.write(line)
                    log.flush()  # terminal process/restart is not required for history
                if retain and progress and line.startswith("{"):
                    try:
                        ev = json.loads(line)
                        if ev.get('type') == 'thread.started' and ev.get('thread_id'):
                            receipt['session_id'] = str(ev['thread_id'])
                            _update(run_id, receipt=receipt)
                        if ev.get('type') == 'approval.denied':
                            _event(run_id, 'approval_denied', clean(str(ev.get('method') or 'unsupported request')))
                        _event(run_id, "progress", clean(str(ev.get("type") or "") + " " + str((ev.get("item") or {}).get("type") or "")))
                    except json.JSONDecodeError:
                        pass

    pumps = [threading.Thread(target=_pump, args=(proc.stdout, out_chunks, True), daemon=True),
             threading.Thread(target=_pump, args=(proc.stderr, err_chunks, False), daemon=True)]
    for t in pumps:
        t.start()
    timed_out = cancelled = over_limit = False
    meter = _ResourceMeter(proc.pid)
    while proc.poll() is None:
        time.sleep(0.25)
        meter.sample()
        if time.time() - started > timeout_s:
            timed_out = True
        elif size["n"] > MAX_OUTPUT_BYTES:
            over_limit = True
        elif (get_run(run_id) or {}).get("cancel_requested"):
            cancelled = True
        if timed_out or cancelled or over_limit:
            _event(run_id, "timeout" if timed_out else "cancel", "stopping the agent")
            _stop_container(run_id)
            _kill(proc)
            break
    proc.wait()
    for t in pumps:
        t.join(timeout=3)
    _procs.pop(run_id, None)
    exit_code = proc.returncode
    cancelled = cancelled or bool((get_run(run_id) or {}).get("cancel_requested"))
    timed_out = timed_out or bool(cid and exit_code == 124)
    _stop_container(run_id)
    if broker:
        broker.close()
    # Subscription refresh may introduce credentials after launch. Sanitize all
    # retained logs again before they become durable verification artifacts.
    secrets_to_hide.update(_private_tokens(state_bindings))
    stdout, stderr = clean("".join(out_chunks)), clean("".join(err_chunks))
    for name, content in (("stdout.jsonl", stdout), ("stderr.log", stderr)):
        path = control_dir / name
        path.write_text(content)
        path.chmod(0o600)
    receipt["output_logs"] = {"stdout": str(control_dir / "stdout.jsonl"), "stderr": str(control_dir / "stderr.log")}
    _update(run_id, receipt=receipt)
    report = adapters.parse(run["agent"], stdout, stderr, str(out_dir))
    report.final_message = clean(report.final_message)
    report.errors = [clean(error) for error in report.errors]
    report.commands = [{key: clean(value) if isinstance(value, str) else value for key, value in cmd.items()}
                       for cmd in report.commands]
    error_kind = adapters.error_class(report, exit_code=exit_code, timed_out=timed_out, cancelled=cancelled)
    if cid and error_kind in ("subscription_quota", "authentication", "isolation_compatibility", "transport"):
        runtime.unavailable(run["agent"], error_kind, quota=error_kind == "subscription_quota")
        discovery.set_discovery_for_tests(None)
    receipt["error_class"] = error_kind
    if over_limit:
        report.errors.append(f"output exceeded {MAX_OUTPUT_BYTES} bytes; the agent was stopped")
    changes = workspace.collect_changes(ws["workspace"], ws["base_commit"])
    tests = None
    before_verification = workspace.snapshot(ws['workspace'])
    if run["mode"] == discovery.WORKSPACE_WRITE and changes["files"] and not (timed_out or cancelled):
        _event(run_id, "progress", "ARIA running tests")
        tests = workspace.run_tests(ws["workspace"], str(proj.get("test_command") or ""),
            timeout=max(0, timeout_s - (time.time() - started)),
            cancel_check=lambda: bool((get_run(run_id) or {}).get('cancel_requested')))
        cancelled = cancelled or bool(tests.get('cancelled'))
        timed_out = timed_out or bool(tests.get('timed_out'))
    cancelled = cancelled or bool((get_run(run_id) or {}).get('cancel_requested'))
    after_verification = workspace.snapshot(ws['workspace'])
    if tests:
        tests['workspace_snapshot'] = before_verification
        if before_verification != after_verification:
            tests.update(passed=False, error='verification changed code; the tested artifact is not the current workspace')
    receipt['workspace_snapshot'] = after_verification
    receipt['session_id'] = report.session_id or receipt.get('session_id', '')
    if cancelled or timed_out:
        error_kind = 'cancelled' if cancelled else 'timeout'
        receipt['error_class'] = error_kind
    from jarvis.coding_agents import artifacts
    receipt['artifacts'] = artifacts.capture(control_dir / 'artifacts', patch=changes['patch'],
        tests=tests, logs=receipt['output_logs'])
    protected_report = None
    if before_snapshot:
        try:
            after_snapshot = boundary.snapshot(protected, data_dir=DATA_DIR, run_id=run_id)
            protected_report = boundary.compare(before_snapshot, after_snapshot, data_dir=DATA_DIR)
            receipt["protected_after"] = boundary.summary(after_snapshot)
        except boundary.BoundaryError as exc:
            protected_report = {"violations": [f"protected inventory failed: {exc}"], "runtime_writes": [],
                                "controller_writes": [], "checked_files": 0}
            receipt["protected_after"] = None
        receipt["protected_changes"] = {**protected_report,
                                        "runtime_writes": protected_report["runtime_writes"][:200]}
    else:
        receipt["protected_after"] = None
    judged = contract.verdict(
        mode=run["mode"], exit_code=exit_code, timed_out=timed_out, cancelled=cancelled,
        changes=changes, tests=tests,
        protected_before=before_protected,
        protected_after=receipt["protected_after"],
        protected_report=protected_report,
        config_before=_config_view(before_config, ws["workspace"], receipt) if before_config else None,
        config_after=_config_view({p: _read(p) for p in config_files}, ws["workspace"], receipt,
                                  before=before_config) if before_config else None,
        agent_claims=adapters.claims(report.final_message), report_errors=report.errors,
        final_message=report.final_message,
    )
    if run['agent'] == 'codex' and report.terminal_status != 'completed' and judged['status'] not in (contract.CANCELLED, contract.TIMEOUT, contract.VIOLATION):
        judged.update(status=contract.FAILED, success=False, reason='Codex did not emit a successful terminal event')
    if over_limit and judged["status"] not in (contract.CANCELLED,):
        judged.update(status=contract.FAILED, success=False, reason="output limit exceeded")
    result = {
        **judged,
        "requested": {"task": run["task"], "mode": run["mode"], "agent": run["agent"], "project": run["project"]},
        "attempted": {"commands": report.commands[:50], "files_reported": sorted(set(filter(None, report.files_reported)))[:100],
                      "events": report.events, "source": "agent's own event stream (unverified)"},
        "changed": {k: changes[k] for k in ("files", "stat", "agent_commits", "diff_truncated", "diff_sha256")},
        "diff_excerpt": changes["diff_excerpt"],
        "tests_run": [tests] if tests else [],
        "agent_report": report.final_message[:6000],
        "usage": report.usage,
        "error_class": error_kind,
        "session_id": report.session_id,
        "artifacts": receipt["artifacts"],
        "seconds": round(time.time() - started, 1),
        "resources": {**meter.summary(), "scope": "controller client only; OCI caps independently enforced"} if cid else meter.summary(),
        "exit_code": exit_code,
    }
    return _finish(run_id, result, receipt=receipt, exit_code=exit_code)


class _ResourceMeter:
    """Peak RSS, CPU seconds and process count of the agent's process tree."""

    def __init__(self, pid: int) -> None:
        self.pid = pid
        self.peak_rss = 0
        self.cpu: dict[int, float] = {}
        self.max_procs = 0

    def sample(self) -> None:
        try:
            import psutil

            root = psutil.Process(self.pid)
            procs = [root, *root.children(recursive=True)]
        except Exception:
            return
        rss = 0
        for p in procs:
            try:
                rss += p.memory_info().rss
                t = p.cpu_times()
                self.cpu[p.pid] = max(self.cpu.get(p.pid, 0.0), t.user + t.system)
            except Exception:
                continue
        self.peak_rss = max(self.peak_rss, rss)
        self.max_procs = max(self.max_procs, len(procs))

    def summary(self) -> dict[str, Any]:
        return {"peak_rss_mb": round(self.peak_rss / 2**20, 1), "cpu_seconds": round(sum(self.cpu.values()), 1),
                "max_processes": self.max_procs, "sampled": "every 0.25 s (short-lived processes may be missed)"}


def _install_dirs(binary: str) -> list[str]:
    """The agent's own installation (binary dir, package root), mounted read-only."""
    real = Path(binary).resolve()
    dirs = {str(Path(binary).parent), str(real.parent)}
    for parent in real.parents:  # an npm package root, e.g. …/lib/node_modules/@anthropic-ai/claude-code
        if parent.name == "node_modules":
            break
        if (parent / "package.json").is_file():
            dirs.add(str(parent))
            break
    return sorted(dirs)


def _private_tokens(bindings: list[tuple[str, str]]) -> set[str]:
    """Redact exact sign-in tokens from private copies, never return them in receipts."""
    found = set()
    def scan(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, str) and len(item) >= 8 and ("token" in key.lower() or "api_key" in key.lower()):
                    found.add(item)
                else:
                    scan(item)
        elif isinstance(value, list):
            for item in value:
                scan(item)
    for raw, _ in bindings:
        root = Path(raw)
        if root.is_symlink() or any(parent.is_symlink() for parent in root.parents):
            continue
        paths = (path for path in root.rglob("*") if path.is_file() and (path.suffix == ".json" or path.name == "antigravity-oauth-token")) if root.is_dir() else [root]
        for index, path in enumerate(paths):
            if index >= 100:
                break
            if path.is_symlink() or not workspace._inside(path, root if root.is_dir() else root.parent):
                continue
            try:
                if path.stat().st_size <= 1_000_000:
                    scan(json.loads(path.read_text()))
            except (OSError, ValueError):
                continue
    return found


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


_TRUST_ENTRY = re.compile(r'\n?\[projects\."(?P<path>[^"]+)"\]\s*\ntrust_level\s*=\s*"[a-z]+"\s*\n?')


def _config_view(files: dict[str, str], ws: str, receipt: dict, *, before: dict[str, str] | None = None) -> dict:
    """Agent config content for comparison, minus one benign vendor write.

    Codex records ``[projects."<cwd>"] trust_level`` for every directory it runs
    in. A new entry for *this run's disposable workspace* is bookkeeping, noted
    in the receipt; any other change still counts as the agent changing its own
    permissions.
    """
    out = {}
    for path, text in files.items():
        if before is not None:
            for m in _TRUST_ENTRY.finditer(text):
                if m.group("path") == ws and m.group(0).strip() not in (before.get(path) or ""):
                    text = text.replace(m.group(0), "\n", 1)
                    receipt.setdefault("notes", []).append(f"{Path(path).name}: CLI recorded a trust entry for the disposable workspace")
        out[path] = re.sub(r"\n{2,}", "\n", text).strip()
    return out


def _agent_config_files(agent: str) -> list[str]:
    home = Path.home()
    return [str(p) for p in {
        "codex": [home / ".codex" / "config.toml"],
        "claude_code": [home / ".claude.json", home / ".claude" / "settings.json", home / ".claude" / "settings.local.json"],
        "antigravity": [home / ".gemini" / "antigravity-cli" / "settings.json", home / ".gemini" / "settings.json"],
    }.get(agent, [])]


def _finish(run_id: str, result: dict[str, Any], *, receipt: dict[str, Any], exit_code: int | None = None) -> dict[str, Any]:
    # Serialize completion with owner cancellation. A cancellation accepted
    # before this commit must never be reported as a verified completion.
    with _conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = conn.execute("SELECT status,cancel_requested FROM runs WHERE id=?", (run_id,)).fetchone()
        if current and current["cancel_requested"] and result["status"] not in (contract.VIOLATION, contract.REFUSED):
            result = {
                **result,
                "status": contract.CANCELLED,
                "success": False,
                "verified_completion": False,
                "reason": "owner cancelled before completion",
                "error_class": "cancelled",
            }
            receipt = {**receipt, "error_class": "cancelled"}
        conn.execute(
            "UPDATE runs SET status=?,finished_at=?,exit_code=?,result=?,receipt=? WHERE id=?",
            (result["status"], time.time(), exit_code, json.dumps(result, default=str), json.dumps(receipt, default=str), run_id),
        )
    _event(run_id, "finished", f"{result['status']}: {result.get('reason', '')}")
    run = get_run(run_id) or {}
    if result["status"] == contract.VIOLATION:
        from jarvis.coding_agents import runtime

        runtime.unavailable(run["agent"], f"boundary violation in durable run {run_id}; requires review")
        discovery.set_discovery_for_tests(None)
    _continuity_outcome(run, result)
    return result


# ---------------------------------------------------------------- continuity (never ACM)


def _continuity_plan(plan: dict[str, Any]) -> None:
    try:
        from jarvis.continuity import store

        store.add_record(
            store.SUGGESTION,
            f"Proposed: {discovery.LABELS.get(plan['agent'], plan['agent'])} — {plan['task'][:300]} "
            f"({plan['mode'].replace('_', '-')}, project {plan['project']}). Awaiting the owner's approval.",
            actor=store.ASSISTANT, status=store.PROPOSED, project=plan["project"],
            source_ref=f"coding_plan:{plan['id']}", detail={"plan_id": plan["id"], "agent": plan["agent"]},
        )
    except Exception:
        pass


def _continuity_update(source_ref: str, status: str) -> None:
    try:
        from jarvis.continuity import store

        rec = store.record_by_source(source_ref)
        if rec:
            store.update_record(rec["id"], status=status)
    except Exception:
        pass


def _continuity_outcome(run: dict[str, Any], result: dict[str, Any]) -> None:
    """A tool-actor outcome and a project checkpoint. Agent claims stay labelled as claims."""
    try:
        from jarvis.continuity import store

        label = discovery.LABELS.get(run.get("agent") or "", run.get("agent") or "agent")
        lines = [f"[{label}] {run.get('task', '')[:200]} — {result['status']}: {result.get('reason', '')}"]
        if result.get("verified"):
            lines.append("Verified by ARIA: " + "; ".join(result["verified"]))
        files = [f["path"] for f in (result.get("changed") or {}).get("files") or []]
        if files:
            lines.append("Files changed (git): " + ", ".join(files[:12]))
        if result.get("unverified"):
            lines.append("Agent reported (unverified): " + " | ".join(result["unverified"][:4]))
        if result.get("contradicted_claims"):
            lines.append("Agent claims contradicted by ARIA's tests: " + " | ".join(result["contradicted_claims"][:3]))
        ok = bool(result.get("success"))
        store.add_record(
            store.OUTCOME, "\n".join(lines), actor=store.TOOL, status=store.DONE if ok else store.FAILED,
            project=run.get("project") or "", source_ref=f"coding_run:{run['id']}",
            verified=bool(result.get("verified_completion")),
            detail={"run_id": run["id"], "agent": run.get("agent"), "status": result["status"]},
        )
        store.add_record(
            store.CHECKPOINT,
            f"Checkpoint after {label} run {run['id']} on {run.get('project')}: {result['status']}. "
            + (f"Workspace {run.get('workspace')} (base {str(run.get('base_commit') or '')[:10]}) holds the changes; "
               "nothing was applied to the project." if files else "No changes to apply."),
            actor=store.MISSION, status=store.OPEN if files and ok else store.DONE,
            project=run.get("project") or "", source_ref=f"coding_checkpoint:{run['id']}",
            detail={"run_id": run["id"], "workspace": run.get("workspace"), "base_commit": run.get("base_commit")},
        )
    except Exception:
        pass


def reset_for_tests() -> None:
    with _lock:
        if DB_PATH.exists():
            DB_PATH.unlink()
        _procs.clear()
        _owned.clear()
