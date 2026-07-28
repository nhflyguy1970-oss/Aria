"""Chat handlers for Specialist Team runs — confirm before execute."""

from __future__ import annotations

import re

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action("specialists_propose", module="general", description="Propose a specialist team", info=True)
def specialists_propose(assistant, params: dict, message: str) -> dict:
    from jarvis.specialists.engine import propose_team

    goal = str(params.get("goal") or message or "").strip()
    if not goal:
        return err("What should the specialist team work on?", module="general")
    proposal = propose_team(goal, specialists=params.get("specialists"), use_llm=bool(params.get("use_llm")))
    lines = [
        "**Proposed Specialist Team** (review — nothing has run yet)",
        f"Goal: {goal}",
        f"Team: {', '.join(proposal.get('team') or [])}",
        f"Why: {proposal.get('reasoning')}",
        f"Expected: {proposal.get('expected_output')}",
        "",
        "Say **confirm specialists** or **run specialists confirm** to execute.",
        "Open Automation/Job Center to inspect runs after confirmation.",
    ]
    return ok("\n".join(lines), module="general", proposal=proposal, confirmation_required=True)


@register_action("specialists_run", module="general", description="Run a confirmed specialist team")
def specialists_run(assistant, params: dict, message: str) -> dict:
    from jarvis.specialists.engine import run_team

    goal = str(params.get("goal") or "").strip()
    confirm = bool(params.get("confirm"))
    if not confirm:
        return specialists_propose(assistant, params, message)
    if not goal:
        return err("Missing goal for specialist run.", module="general")
    result = run_team(
        assistant,
        goal,
        specialists=params.get("specialists") or params.get("team"),
        confirm=True,
        approve_writes=bool(params.get("approve_writes")),
        parallel_readers=bool(params.get("parallel_readers")),
        critic_loop=bool(params.get("critic_loop")),
        trigger="chat",
        emit_bridges=True,
    )
    summary = result.get("synthesis") or result.get("summary") or result.get("status")
    return ok(
        f"**Specialist Team:** `{result.get('status')}`\n\n{summary}\n\n"
        f"Run `{result.get('run_id')}` · Job `{result.get('job_id')}`",
        module="general",
        result=result,
    )


@register_action("specialists_history", module="general", description="List specialist team runs", info=True)
def specialists_history(assistant, params: dict, message: str) -> dict:
    from jarvis.specialists.history import list_runs

    runs = list_runs(limit=10, q=str(params.get("q") or ""))
    if not runs:
        return ok("No specialist team runs yet.", module="general")
    lines = [f"· `{r.get('id')}` — {r.get('status')}: {(r.get('goal') or '')[:60]}" for r in runs]
    return ok("**Recent Specialist Team runs**\n\n" + "\n".join(lines), module="general", runs=runs)


@register_action("specialists_gallery", module="general", description="List specialists", info=True)
def specialists_gallery(assistant, params: dict, message: str) -> dict:
    from jarvis.specialists.catalog import list_gallery

    lines = [f"· **{g['name']}** (`{g['id']}`) — {g.get('description')}" for g in list_gallery()]
    return ok("**Specialist gallery**\n\n" + "\n".join(lines), module="general", gallery=list_gallery())


def parse_specialists_intent(message: str) -> dict | None:
    lower = (message or "").strip().lower()
    if not lower:
        return None
    if re.search(r"\b(list|show)\s+specialists?\b", lower) or "specialist gallery" in lower:
        return {"action": "specialists_gallery", "params": {}}
    if re.search(r"\bspecialist(s)?\s+(history|runs)\b", lower) or "team runs" in lower:
        return {"action": "specialists_history", "params": {}}
    m = re.search(
        r"(?:run specialists?(?:\s+for)?|research this|have the coding specialist|ask the writer|"
        r"explain with specialists?|specialist team)\s*:?\s*(.*)$",
        lower,
    )
    if m or re.search(r"\bpropose\s+specialists?\b", lower):
        goal = (m.group(1) if m else "").strip() or re.sub(
            r".*?(?:specialists?|research this|writer|coding specialist)\s*:?\s*",
            "",
            message,
            flags=re.I,
        ).strip()
        confirm = bool(re.search(r"\bconfirm\b", lower))
        if confirm:
            return {
                "action": "specialists_run",
                "params": {"goal": goal or message, "confirm": True},
            }
        return {"action": "specialists_propose", "params": {"goal": goal or message}}
    if re.search(r"\bconfirm\s+specialists?\b", lower):
        # Need goal from context — ask
        return {
            "action": "specialists_propose",
            "params": {"goal": "Confirm requested — please repeat the goal with: run specialists confirm: <goal>"},
        }
    return None
