"""Answers about coding work, built from receipts — never from an agent's say-so.

One state taxonomy for everything a coding request goes through:

  proposed            a plan or promotion awaiting the owner
  approved            approved, not started
  in_progress         an agent is running
  completed           agent finished a read-only task (findings unverified)
  verified            changes made and ARIA's own tests passed
  awaiting_promotion  verified/accepted changes not yet in the real project
  applied             promoted into the project's working tree
  unverified          changes made but nothing verified them
  failed / cancelled / interrupted / rejected / reverted
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

from jarvis.coding_agents import contract, discovery, runs

STATE_LABELS = {
    "proposed": "proposed (awaiting your approval)",
    "approved": "approved, not started",
    "in_progress": "in progress",
    "completed": "agent finished (findings unverified)",
    "verified": "independently verified",
    "awaiting_promotion": "verified, awaiting promotion",
    "applied": "applied to the project",
    "unverified": "changed, not verified",
    "failed": "failed",
    "cancelled": "cancelled",
    "interrupted": "interrupted",
    "rejected": "rejected",
    "reverted": "rolled back",
}


def run_state(run: dict[str, Any], promotion: dict[str, Any] | None = None) -> str:
    st = run.get("status")
    if st in (runs.PENDING, runs.RUNNING):
        return "in_progress"
    if promotion:
        ps = promotion.get("status")
        if ps == "applied":
            return "applied"
        if ps == "reverted":
            return "reverted"
        if ps in ("proposed", "approved"):
            return "awaiting_promotion"
    if st == contract.VERIFIED:
        return "awaiting_promotion"
    if st == contract.COMPLETED:
        return "completed"
    if st == contract.UNVERIFIED:
        return "unverified"
    if st in (contract.CANCELLED, contract.INTERRUPTED):
        return st
    return "failed"


def _promotions_by_run() -> dict[str, dict[str, Any]]:
    try:
        from jarvis.coding_agents import promotion

        return {p["run_id"]: p for p in promotion.list_promotions(limit=200)}
    except Exception:
        return {}


def window(text: str) -> tuple[float, float, str]:
    low = (text or "").lower()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if "yesterday" in low:
        return (today - timedelta(days=1)).timestamp(), today.timestamp(), "yesterday"
    if "today" in low:
        return today.timestamp(), time.time() + 1, "today"
    if "week" in low:
        return (today - timedelta(days=7)).timestamp(), time.time() + 1, "in the last 7 days"
    return 0.0, time.time() + 1, "on record"


def _label(agent: str) -> str:
    return discovery.LABELS.get(agent, agent)


def runs_for(*, project: str = "", agent: str = "", since: float = 0.0, until: float | None = None,
             limit: int = 50) -> list[dict[str, Any]]:
    out = [r for r in runs.list_runs(since=since, project=project, limit=200)
           if (not agent or r["agent"] == agent) and (until is None or (r.get("started_at") or 0) < until)]
    return out[:limit]


def project_activity(slug: str, title: str) -> str:
    """'What were we doing with BlackFly?'"""
    proms = _promotions_by_run()
    lines = [f"**{title}** — from execution receipts and conversation records:"]
    with runs._conn() as conn:
        plans = [dict(r) for r in conn.execute(
            "SELECT id, agent, task, status, created_at FROM plans WHERE project=? ORDER BY created_at DESC LIMIT 5",
            (slug,)).fetchall()]
    rs = runs_for(project=slug, limit=8)
    for r in rs:
        when = datetime.fromtimestamp(r["started_at"]).strftime("%a %d %b %H:%M") if r.get("started_at") else "?"
        lines.append(f"- {when} · {_label(r['agent'])} · {STATE_LABELS[run_state(r, proms.get(r['id']))]} — {r['task'][:90]}")
    for p in plans:
        if p["status"] == runs.PROPOSED:
            lines.append(f"- plan {p['id']} for {_label(p['agent'])} — proposed, awaiting approval: {p['task'][:80]}")
    try:
        from jarvis.continuity import store

        recs = [x for x in store.list_records(limit=200) if x.get("project") == slug][:5]
        for x in recs:
            lines.append(f"- note ({x['kind']}, {x['actor']}, {x['status']}): {x['text'].splitlines()[0][:110]}")
    except Exception:
        pass
    if len(lines) == 1:
        return f"I have no record of any work on {title} yet — no agent plans, runs or project-tagged notes."
    return "\n".join(lines)


def agent_work(agent: str, *, project: str = "", text: str = "") -> str:
    """'Which coding agent worked on ARIA yesterday?' / 'What changes did Codex actually make?'"""
    start, end, label = window(text)
    rs = runs_for(project=project, agent=agent, since=start, until=end, limit=10)
    who = _label(agent) if agent else "coding agents"
    where = f" on {project}" if project else ""
    if not rs:
        return f"No {who} runs{where} {label}. (Source: execution receipts.)"
    proms = _promotions_by_run()
    lines = [f"**{who}{where} {label}** (git-observed changes; claims marked as claims):"]
    for r in rs:
        res = r.get("result") or {}
        files = [f["path"] for f in (res.get("changed") or {}).get("files") or []]
        when = datetime.fromtimestamp(r["started_at"]).strftime("%a %H:%M") if r.get("started_at") else "?"
        lines.append(f"- {when} · {_label(r['agent'])} · {r['project']} · {STATE_LABELS[run_state(r, proms.get(r['id']))]}"
                     f" — {r['task'][:80]}")
        lines.append(f"  - actually changed: {', '.join(files) if files else 'nothing'}"
                     + (f" ({(res.get('changed') or {}).get('stat', '').splitlines()[-1].strip()})"
                        if files and (res.get('changed') or {}).get('stat') else ""))
        if res.get("unverified"):
            lines.append(f"  - agent claimed (unverified): {' | '.join(res['unverified'][:2])}")
    return "\n".join(lines)


def agent_tests(agent: str, *, project: str = "") -> str:
    """'What did Claude test before reporting success?'"""
    rs = [r for r in runs_for(agent=agent, project=project, limit=20) if r["status"] in contract.TERMINAL]
    if not rs:
        return f"No finished {_label(agent)} runs on record."
    r = rs[0]
    res = r.get("result") or {}
    cmds = (res.get("attempted") or {}).get("commands") or []
    tests_by_agent = [c for c in cmds if any(k in c.get("command", "") for k in ("pytest", "unittest", "npm test", "make test", "test"))]
    lines = [f"**{_label(r['agent'])} — run {r['id']}** ({r['status']}, {r['task'][:70]}):"]
    if tests_by_agent:
        lines.append("- the agent reports running: " + "; ".join(c["command"][:80] for c in tests_by_agent[:4])
                     + " (its own report — not independently checked)")
    else:
        lines.append("- the agent ran no tests itself"
                     + (" (Claude Code isn't given a shell under ARIA)" if r["agent"] == "claude_code" else ""))
    for t in res.get("tests_run") or []:
        lines.append(f"- ARIA ran `{t.get('command')}`: {'passed' if t.get('passed') else 'FAILED'} (exit {t.get('exit_code')})")
    if not res.get("tests_run"):
        lines.append("- ARIA ran no tests for this run" + (" (read-only task)" if r["mode"] == "read_only" else ""))
    if res.get("contradicted_claims"):
        lines.append("- claims contradicted by ARIA's tests: " + " | ".join(res["contradicted_claims"][:2]))
    return "\n".join(lines)


def awaiting_approval() -> str:
    """'Which changes are awaiting my approval?'"""
    lines = []
    with runs._conn() as conn:
        plans = [dict(r) for r in conn.execute(
            "SELECT id, agent, project, task, created_at FROM plans WHERE status=? ORDER BY created_at DESC LIMIT 10",
            (runs.PROPOSED,)).fetchall()]
    for p in plans:
        lines.append(f"- **coding plan** {p['id']}: {_label(p['agent'])} on {p['project']} — {p['task'][:80]}")
    proms = _promotions_by_run()
    for p in proms.values():
        if p["status"] in ("proposed", "approved"):
            lines.append(f"- **change promotion** {p['id']} into {p['project']} ({len(p['manifest'])} file(s)) — "
                         f"{'approved, not applied' if p['status'] == 'approved' else 'awaiting your approval'}")
    for r in runs.list_runs(limit=30):
        if r["status"] == contract.VERIFIED and r["id"] not in proms:
            files = len(((r.get("result") or {}).get("changed") or {}).get("files") or [])
            lines.append(f"- **verified changes, not proposed for promotion**: run {r['id']} ({_label(r['agent'])}, "
                         f"{r['project']}, {files} file(s)) — say \"promote run {r['id']}\" to review")
    if not lines:
        return "Nothing is awaiting your approval: no proposed agent plans, promotions or unpromoted verified changes."
    return "**Awaiting your decision:**\n" + "\n".join(lines)
