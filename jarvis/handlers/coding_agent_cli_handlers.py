"""Coding-agent CLIs (Codex, Claude Code, Antigravity) — supervised, approval-gated.

Chat can propose a run and the owner approves it with a reply; nothing here
starts an agent without an approved plan (see jarvis.coding_agents.runs).
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _set_choice(assistant, question: str, choices: list[dict], message: str) -> None:
    session = getattr(assistant, "session", None)
    if session is None:
        return
    session.pending_clarification = {
        "type": "action_choice",
        "action": "clarify",
        "choices": [c["label"] for c in choices],
        "choice_intents": [c["intent"] for c in choices],
        "clarification_question": question,
        "original_prompt": message,
    }


@register_action("coding_agents_status", module="coding",
                 description="Which coding agents (Codex, Claude Code, Antigravity) are installed and signed in",
                 info=True)
def coding_agents_status(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import discovery

    rows = []
    for st in discovery.discover(refresh=bool(params.get("refresh"))).values():
        if not st.installed:
            rows.append(f"- **{st.label}**: not installed")
            continue
        auth = st.auth.get("state", "unknown")
        billing = st.auth.get("billing") or "?"
        state = "ready" if st.usable else "not usable"
        rows.append(f"- **{st.label}** {st.version}: {state}; sign-in {auth} ({billing}); modes "
                    f"{', '.join(m.replace('_', '-') for m in st.modes)}"
                    + (f"; notes: {'; '.join(st.notes)}" if st.notes else ""))
    return ok("**Coding agents**\n" + "\n".join(rows), module="coding",
              agents={k: v.to_dict() for k, v in discovery.discover().items()})


@register_action("coding_agent_plan", module="coding",
                 description="Propose a coding-agent run for a project (does not start it)", info=True)
def coding_agent_plan(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import supervisor

    out = supervisor.propose(message, agent_hint=str(params.get("agent") or ""), task=str(params.get("task") or ""),
                             session=getattr(assistant, "session", None), project_hint=str(params.get("project") or ""))
    if "error" in out:
        return err(out["error"], module="coding", error_kind="agent_unavailable")
    if "question" in out:
        return ok(out["question"], module="coding", type="clarification")
    _set_choice(assistant, "Start this coding-agent run?", out["choices"], message)
    return ok(out["text"] + "\n\nReply **yes** to start or **no** to drop it.", module="coding",
              type="clarification", plan=out["plan"], choices=["Yes", "No"])


@register_action("coding_agent_execute", module="coding",
                 description="Start an owner-approved coding-agent plan")
def coding_agent_execute(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import runs

    plan_id = str(params.get("plan_id") or "")
    plan = runs.get_plan(plan_id) if plan_id else None
    if not plan:
        return err("There's no such coding-agent plan.", module="coding")
    token = str(params.get("approval_token") or "")
    if plan["status"] == runs.PROPOSED and not token:
        return err("That plan hasn't been approved. I only start agent runs you confirm.", module="coding",
                   error_kind="approval_required")
    try:
        run = runs.start(plan_id, token=token, via="chat_confirmation", assistant=assistant)
    except runs.AgentRunError as exc:
        return err(f"Not started: {exc}", module="coding", error_kind="policy_denied")
    return ok(f"Started **{run['id']}** ({plan['agent']} on {plan['project']}). It works in a sandboxed disposable "
              f"copy; I'll verify the result myself. Ask \"how is the coding agent doing?\" for progress.",
              module="coding", run=run)


@register_action("coding_agent_reject", module="coding", description="Drop a proposed coding-agent plan", info=True)
def coding_agent_reject(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import runs

    if plan_id := str(params.get("plan_id") or ""):
        runs.reject(plan_id)
    return ok("Okay — not started.", module="coding")


@register_action("coding_agent_cancel", module="coding", description="Cancel a running coding-agent run")
def coding_agent_cancel(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import runs

    run_id = str(params.get("run_id") or "")
    if not run_id:
        active = [r for r in runs.list_runs(limit=5) if r["status"] in (runs.PENDING, runs.RUNNING)]
        if len(active) != 1:
            return err("Which run? " + (", ".join(r["id"] for r in active) or "None is running."), module="coding")
        run_id = active[0]["id"]
    try:
        run = runs.cancel(run_id)
    except runs.AgentRunError as exc:
        return err(str(exc), module="coding")
    return ok(f"Cancellation requested for {run_id} (status: {run['status']}).", module="coding")


def _window(text: str) -> tuple[float, float, str]:
    low = (text or "").lower()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if "yesterday" in low:
        return (today - timedelta(days=1)).timestamp(), today.timestamp(), "yesterday"
    if "today" in low:
        return today.timestamp(), time.time() + 1, "today"
    if "week" in low:
        return (today - timedelta(days=7)).timestamp(), time.time() + 1, "in the last 7 days"
    return 0.0, time.time() + 1, "so far"


@register_action("coding_agent_runs", module="coding",
                 description="What the coding agents did — from execution receipts, verified vs claimed", info=True)
def coding_agent_runs(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import discovery, runs

    start, end, label = _window(str(params.get("when") or message))
    rows = [r for r in runs.list_runs(since=start, project=str(params.get("project") or ""), limit=50)
            if (r.get("started_at") or 0) < end]
    if not rows:
        return ok(f"No coding-agent runs {label}. (Source: ARIA's execution receipts.)", module="coding")
    lines = [f"**Coding-agent runs {label}** (from execution receipts):"]
    for r in rows:
        res = r.get("result") or {}
        when = datetime.fromtimestamp(r["started_at"]).strftime("%a %H:%M") if r.get("started_at") else "?"
        lines.append(f"- {when} · {discovery.LABELS.get(r['agent'], r['agent'])} · {r['project']} · "
                     f"**{r['status']}** — {r['task'][:100]}")
        if res.get("verified"):
            lines.append(f"  - verified: {'; '.join(res['verified'][:3])}")
        if res.get("unverified"):
            lines.append(f"  - agent claimed (unverified): {' | '.join(res['unverified'][:2])}")
        if res.get("contradicted_claims"):
            lines.append(f"  - claims contradicted by tests: {' | '.join(res['contradicted_claims'][:2])}")
    return ok("\n".join(lines), module="coding", runs=[{k: r[k] for k in ("id", "agent", "project", "status")} for r in rows])


@register_action("coding_agent_progress", module="coding", description="Progress of the current coding-agent run",
                 info=True)
def coding_agent_progress(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import runs

    recent = runs.list_runs(limit=1)
    if not recent:
        return ok("No coding-agent runs yet.", module="coding")
    r = recent[0]
    ev = runs.events(r["id"], limit=5)
    tail = "\n".join(f"  - {e['kind']}: {e['detail']}" for e in ev)
    return ok(f"**{r['id']}** ({r['agent']} on {r['project']}): {r['status']}\n{tail}", module="coding")


@register_action("coding_agent_resume", module="coding",
                 description="Find unfinished coding-agent work and propose continuing it", info=True)
def coding_agent_resume(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import projects, supervisor

    where = projects.resolve(str(params.get("project") or message), session=getattr(assistant, "session", None))
    if "unregistered" in where:
        return err(f"{projects.TITLES[where['unregistered']]} isn't registered as a project in ARIA; "
                   "I won't guess its location.", module="coding")
    slug = (where.get("project") or {}).get("slug", "")
    todo = supervisor.resume_candidates(slug)
    if not todo:
        scope = f" for {where['project']['title']}" if slug else ""
        return ok(f"I have no unfinished coding-agent work on record{scope}. (Source: execution receipts.)",
                  module="coding")
    last = todo[0]
    res = last.get("result") or {}
    task = f"Continue this unfinished task: {last['task']}\nPrevious attempt ended: {last['status']} — {res.get('reason', '')}"
    out = supervisor.propose(task, agent_hint=last["agent"], task=task, project_hint=last["project"],
                             session=getattr(assistant, "session", None))
    if "error" in out or "question" in out:
        return err(out.get("error") or out.get("question"), module="coding")
    _set_choice(assistant, "Start this coding-agent run?", out["choices"], message)
    return ok(f"Last unfinished: **{last['id']}** — {last['status']} ({res.get('reason', '')}).\n\n" + out["text"]
              + "\n\nReply **yes** to start or **no** to drop it.", module="coding", type="clarification")


@register_action("coding_project_which", module="coding",
                 description="Which project we were working on — from records", info=True)
def coding_project_which(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import projects, runs

    session = getattr(assistant, "session", None)
    where = projects.resolve("", session=session)
    lines = []
    if "project" in where:
        lines.append(f"Active project: **{where['project']['title']}** ({where['how']}).")
    recent = runs.list_runs(limit=1)
    if recent:
        r = recent[0]
        lines.append(f"Most recent coding-agent run: {r['project']} — {r['status']} ({r['task'][:80]}).")
    try:
        from jarvis.continuity import store

        recs = [x for x in store.list_records(limit=20) if x.get("project")]
        if recs:
            lines.append(f"Latest project-tagged conversation record: {recs[0]['project']} — {recs[0]['text'][:100]}")
    except Exception:
        pass
    if not lines:
        return ok("I don't have a record of a current project: no active project is set and no coding runs or "
                  "project-tagged notes exist.", module="coding")
    return ok("\n".join(lines), module="coding")


@register_action("coding_agent_run_step", module="coding", description="Mission step: execute an approved agent run")
def coding_agent_run_step(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import runs

    return runs.execute_step(str(params.get("run_id") or ""))


# ---------------------------------------------------------------- Phase 6: promotion & history


@register_action("coding_promotion_propose", module="coding",
                 description="Review an agent run's changes for promotion into the real project (does not apply)",
                 info=True)
def coding_promotion_propose(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import promotion, runs

    run_id = str(params.get("run_id") or "")
    if not run_id:
        verified = [r for r in runs.list_runs(limit=20) if r["status"] == "verified"]
        if len(verified) != 1:
            return err("Which run? " + (", ".join(r["id"] for r in verified[:5]) or "No verified runs to promote."),
                       module="coding")
        run_id = verified[0]["id"]
    try:
        p = promotion.propose(run_id, allow_unverified=bool(params.get("allow_unverified")))
    except promotion.PromotionError as exc:
        return err(f"Can't promote: {exc}", module="coding")
    text = promotion.summary_text(p)
    if p["status"] != promotion.PROPOSED:
        return err(text, module="coding", error_kind="promotion_blocked", promotion=p)
    token = promotion.approval_token(p["id"])
    _set_choice(assistant, "Apply these changes to the project?", [
        {"label": "Yes", "intent": {"action": "coding_promotion_apply",
                                    "params": {"promotion_id": p["id"], "approval_token": token}}},
        {"label": "No", "intent": {"action": "coding_promotion_reject", "params": {"promotion_id": p["id"]}}},
    ], message)
    return ok(text + "\n\nApply these exact changes? Reply **yes** or **no**. (Approving the agent's plan earlier "
              "did not approve this.)", module="coding", type="clarification", promotion=p, choices=["Yes", "No"])


@register_action("coding_promotion_apply", module="coding",
                 description="Apply an owner-approved promotion to the project's working tree")
def coding_promotion_apply(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import promotion

    pid = str(params.get("promotion_id") or "")
    p = promotion.get(pid) if pid else None
    if not p:
        return err("There's no such promotion.", module="coding")
    token = str(params.get("approval_token") or "")
    if p["status"] == promotion.PROPOSED and not token:
        return err("That promotion hasn't been approved.", module="coding", error_kind="approval_required")
    try:
        out = promotion.apply(pid, token=token, via="chat_confirmation")
    except promotion.PromotionError as exc:
        return err(f"Not applied: {exc}", module="coding", error_kind="policy_denied")
    res = out.get("result") or {}
    if out["status"] != promotion.APPLIED:
        return err(f"Promotion {pid}: {out['status']} — {res.get('reason')}", module="coding", promotion=out)
    return ok(f"Applied promotion **{pid}** to {out['destination']} (working tree only — not committed or pushed). "
              f"{res.get('reason')}.\n\nRollback: {res.get('rollback')}", module="coding", promotion=out)


@register_action("coding_promotion_reject", module="coding", description="Reject a proposed promotion", info=True)
def coding_promotion_reject(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import promotion

    if pid := str(params.get("promotion_id") or ""):
        promotion.reject(pid)
    return ok("Okay — nothing was applied.", module="coding")


@register_action("coding_promotion_rollback", module="coding", description="Roll back an applied promotion")
def coding_promotion_rollback(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import promotion

    pid = str(params.get("promotion_id") or "")
    if not pid:
        applied = promotion.list_promotions(status=promotion.APPLIED, limit=5)
        if len(applied) != 1:
            return err("Which promotion? " + (", ".join(p["id"] for p in applied) or "None is applied."), module="coding")
        pid = applied[0]["id"]
    try:
        out = promotion.rollback(pid)
    except promotion.PromotionError as exc:
        return err(f"Not rolled back: {exc}", module="coding")
    return ok(f"Rolled back promotion {pid}: restored {', '.join(out['result'].get('restored') or [])}.",
              module="coding")


@register_action("coding_approvals_pending", module="coding",
                 description="Coding plans, promotions and verified changes awaiting the owner", info=True)
def coding_approvals_pending(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import history

    return ok(history.awaiting_approval(), module="coding")


@register_action("coding_project_activity", module="coding",
                 description="What we were doing on a project — from receipts and records", info=True)
def coding_project_activity(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import history, projects

    where = projects.resolve(str(params.get("project") or message), session=getattr(assistant, "session", None))
    if "unregistered" in where:
        return err(f"{projects.TITLES[where['unregistered']]} isn't registered as a project.", module="coding")
    if "project" not in where:
        return err("Which project?", module="coding")
    p = where["project"]
    return ok(history.project_activity(p["slug"], p["title"]), module="coding")


@register_action("coding_agent_changes", module="coding",
                 description="What an agent actually changed (git), separate from what it claimed", info=True)
def coding_agent_changes(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import discovery, history, projects

    agent = str(params.get("agent") or discovery.resolve_agent_name(message))
    where = projects.resolve(message) if projects.known_key(message) else {}
    slug = (where.get("project") or {}).get("slug", "")
    return ok(history.agent_work(agent, project=slug, text=message), module="coding")


@register_action("coding_agent_tests", module="coding",
                 description="What an agent tested before reporting success, and what ARIA verified", info=True)
def coding_agent_tests(assistant, params: dict, message: str) -> dict:
    from jarvis.coding_agents import discovery, history

    agent = str(params.get("agent") or discovery.resolve_agent_name(message))
    if not agent:
        return err("Which agent — Codex, Claude Code or Antigravity?", module="coding")
    return ok(history.agent_tests(agent), module="coding")
