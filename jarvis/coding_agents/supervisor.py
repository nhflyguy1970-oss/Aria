"""Supervised coding-agent orchestration — steps 1–5 here, 6–10 in ``runs``.

 1. interpret the request (agent named? task kind → read-only or write)
 2. resolve the project from records (``projects.resolve``) — never a guess
 3. decide whether an agent can do it (installed, signed in, not paid-API,
    supports the mode)
 4. select the agent: the one named, else the best *measured* agent for the
    task kind on the disposable-fixture benchmark, else say it is unmeasured
 5. present a concise plan; nothing runs until the owner approves it
 6–10 (``runs``): execute within the approved scope in a sandboxed
    disposable clone, enforce limits, collect git/test evidence, verify
    independently, and save a checkpoint + report to continuity.
"""

from __future__ import annotations

import json
import re
from typing import Any

from jarvis.coding_agents import discovery, projects, runs
from jarvis.coding_agents.discovery import READ_ONLY, WORKSPACE_WRITE
from jarvis.config import DATA_DIR

BENCHMARK_FILE = DATA_DIR / "coding_agent_benchmark.json"

# Task kinds (benchmark categories) and the mode each needs.
KINDS = [
    ("code_review", READ_ONLY, r"\b(?:review|look\s+over|critique|audit)\b"),
    ("bug_diagnosis", READ_ONLY, r"\b(?:investigate|diagnose|figure\s+out|find\s+out|why\s+(?:is|does|do)|root\s+cause|look\s+into|slowdown)\b"),
    ("comprehension", READ_ONLY, r"\b(?:explain|summari[sz]e|how\s+does|walk\s+me\s+through|understand|map\s+out)\b"),
    ("test_creation", WORKSPACE_WRITE, r"\b(?:write|add|create)\s+(?:a\s+|some\s+|unit\s+)?tests?\b"),
    ("refactoring", WORKSPACE_WRITE, r"\b(?:refactor|restructure|rename\s+\w+\s+across)\b"),
    ("documentation", WORKSPACE_WRITE, r"\b(?:document|update\s+the\s+(?:docs|readme)|write\s+(?:the\s+)?docs)\b"),
    ("small_repair", WORKSPACE_WRITE, r"\b(?:fix|repair|implement|add|change|update|patch|make)\b"),
]


def classify(task: str) -> tuple[str, str]:
    low = (task or "").lower()
    for kind, mode, pattern in KINDS:
        if re.search(pattern, low):
            return kind, mode
    return "comprehension", READ_ONLY


def measured() -> dict[str, Any]:
    try:
        return json.loads(BENCHMARK_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


MIN_SAMPLES = 2


def _agent_scores(agent: str, kind: str, data: dict[str, Any]) -> dict[str, Any]:
    cat = ((data.get("by_category") or {}).get(kind) or {}).get(agent)
    summ = (data.get("summary") or {}).get(agent) or {}
    return {"category": cat, "summary": summ}


def select_agent(kind: str, mode: str, *, named: str = "", project: dict[str, Any] | None = None) -> dict[str, Any]:
    """Pick an agent and say why, criterion by criterion.

    1 capabilities (mode) · 2 sign-in/availability · 3 measured correctness on this
    kind of task · 4 permission compatibility (boundary record) · 5 project
    requirements (allowed agents) · 6 time/resources · 7 reliability.
    An owner override (``named``) skips ranking but none of the checks.
    """
    statuses = discovery.discover()
    data = measured()
    allowed = list(((project or {}).get("agent_settings") or {}).get("allowed_agents") or []) or \
        list((project or {}).get("allowed_agents") or [])
    reasons: dict[str, list[str]] = {}
    eligible = []
    for agent, st in statuses.items():
        from jarvis.coding_agents import runtime
        st.execution = runtime.compatibility(agent, st.path, st.version)
        why = reasons.setdefault(agent, [])
        if not st.installed:
            why.append("not installed")
            continue
        if not st.usable:
            why.append("not usable (" + "; ".join(st.notes + st.missing_flags + [st.auth.get("state", "")]) + ")")
            continue
        if mode not in st.modes:
            why.append(f"cannot do {mode.replace('_', '-')} work")
            continue
        if allowed and agent not in allowed:
            why.append("not allowed for this project")
            continue
        summ = _agent_scores(agent, kind, data)["summary"]
        if summ.get("violations") or summ.get("outside_attempts"):
            why.append(f"boundary record: {summ.get('violations', 0)} violation(s), "
                       f"{summ.get('outside_attempts', 0)} outside-workspace attempt(s) in the benchmark")
            # Named requests cannot bypass an unresolved safety finding.
            if not st.execution.get("boundary_history_reviewed"):
                continue
        eligible.append(agent)
    if named:
        if named not in statuses:
            return {"error": f"Unknown agent {named!r}."}
        if named not in eligible:
            return {"error": f"{discovery.LABELS.get(named, named)} can't take this: {'; '.join(reasons[named])}."}
        sc = _agent_scores(named, kind, data)["category"]
        measured_note = (f"measured {sc['verified_pct']}% on '{kind}' (n={sc['n']})" if sc
                         else f"unmeasured on '{kind}'")
        return {"agent": named, "why": f"your choice (override); {measured_note}", "explanation": reasons,
                "measured": bool(sc)}
    if not eligible:
        return {"error": "No coding agent is installed, signed in, permitted and able to do this: "
                         + "; ".join(f"{a}: {', '.join(r)}" for a, r in reasons.items())}
    ranked = []
    for agent in eligible:
        sc = _agent_scores(agent, kind, data)
        cat, summ = sc["category"], sc["summary"]
        runs_n = max(1, int(summ.get("runs") or 0))
        reliability = (int(summ.get("execution_ok", summ.get("structured_ok")) or 0)
                       - int(summ.get("timeouts") or 0)) / runs_n if summ else 0.0
        enough = bool(cat) and int(cat.get("n") or 0) >= MIN_SAMPLES
        ranked.append((agent, enough, float(cat["verified_pct"]) if cat else -1.0, reliability,
                       float(cat["p50_s"]) if cat else 1e9, float(summ.get("cpu_s_total") or 0), cat))
    ranked.sort(key=lambda r: (not r[1], -r[2], -r[3], r[4], r[5]))
    best = ranked[0]
    agent, enough, pct, rel, p50, cpu, cat = best
    if not cat:
        return {"agent": agent, "why": f"no benchmark result for '{kind}' — unmeasured; chose the first eligible agent",
                "explanation": reasons, "measured": False}
    ties = [r for r in ranked[1:] if r[1] == enough and r[2] == pct]
    why = (f"{pct:.0f}% verified on '{kind}' fixtures (n={cat['n']}"
           + ("" if enough else f", fewer than {MIN_SAMPLES} samples — weak evidence") + ")"
           + (f"; tied on correctness with {', '.join(discovery.LABELS[t[0]] for t in ties)}, chosen for "
              f"{'reliability' if rel > max(t[3] for t in ties) else 'speed'} (p50 {p50:.0f}s)" if ties else
              f"; p50 {p50:.0f}s"))
    for other in ranked[1:]:
        reasons[other[0]].append(f"ranked below: {other[2]:.0f}% on '{kind}'" if other[6] else "unmeasured on this task")
    return {"agent": agent, "why": why, "explanation": reasons, "measured": enough}


def propose(message: str, *, agent_hint: str = "", task: str = "", session=None, project_hint: str = "") -> dict[str, Any]:
    """Steps 1–5. Returns {"plan", "text", "choices"} or {"question"} / {"error"}."""
    task = (task or message or "").strip()
    owner_named = discovery.resolve_agent_name(message)
    if owner_named and agent_hint and agent_hint != owner_named:
        return {"error": "Agent proposal conflicts with the explicit owner selection."}
    named = owner_named or agent_hint
    kind, mode = classify(task)
    where = projects.resolve(project_hint or message, session=session)
    if "ambiguous" in where:
        return {"question": "Which project? " + ", ".join(p["title"] for p in where["ambiguous"])}
    if "unregistered" in where:
        key = where["unregistered"]
        cand = where.get("candidate") or {}
        hint = (f" I found a likely location: `{cand['path']}` ({cand['evidence']})." if cand.get("path") else "")
        return {"error": f"{projects.TITLES[key]} isn't registered as a project in ARIA, so I won't guess where it is."
                         f"{hint} Register it (Projects → Import repository, then set its test command) and ask again."}
    if "project" not in where:
        return {"question": "Which project should the agent work on? I don't have an active project for this conversation."}
    proj = where["project"]
    choice = select_agent(kind, mode, named=named, project=proj)
    if "error" in choice:
        return {"error": choice["error"]}
    agent = choice["agent"]
    st = discovery.discover()[agent]
    plan = runs.create_plan(agent=agent, project=proj["slug"], mode=mode, task=task,
                            rationale=f"{kind}; {choice['why']}; project from {where.get('how')}")
    minutes = round(plan["timeout_s"] / 60)
    lines = [
        f"**Plan** — {st.label} ({st.version}, {st.auth.get('billing') or 'auth unknown'})",
        f"- Project: **{proj['title']}** (`{proj['path']}`, from {where.get('how')})",
        f"- Work: {kind.replace('_', ' ')} — {'read-only' if mode == READ_ONLY else 'may edit files'}",
        f"- Task: {task[:300]}",
        "- Where: a disposable copy of the committed code, sandboxed (read-only system, no push); "
        "nothing is applied to the project",
        f"- Verification: {'`' + proj['test_command'] + '` run by ARIA' if proj['test_command'] else 'no test command set — changes would stay unverified'}"
        if mode == WORKSPACE_WRITE else "- Verification: findings are reported as the agent's, unverified",
        f"- Limit: {minutes} min · Agent choice: {choice['why']}",
        "",
        "Start it?",
    ]
    token = runs.approval_token(plan["id"])
    from jarvis.coding_agents import permissions
    return {
        "plan": plan,
        "permissions": permissions.for_plan(plan["id"]),
        "text": "\n".join(lines),
        "choices": [
            {"label": "Yes", "intent": {"action": "coding_agent_execute",
                                        "params": {"plan_id": plan["id"], "approval_token": token}}},
            {"label": "No", "intent": {"action": "coding_agent_reject", "params": {"plan_id": plan["id"]}}},
        ],
    }


def propose_continuation(run: dict, *, task: str) -> dict[str, Any]:
    """Present a private-session continuation through the existing Yes/No path."""
    choice = select_agent("comprehension", run["mode"], named=run["agent"], project=projects.get(run["project"]))
    if "error" in choice:
        return choice
    try:
        plan = runs.create_resume_plan(run["id"], task=task)
    except runs.AgentRunError as exc:
        return {"error": str(exc)}
    scope = json.loads(plan["project_scope"])
    text = (
        f"**Continue Codex session** — previous run `{run['id']}` ({run['status']})\n"
        f"- Project: {run['project']} · Mode: {run['mode'].replace('_', '-')}\n"
        f"- Workspace: `{scope['resume']['workspace']}` (existing isolated copy)\n"
        f"- Task: {task[:300]}\n"
        f"- Limit: {round(plan['timeout_s'] / 60)} min; independent verification remains required.\n"
        "- A new approval covers this continuation only. Nothing is merged or pushed."
    )
    return {
        "plan": plan,
        "text": text,
        "choices": [
            {
                "label": "Yes",
                "intent": {
                    "action": "coding_agent_execute",
                    "params": {"plan_id": plan["id"], "approval_token": runs.approval_token(plan["id"])},
                },
            },
            {"label": "No", "intent": {"action": "coding_agent_reject", "params": {"plan_id": plan["id"]}}},
        ],
    }


def resume_candidates(project: str = "") -> list[dict[str, Any]]:
    """Unfinished work from receipts: interrupted, timed-out, failed or unverified runs."""
    unfinished = {"interrupted", "timeout", "failed", "tests_failed", "changes_unverified", "no_changes"}
    return [r for r in runs.list_runs(project=project, limit=20) if r["status"] in unfinished]
