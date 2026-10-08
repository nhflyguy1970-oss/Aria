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
import secrets
import signal
import sqlite3
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from jarvis.coding_agents import adapters, contract, discovery, workspace
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
            depth INTEGER DEFAULT 0, source TEXT, rationale TEXT
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
    return conn


# ---------------------------------------------------------------- plans


def _hash(agent: str, project: str, mode: str, task: str, timeout_s: int) -> str:
    return hashlib.sha256(json.dumps([agent, project, mode, task, timeout_s]).encode()).hexdigest()[:16]


def create_plan(*, agent: str, project: str, mode: str, task: str, timeout_s: int = DEFAULT_TIMEOUT_S,
                source: str = "chat", rationale: str = "", parent_run: str = "") -> dict[str, Any]:
    from jarvis.integration import policy

    if mode not in (discovery.READ_ONLY, discovery.WORKSPACE_WRITE):
        raise AgentRunError(f"unknown mode {mode!r}")
    ceiling = int(policy.bounds_for().get("max_runtime_s") or DEFAULT_TIMEOUT_S)
    timeout_s = max(30, min(int(timeout_s or DEFAULT_TIMEOUT_S), ceiling))
    depth = 0
    if parent_run:
        parent = get_run(parent_run)
        parent_plan = get_plan(parent["plan_id"]) if parent else None
        depth = int((parent_plan or {}).get("depth") or 0) + 1
        if depth > MAX_DELEGATION_DEPTH:
            raise AgentRunError("delegation depth limit reached: an agent's recommendation cannot start another chain")
    pid = "plan_" + uuid.uuid4().hex[:10]
    row = {
        "id": pid, "created_at": time.time(), "agent": agent, "project": project, "mode": mode,
        "task": task.strip()[:4000], "timeout_s": timeout_s, "plan_hash": _hash(agent, project, mode, task, timeout_s),
        "status": PROPOSED, "nonce": secrets.token_urlsafe(16), "approved_at": None, "approved_via": "",
        "expires_at": None, "parent_run": parent_run, "depth": depth, "source": source, "rationale": rationale[:500],
    }
    with _lock, _conn() as conn:
        conn.execute(f"INSERT INTO plans ({','.join(row)}) VALUES ({','.join('?' * len(row))})", tuple(row.values()))
    _continuity_plan(row)
    return public_plan(row)


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
    if plan["plan_hash"] != _hash(plan["agent"], plan["project"], plan["mode"], plan["task"], plan["timeout_s"]):
        raise AgentRunError("plan changed after it was proposed")
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


def _consume(plan_id: str) -> dict[str, Any]:
    now = time.time()
    with _lock, _conn() as conn:
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
        if r["owner_pid"] != os.getpid() or not _alive(r["pid"]):
            _update(r["id"], status=contract.INTERRUPTED, finished_at=time.time(),
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
    recover_interrupted()
    with _conn() as conn:
        active = conn.execute("SELECT COUNT(*) FROM runs WHERE status IN (?,?)", (PENDING, RUNNING)).fetchone()[0]
    if active >= MAX_CONCURRENT:
        raise AgentRunError("another coding-agent run is in progress; wait for it or cancel it")
    plan = _consume(plan_id)
    run_id = "run_" + uuid.uuid4().hex[:10]
    mission_id = engine.create_mission(
        f"[{plan['agent']}] {plan['task'][:120]}",
        steps=[{"name": "coding agent run", "action": "coding_agent_run_step", "params": {"run_id": run_id}}],
        kind="coding_agent",
    )
    with _conn() as conn:
        conn.execute(
            "INSERT INTO runs (id, plan_id, mission_id, agent, project, mode, task, status, owner_pid, started_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (run_id, plan_id, mission_id, plan["agent"], plan["project"], plan["mode"], plan["task"], PENDING,
             os.getpid(), time.time()),
        )
    _event(run_id, "queued", f"mission {mission_id}")
    _owned.add(run_id)

    def _go() -> None:
        try:
            engine.run(mission_id, runner=lambda step, ctx: execute_step(step["params"]["run_id"]))
        except Exception as exc:  # noqa: BLE001 — recorded on the run
            run = get_run(run_id)
            if run and run["status"] in (PENDING, RUNNING):
                _finish(run_id, {"status": contract.REFUSED if "policy" in type(exc).__name__.lower() else contract.FAILED,
                                 "success": False, "reason": f"{type(exc).__name__}: {exc}",
                                 "verified": [], "unverified": []}, receipt={})
        finally:
            _owned.discard(run_id)

    if background:
        threading.Thread(target=_go, name=f"coding-agent-{run_id}", daemon=True).start()
    else:
        _go()
    return get_run(run_id) or {}


def cancel(run_id: str) -> dict[str, Any]:
    run = get_run(run_id)
    if not run:
        raise AgentRunError("no such run")
    _update(run_id, cancel_requested=1)
    _event(run_id, "cancel", "owner requested cancellation")
    if run.get("mission_id"):
        try:
            from jarvis.missions import store as mission_store

            mission_store.request_cancel(run["mission_id"])
        except Exception:
            pass
    proc = _procs.get(run_id)
    if proc and proc.poll() is None:
        _kill(proc)
    return get_run(run_id) or {}


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
    receipt: dict[str, Any] = {"plan_id": run["plan_id"], "plan_hash": plan.get("plan_hash"),
                               "approved_via": plan.get("approved_via"), "mission_id": run.get("mission_id")}

    def refuse(reason: str) -> dict[str, Any]:
        return _finish(run_id, {"status": contract.REFUSED, "success": False, "reason": reason,
                                "verified": [], "unverified": []}, receipt=receipt)

    for cap in ("mission", "coding"):
        if reason := policy.refusal(cap):
            return refuse(reason)
    status = discovery.discover().get(run["agent"])
    if not status or not status.usable:
        return refuse(f"{run['agent']} is not usable: {(status.notes if status else ['unknown agent'])}")
    if run["mode"] not in status.modes:
        return refuse(f"{run['agent']} does not support {run['mode']}")
    proj = projects.get(run["project"])
    if not proj:
        return refuse(f"project {run['project']!r} is not registered")
    receipt.update(agent_version=status.version, auth_method=status.auth.get("method"),
                   billing=status.auth.get("billing"), project_path=proj["path"])

    try:
        ws = workspace.prepare(proj["path"], run_id)
    except (workspace.WorkspaceError, subprocess.TimeoutExpired) as exc:
        return refuse(f"workspace: {exc}")
    out_dir = Path(ws["workspace"]).parent / f"run-{run_id}.out"
    out_dir.mkdir(parents=True, exist_ok=True)
    receipt.update(workspace=ws["workspace"], base_commit=ws["base_commit"],
                   source_uncommitted_changes=ws["source_uncommitted_changes"])
    _update(run_id, workspace=ws["workspace"], base_commit=ws["base_commit"])

    argv = adapters.build_argv(run["agent"], status.path, task=run["task"], mode=run["mode"],
                               workspace=ws["workspace"], out_dir=str(out_dir), timeout_s=plan.get("timeout_s") or DEFAULT_TIMEOUT_S)
    state_dirs = workspace.agent_state_dirs(run["agent"])
    try:
        sandboxed = workspace.sandbox_argv(argv, ws["workspace"], writable=state_dirs + [str(out_dir)],
                                           readable=[str(Path(status.path).parent)], network=True)
    except workspace.WorkspaceError as exc:
        return refuse(str(exc))
    receipt["argv"] = [a if a != argv[-1] or run["agent"] == "antigravity" else "<prompt>" for a in argv]
    receipt["sandbox"] = "bwrap: read-only root; writable workspace, run output dir and agent state dirs"
    protected = list(proj.get("protected_paths") or [])
    config_files = [p for p in _agent_config_files(run["agent"]) if Path(p).exists()]
    before_protected = workspace.fingerprint(protected) if protected else None
    before_config = workspace.fingerprint(config_files) if config_files else None

    from jarvis.coding_agents.discovery import _search_path

    env = build_subprocess_env(extra={"PATH": os.pathsep.join(_search_path()), "NO_COLOR": "1",
                                      "GIT_TERMINAL_PROMPT": "0"})
    env.pop("SSH_AUTH_SOCK", None)
    timeout_s = int(plan.get("timeout_s") or DEFAULT_TIMEOUT_S)
    started = time.time()
    _update(run_id, status=RUNNING, started_at=started)
    _event(run_id, "started", f"{run['agent']} in {ws['workspace']}")
    proc = subprocess.Popen(sandboxed, cwd=ws["workspace"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL, text=True, start_new_session=True)
    _procs[run_id] = proc
    _update(run_id, pid=proc.pid)
    out_chunks: list[str] = []
    err_chunks: list[str] = []
    size = {"n": 0}

    def _pump(stream, sink: list[str], progress: bool) -> None:
        for line in stream:
            size["n"] += len(line)
            if size["n"] <= MAX_OUTPUT_BYTES:
                sink.append(line)
            if progress and line.startswith("{"):
                try:
                    ev = json.loads(line)
                    _event(run_id, "progress", str(ev.get("type") or "") + " " + str((ev.get("item") or {}).get("type") or ""))
                except json.JSONDecodeError:
                    pass

    pumps = [threading.Thread(target=_pump, args=(proc.stdout, out_chunks, True), daemon=True),
             threading.Thread(target=_pump, args=(proc.stderr, err_chunks, False), daemon=True)]
    for t in pumps:
        t.start()
    timed_out = cancelled = over_limit = False
    while proc.poll() is None:
        time.sleep(0.25)
        if time.time() - started > timeout_s:
            timed_out = True
        elif size["n"] > MAX_OUTPUT_BYTES:
            over_limit = True
        elif (get_run(run_id) or {}).get("cancel_requested"):
            cancelled = True
        if timed_out or cancelled or over_limit:
            _event(run_id, "timeout" if timed_out else "cancel", "stopping the agent")
            _kill(proc)
            break
    proc.wait()
    for t in pumps:
        t.join(timeout=3)
    _procs.pop(run_id, None)
    exit_code = proc.returncode
    report = adapters.parse(run["agent"], "".join(out_chunks), "".join(err_chunks), str(out_dir))
    if over_limit:
        report.errors.append(f"output exceeded {MAX_OUTPUT_BYTES} bytes; the agent was stopped")
    changes = workspace.collect_changes(ws["workspace"], ws["base_commit"])
    tests = None
    if run["mode"] == discovery.WORKSPACE_WRITE and changes["files"] and not (timed_out or cancelled):
        _event(run_id, "progress", "ARIA running tests")
        tests = workspace.run_tests(ws["workspace"], str(proj.get("test_command") or ""))
    judged = contract.verdict(
        mode=run["mode"], exit_code=exit_code, timed_out=timed_out, cancelled=cancelled,
        changes=changes, tests=tests,
        protected_before=before_protected,
        protected_after=workspace.fingerprint(protected) if protected else None,
        config_before=before_config,
        config_after=workspace.fingerprint(config_files) if config_files else None,
        agent_claims=adapters.claims(report.final_message), report_errors=report.errors,
        final_message=report.final_message,
    )
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
        "session_id": report.session_id,
        "seconds": round(time.time() - started, 1),
        "exit_code": exit_code,
    }
    return _finish(run_id, result, receipt=receipt, exit_code=exit_code)


def _agent_config_files(agent: str) -> list[str]:
    home = Path.home()
    return [str(p) for p in {
        "codex": [home / ".codex" / "config.toml"],
        "claude_code": [home / ".claude" / "settings.json", home / ".claude" / "settings.local.json"],
        "antigravity": [home / ".gemini" / "antigravity-cli" / "settings.json", home / ".gemini" / "settings.json"],
    }.get(agent, [])]


def _finish(run_id: str, result: dict[str, Any], *, receipt: dict[str, Any], exit_code: int | None = None) -> dict[str, Any]:
    _update(run_id, status=result["status"], finished_at=time.time(), exit_code=exit_code, result=result, receipt=receipt)
    _event(run_id, "finished", f"{result['status']}: {result.get('reason', '')}")
    run = get_run(run_id) or {}
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
