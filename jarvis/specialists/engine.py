"""Unified Specialist Team orchestrator — one execution model."""

from __future__ import annotations

import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from jarvis.specialists.budgets import TeamBudget
from jarvis.specialists.catalog import get_specialist, normalize_team
from jarvis.specialists.composer import compose_team, map_roles_to_specialists
from jarvis.specialists.execute import run_specialist
from jarvis.specialists.scratchpad import SharedScratchpad
from jarvis.specialists.synthesizer import synthesize

log = logging.getLogger("jarvis.specialists.engine")


def propose_team(goal: str, *, specialists: list[str] | None = None, use_llm: bool = False) -> dict[str, Any]:
    return compose_team(goal, specialists=specialists, use_llm=use_llm)


def explain_run(run_id: str) -> dict[str, Any]:
    from jarvis.specialists.history import get_run

    run = get_run(run_id)
    if not run:
        pad = SharedScratchpad.load(run_id)
        if not pad:
            return {"ok": False, "error": "not_found"}
        return {"ok": True, "run_id": run_id, "scratchpad": pad.snapshot()}
    return {"ok": True, "run": run}


def run_team(
    assistant: Any,
    goal: str,
    *,
    specialists: list[str] | None = None,
    roles: list[str] | None = None,  # legacy
    confirm: bool = False,
    stop_on_error: bool = False,
    synthesize_final: bool = True,
    budget: dict[str, Any] | TeamBudget | None = None,
    extras: dict[str, Any] | None = None,
    trigger: str = "manual",
    emit_bridges: bool = True,
    parallel_readers: bool = False,
    critic_loop: bool = False,
    approve_writes: bool = False,
    approve_experimental: bool = False,
    cancel_check: Callable[[], bool] | None = None,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Execute a Specialist Team run. Requires confirm=True unless trigger is internal test with confirm."""
    goal = (goal or "").strip()
    if not goal:
        return {"ok": False, "status": "failed", "error": "goal required"}

    bud = budget if isinstance(budget, TeamBudget) else TeamBudget.from_dict(budget)
    if critic_loop:
        bud.allow_critic_loop = True
    if parallel_readers:
        bud.allow_parallel_readers = True
    if bud.require_confirm and not confirm and trigger not in ("compat-legacy",):
        # Allow legacy compat path to set confirm via wrapper
        proposal = propose_team(goal, specialists=specialists)
        return {
            "ok": False,
            "status": "permission_required",
            "error": "confirm=true required — review proposed team first",
            "confirmation_required": True,
            "proposal": proposal,
        }

    if roles and not specialists:
        specialists = map_roles_to_specialists(roles)

    proposal = propose_team(goal, specialists=specialists)
    team = list(proposal["team"])
    err = bud.check_start(len(team))
    if err:
        return err

    run_id = uuid.uuid4().hex[:12]
    correlation_id = correlation_id or uuid.uuid4().hex[:12]
    pad = SharedScratchpad(goal, run_id=run_id)
    steps: list[dict[str, Any]] = []
    status = "running"
    started = time.time()
    job_id = None
    cancelled = False
    permissions: list[str] = []

    if emit_bridges:
        try:
            from jarvis.specialists.jobs import start_team_job

            job_id = start_team_job(run_id=run_id, goal=goal, team=team, correlation_id=correlation_id)
        except Exception as exc:
            log.debug("job bridge: %s", exc)

    def progress(payload: dict[str, Any]) -> None:
        if on_progress:
            try:
                on_progress(payload)
            except Exception:
                pass
        if job_id:
            try:
                from jarvis.specialists.jobs import update_team_job

                update_team_job(job_id, **payload)
            except Exception:
                pass

    progress({"status": "running", "pct": 0, "message": f"Starting team: {', '.join(team)}", "current": None})

    # Optional parallel read-only phase
    readers = [s for s in team if (get_specialist(s) or {}).get("read_only")]
    writers = [s for s in team if not (get_specialist(s) or {}).get("read_only")]
    ordered: list[str]
    if parallel_readers and bud.allow_parallel_readers and len(readers) > 1:
        ordered = []  # handled specially
    else:
        # writers after readers by default for safer flows
        ordered = [s for s in team if s in readers] + [s for s in team if s in writers]
        if not ordered:
            ordered = team

    def _one(sid: str) -> dict[str, Any]:
        bud.charge(1.0)
        t0 = time.time()
        result = run_specialist(
            assistant,
            sid,
            goal,
            pad,
            extras=extras,
            approve_writes=approve_writes or not bud.require_write_approval,
        )
        result["elapsed_ms"] = int((time.time() - t0) * 1000)
        return result

    def _record(result: dict[str, Any]) -> None:
        nonlocal status
        sid = result.get("agent") or "?"
        for p in result.get("permissions") or []:
            if p not in permissions:
                permissions.append(p)
        if result.get("permission_required"):
            status = "permission_required"
            pad.add_failure(sid, result.get("error") or "permission required", recovered=False)
        elif result.get("ok"):
            if result.get("message"):
                pad.add_note(sid, result["message"])
            pad.add_artifact(sid, result.get("data") or {}, kind="output")
        else:
            # Honest: missing action is failure, not recovery
            recovered = False
            pad.add_failure(sid, result.get("error") or result.get("message") or "failed", recovered=recovered)
            result["recovered"] = False
        steps.append(result)

    if parallel_readers and bud.allow_parallel_readers and len(readers) > 1:
        progress({"status": "running", "pct": 10, "message": "Parallel read specialists", "current": "parallel"})
        with ThreadPoolExecutor(max_workers=min(4, len(readers))) as pool:
            futs = {pool.submit(_one, sid): sid for sid in readers}
            for fut in as_completed(futs):
                if cancel_check and cancel_check():
                    cancelled = True
                    status = "cancelled"
                    break
                budget_err = bud.check_step()
                if budget_err:
                    status = budget_err.get("status") or "failed"
                    steps.append({"ok": False, "agent": "_budget", "error": budget_err.get("error")})
                    break
                _record(fut.result())
        for sid in writers:
            if cancelled or status in ("permission_required", "timeout", "failed") and stop_on_error:
                break
            if cancel_check and cancel_check():
                cancelled = True
                status = "cancelled"
                break
            budget_err = bud.check_step()
            if budget_err:
                status = budget_err.get("status") or "failed"
                break
            progress(
                {
                    "status": "running",
                    "pct": int(100 * len(steps) / max(1, len(team) + 1)),
                    "message": f"Running {sid}",
                    "current": sid,
                }
            )
            _record(_one(sid))
            if not steps[-1].get("ok") and stop_on_error:
                status = "failed"
                break
            if status == "permission_required":
                break
    else:
        for sid in ordered:
            if cancel_check and cancel_check():
                cancelled = True
                status = "cancelled"
                break
            budget_err = bud.check_step()
            if budget_err:
                status = budget_err.get("status") or "failed"
                steps.append({"ok": False, "agent": "_budget", "error": budget_err.get("error"), "recovered": False})
                break
            progress(
                {
                    "status": "running",
                    "pct": int(100 * len(steps) / max(1, len(team) + 1)),
                    "message": f"Running {sid}",
                    "current": sid,
                }
            )
            _record(_one(sid))
            if status == "permission_required":
                break
            if not steps[-1].get("ok") and stop_on_error:
                status = "failed"
                break

    # Optional single critic loop (one revision only)
    synthesis_text = ""
    if critic_loop and bud.allow_critic_loop and status == "running" and not cancelled:
        from jarvis.specialists.critic import one_revision

        rev = one_revision(assistant, goal, pad, steps)
        steps.append(rev)
        if rev.get("ok") and rev.get("message"):
            pad.add_note("critic_loop", rev["message"])

    if synthesize_final and status not in ("cancelled",) and steps:
        syn = synthesize(goal, steps, pad)
        synthesis_text = syn.get("synthesis") or ""
        steps.append(
            {
                "ok": True,
                "agent": "synthesizer",
                "name": "Synthesizer",
                "role": "synthesis",
                "message": synthesis_text[:2000],
                "action": "synthesize",
                "recovered": False,
            }
        )
        pad.add_note("synthesizer", synthesis_text[:2000])

    elapsed_ms = int((time.time() - started) * 1000)
    if cancelled:
        status = "cancelled"
    elif status == "running":
        failed = [s for s in steps if not s.get("ok") and s.get("agent") != "synthesizer"]
        ok_n = [s for s in steps if s.get("ok")]
        if not steps:
            status = "failed"
        elif not failed:
            status = "succeeded"
        elif ok_n:
            status = "partial_success"
        else:
            status = "failed"

    ok = status in ("succeeded", "partial_success")
    payload = {
        "ok": ok,
        "status": status,
        "run_id": run_id,
        "correlation_id": correlation_id,
        "goal": goal,
        "team": team,
        "specialists": team,  # compat
        "steps": steps,
        "scratchpad": pad.snapshot(),
        "synthesis": synthesis_text,
        "summary": synthesis_text or _summary(steps),
        "elapsed_ms": elapsed_ms,
        "job_id": job_id,
        "budget": bud.to_dict(),
        "permissions": permissions,
        "trigger": trigger,
        "stop_on_error": stop_on_error,
        "proposal": proposal,
    }

    try:
        pad.persist()
    except Exception:
        pass
    try:
        from jarvis.specialists.history import record_run

        record_run(payload)
    except Exception as exc:
        log.debug("history: %s", exc)

    if emit_bridges:
        try:
            from jarvis.specialists.activity import publish_team_event

            pub = publish_team_event(payload)
            payload["activity"] = pub.get("activity")
        except Exception as exc:
            log.debug("activity: %s", exc)
        if job_id:
            try:
                from jarvis.specialists.jobs import finish_team_job

                finish_team_job(job_id, status=status, result=payload)
            except Exception:
                pass

    progress({"status": status, "pct": 100, "message": status, "done": True})
    return payload


def _summary(steps: list[dict[str, Any]]) -> str:
    lines = ["## Specialist Team run", ""]
    for s in steps:
        flag = "ok" if s.get("ok") else "failed"
        lines.append(f"- **{s.get('agent')}**: {flag}")
    return "\n".join(lines)
