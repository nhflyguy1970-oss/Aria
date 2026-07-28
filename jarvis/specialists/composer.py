"""Team composition — heuristic + optional LLM-assisted suggestions (confirm required)."""

from __future__ import annotations

import re
from typing import Any

from jarvis.specialists.catalog import ROLE_TO_SPECIALIST, get_specialist, list_gallery, normalize_team


def compose_team(goal: str, *, specialists: list[str] | None = None, use_llm: bool = False) -> dict[str, Any]:
    """Propose a specialist team. Never executes."""
    if specialists:
        team = normalize_team(specialists)
        reason = "Explicit specialist list provided by user."
    else:
        team, reason = _heuristic_team(goal)

    if use_llm:
        llm_extra = _llm_suggest(goal)
        if llm_extra.get("team"):
            # Merge unique, preserve heuristic order first
            for s in llm_extra["team"]:
                if s not in team:
                    team.append(s)
            team = normalize_team(team)[:6]
            reason = (reason + " " + str(llm_extra.get("reason") or "")).strip()

    detail = []
    for sid in team:
        meta = get_specialist(sid)
        if meta:
            detail.append(
                {
                    "id": sid,
                    "name": meta.get("name"),
                    "description": meta.get("description"),
                    "permissions": meta.get("permissions") or [],
                    "read_only": bool(meta.get("read_only")),
                    "organ": meta.get("organ"),
                }
            )

    return {
        "ok": True,
        "goal": goal,
        "team": team,
        "specialists": team,
        "detail": detail,
        "reasoning": reason,
        "expected_output": _expected(team),
        "confirmation_required": True,
        "auto_run": False,
        "gallery_hint": [g["id"] for g in list_gallery()[:8]],
    }


def _heuristic_team(goal: str) -> tuple[list[str], str]:
    lower = (goal or "").lower()
    team: list[str] = []
    reasons: list[str] = []

    def add(sid: str, why: str) -> None:
        if sid not in team:
            team.append(sid)
            reasons.append(why)

    if re.search(r"\b(plan|roadmap|break down|steps)\b", lower):
        add("planner", "Goal mentions planning.")
    if re.search(r"\b(research|investigate|find out|search|learn about)\b", lower):
        add("researcher", "Goal mentions research.")
    if re.search(r"\b(code|implement|refactor|bug|fix|debug|python|file)\b", lower):
        add("coder", "Goal mentions coding.")
    if re.search(r"\b(document|readme|summarize|write|draft)\b", lower):
        add("writer", "Goal mentions writing/docs.")
    if re.search(r"\b(test|verify|qa|lint|regress)\b", lower):
        add("critic", "Goal mentions QA/tests.")
    if re.search(r"\b(remember|memory|recall)\b", lower):
        add("memory", "Goal mentions memory.")
    if re.search(r"\b(pdf|docx|document|cite)\b", lower):
        add("documents", "Goal mentions documents.")
    if re.search(r"\b(graph|connection|entity|relationship)\b", lower):
        add("graph", "Goal mentions knowledge graph.")
    if re.search(r"\b(image|screenshot|ocr|vision|photo)\b", lower):
        add("vision", "Goal mentions vision.")
    if re.search(r"\b(light|home assistant|thermostat|scene)\b", lower):
        add("home", "Goal mentions home.")
    if re.search(r"\b(status|diagnose|recover|workstation)\b", lower):
        add("operations", "Goal mentions operations.")
    if re.search(r"\b(automation|schedule|rule)\b", lower):
        add("automation", "Goal mentions automation.")

    if not team:
        team = ["researcher", "planner"]
        reasons.append("Default research + planner team.")

    # Always offer synthesis as post-step (engine adds)
    return normalize_team(team), " ".join(reasons)


def _llm_suggest(goal: str) -> dict[str, Any]:
    """Best-effort optional LLM suggestion; fails soft to empty."""
    try:
        from jarvis.intelligence.reasoning import reason

        out = reason(f"Suggest up to 4 specialist roles for this Aria OS goal (planner,researcher,coder,writer,critic,memory,documents,graph,vision,home,operations): {goal}")
        text = str(out.get("summary") or out.get("message") or out.get("plan") or "")
        found = []
        for sid in (
            "planner",
            "researcher",
            "coder",
            "writer",
            "critic",
            "memory",
            "documents",
            "graph",
            "vision",
            "home",
            "operations",
        ):
            if sid in text.lower():
                found.append(sid)
        return {"team": found[:4], "reason": "LLM-assisted composition (review before run)."}
    except Exception:
        return {}


def _expected(team: list[str]) -> str:
    names = []
    for sid in team:
        meta = get_specialist(sid)
        names.append((meta or {}).get("name") or sid)
    return f"Coordinated outputs from: {', '.join(names)}, then a final synthesis."


# Compat for old suggest_agents role lists
def suggest_roles_legacy(goal: str) -> list[str]:
    team = compose_team(goal)["team"]
    roles = []
    for sid in team:
        meta = get_specialist(sid)
        if meta:
            roles.append(meta.get("role") or sid)
    return roles or ["research", "planning"]


def map_roles_to_specialists(roles: list[str]) -> list[str]:
    out = []
    for r in roles:
        out.append(ROLE_TO_SPECIALIST.get(r, r))
    return normalize_team(out)
