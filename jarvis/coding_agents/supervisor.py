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


def select_agent(kind: str, mode: str, *, named: str = "") -> dict[str, Any]:
    statuses = discovery.discover()
    if named:
        st = statuses.get(named)
        if not st or not st.installed:
            return {"error": f"{discovery.LABELS.get(named, named)} is not installed."}
        if not st.usable:
            why = "; ".join(st.notes + (["missing flags: " + ", ".join(st.missing_flags)] if st.missing_flags else [])
                            + ([f"signed out ({st.auth.get('evidence')})"] if st.auth.get("state") == "logged_out" else []))
            return {"error": f"{st.label} can't be used: {why or 'not ready'}."}
        if mode not in st.modes:
            return {"error": f"{st.label} does not support {mode.replace('_', '-')} work."}
        return {"agent": named, "why": "named in the request"}
    scores = (measured().get("by_category") or {}).get(kind) or {}
    usable = [a for a, st in statuses.items() if st.usable and mode in st.modes]
    if not usable:
        return {"error": "No coding agent is installed, signed in and able to do this."}
    ranked = sorted(
        (a for a in usable if a in scores),
        key=lambda a: (-float(scores[a].get("verified_pct") or 0), float(scores[a].get("p50_s") or 1e9)),
    )
    if ranked:
        best = ranked[0]
        s = scores[best]
        return {"agent": best, "why": f"best measured on '{kind}' fixtures ({s.get('verified_pct')}% verified, "
                                      f"p50 {s.get('p50_s')}s; n={s.get('n')})"}
    order = ["codex", "claude_code", "antigravity"]
    best = next(a for a in order if a in usable)
    return {"agent": best, "why": f"no benchmark result for '{kind}' yet — default order, unmeasured"}


def propose(message: str, *, agent_hint: str = "", task: str = "", session=None, project_hint: str = "") -> dict[str, Any]:
    """Steps 1–5. Returns {"plan", "text", "choices"} or {"question"} / {"error"}."""
    task = (task or message or "").strip()
    named = agent_hint or discovery.resolve_agent_name(message)
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
    choice = select_agent(kind, mode, named=named)
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
    return {
        "plan": plan,
        "text": "\n".join(lines),
        "choices": [
            {"label": "Yes", "intent": {"action": "coding_agent_execute",
                                        "params": {"plan_id": plan["id"], "approval_token": token}}},
            {"label": "No", "intent": {"action": "coding_agent_reject", "params": {"plan_id": plan["id"]}}},
        ],
    }


def resume_candidates(project: str = "") -> list[dict[str, Any]]:
    """Unfinished work from receipts: interrupted, timed-out, failed or unverified runs."""
    unfinished = {"interrupted", "timeout", "failed", "tests_failed", "changes_unverified", "no_changes"}
    return [r for r in runs.list_runs(project=project, limit=20) if r["status"] in unfinished]
