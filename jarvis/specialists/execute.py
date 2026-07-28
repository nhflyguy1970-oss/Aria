"""Deep specialist execution — real Aria organs, honest failures."""

from __future__ import annotations

import logging
from typing import Any

from jarvis.specialists.catalog import get_specialist
from jarvis.specialists.params import build_params
from jarvis.specialists.scratchpad import SharedScratchpad

log = logging.getLogger("jarvis.specialists.execute")


def run_specialist(
    assistant: Any,
    specialist_id: str,
    goal: str,
    pad: SharedScratchpad,
    *,
    extras: dict[str, Any] | None = None,
    approve_writes: bool = False,
) -> dict[str, Any]:
    meta = get_specialist(specialist_id)
    if not meta:
        return {
            "ok": False,
            "agent": specialist_id,
            "error": f"Unknown specialist '{specialist_id}'",
            "recovered": False,
            "missing": True,
        }

    sid = meta["id"]
    if not meta.get("read_only") and not approve_writes:
        return {
            "ok": False,
            "agent": sid,
            "error": f"Write specialist '{sid}' requires write approval",
            "permission_required": True,
            "recovered": False,
            "status": "permission_required",
        }

    params = build_params(sid, goal, pad, extras)
    pad.add_reasoning(sid, f"Params synthesized for {sid}: {list(params.keys())}")

    try:
        if sid == "coder":
            result = _run_coder(assistant, goal, params)
        elif sid == "vision":
            result = _run_vision(assistant, params, goal)
        elif sid == "writer":
            result = _run_writer(goal, pad, params)
        elif sid == "planner":
            result = _run_planner(assistant, goal, params)
        elif sid == "researcher":
            result = _run_researcher(assistant, goal, params)
        elif sid == "memory":
            result = _call(assistant, "memory_search", params, goal)
        elif sid == "documents":
            result = _run_documents(assistant, goal, params)
        elif sid == "graph":
            result = _run_graph(goal, params)
        elif sid in ("critic", "reviewer"):
            result = _run_critic(assistant, goal, pad, params)
        elif sid == "home":
            result = _call(assistant, "ha_status", params, goal)
        elif sid == "voice":
            result = _call(assistant, "voice_smoke_test", params, goal)
        elif sid == "operations":
            result = _run_operations(assistant, goal, params)
        elif sid == "automation":
            result = _run_automation_status()
        else:
            result = {"ok": False, "error": f"No deep handler for {sid}", "missing": True}
    except Exception as exc:
        log.exception("specialist %s failed", sid)
        return {
            "ok": False,
            "agent": sid,
            "role": meta.get("role"),
            "error": str(exc),
            "recovered": False,
            "organ": meta.get("organ"),
        }

    ok = bool(result.get("ok", False))
    message = str(result.get("message") or result.get("summary") or result.get("draft") or result.get("error") or "")[
        :4000
    ]
    return {
        "ok": ok,
        "agent": sid,
        "name": meta.get("name"),
        "role": meta.get("role"),
        "organ": meta.get("organ"),
        "action": result.get("action") or sid,
        "message": message,
        "data": {k: v for k, v in result.items() if k not in ("message",)},
        "recovered": False,  # only engine may set recovered for true recovery
        "permissions": meta.get("permissions") or [],
        "read_only": bool(meta.get("read_only")),
        "missing": bool(result.get("missing")),
        "permission_required": bool(result.get("permission_required")),
    }


def _call(assistant: Any, action: str, params: dict[str, Any], goal: str) -> dict[str, Any]:
    from jarvis.handlers.registry import call_action, has_action

    if not has_action(action):
        return {"ok": False, "error": f"Action '{action}' not registered", "missing": True, "action": action}
    result = call_action(assistant, action, params, goal)
    if not isinstance(result, dict):
        return {"ok": True, "message": str(result), "action": action}
    result.setdefault("action", action)
    return result


def _run_coder(assistant: Any, goal: str, params: dict[str, Any]) -> dict[str, Any]:
    # Prefer CodingAgent when available
    try:
        from jarvis.coding_agent import CodingAgent

        agent = CodingAgent(assistant)
        # Use a bounded diagnose/read oriented call if API exists
        run = getattr(agent, "run", None) or getattr(agent, "plan_and_run", None)
        if callable(run):
            out = run(goal)
            if isinstance(out, dict):
                out.setdefault("action", "coding_agent")
                out.setdefault("ok", bool(out.get("ok", True)))
                return out
            return {"ok": True, "message": str(out)[:2000], "action": "coding_agent"}
    except Exception as exc:
        log.debug("CodingAgent unavailable: %s", exc)

    # Fallback: coding_read then optional diagnose via call_action
    read = _call(assistant, "coding_read", params, goal)
    if read.get("missing"):
        return read
    msg = read.get("message") or ""
    return {
        "ok": bool(read.get("ok", True)),
        "message": f"[coding_read fallback] {msg}",
        "action": "coding_read",
        "data": read,
        "delegated": False,
        "note": "CodingAgent not available; used coding_read.",
    }


def _run_vision(assistant: Any, params: dict[str, Any], goal: str) -> dict[str, Any]:
    path = str(params.get("path") or "")
    if not path:
        return {
            "ok": False,
            "error": "Vision specialist requires params.path (image file)",
            "missing": False,
            "action": "describe_image",
        }
    if params.get("ocr"):
        return _call(assistant, "ocr_image", {"path": path}, goal)
    return _call(assistant, "describe_image", {"path": path}, goal)


def _run_writer(goal: str, pad: SharedScratchpad, params: dict[str, Any]) -> dict[str, Any]:
    # Draft only — never auto journal_log
    prior = "\n".join(n["text"] for n in pad.notes[-3:])
    draft = (
        f"# Draft\n\n**Goal:** {goal}\n\n"
        f"## Summary\n\nBased on specialist context, here is a draft response:\n\n"
        f"{prior[:2500] if prior else '_No prior notes — draft skeleton only._'}\n\n"
        f"## Next steps\n\n- Review this draft in Chat\n- Save to Journal only if you confirm\n"
    )
    return {
        "ok": True,
        "draft": draft,
        "message": draft[:1500],
        "action": "draft_generate",
        "journal_written": False,
    }


def _run_planner(assistant: Any, goal: str, params: dict[str, Any]) -> dict[str, Any]:
    # Try structured planner store first
    try:
        from jarvis.planner_store import load_planner

        planner = load_planner()
        title = params.get("title") or goal[:120]
        _ = title
        # Don't auto-create — return structured plan proposal
        tasks = []
        for i, line in enumerate(_split_steps(goal), 1):
            tasks.append({"n": i, "title": line})
        return {
            "ok": True,
            "message": "## Proposed plan\n\n" + "\n".join(f"{t['n']}. {t['title']}" for t in tasks),
            "action": "planner_propose",
            "proposed_tasks": tasks,
            "planner_enabled": bool(planner.get("enabled")),
            "note": "Tasks proposed only — not auto-added. Confirm in Planner to save.",
        }
    except Exception:
        pass
    return _call(assistant, "plan_create", params, goal)


def _split_steps(goal: str) -> list[str]:
    parts = [p.strip(" -•\t") for p in goal.replace(";", "\n").split("\n") if p.strip()]
    if len(parts) >= 2:
        return parts[:8]
    # synthetic breakdown
    return [
        f"Clarify: {goal[:80]}",
        "Gather context from memory/documents",
        "Execute primary work",
        "Verify and summarize",
    ]


def _run_researcher(assistant: Any, goal: str, params: dict[str, Any]) -> dict[str, Any]:
    parts = []
    ok_any = False
    data: dict[str, Any] = {}
    for action in ("unified_search", "document_search", "memory_search"):
        r = _call(assistant, action, {**params, "query": goal}, goal)
        if r.get("missing"):
            continue
        if r.get("ok", True):
            ok_any = True
        parts.append(f"### {action}\n{r.get('message') or ''}")
        data[action] = r
    if not parts:
        return {"ok": False, "error": "No search actions available", "missing": True}
    return {"ok": ok_any, "message": "\n\n".join(parts)[:4000], "action": "research_bundle", "data": data}


def _run_documents(assistant: Any, goal: str, params: dict[str, Any]) -> dict[str, Any]:
    r = _call(assistant, "document_search", params, goal)
    if r.get("missing"):
        # try hybrid rag
        try:
            from jarvis.intelligence.hybrid_rag import hybrid_search

            hs = hybrid_search(goal, limit=int(params.get("limit") or 8))
            return {
                "ok": bool(hs.get("ok")),
                "message": str(hs.get("summary") or hs)[:2000],
                "action": "hybrid_rag",
                "data": hs,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc), "missing": True}
    return r


def _run_graph(goal: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        from jarvis.intelligence.knowledge_graph import search_graph

        out = search_graph(goal, limit=int(params.get("limit") or 8))
        return {
            "ok": bool(out.get("ok", True)),
            "message": str(out.get("summary") or out)[:2000],
            "action": "graph_search",
            "data": out,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "missing": True, "action": "graph_search"}


def _run_critic(assistant: Any, goal: str, pad: SharedScratchpad, params: dict[str, Any]) -> dict[str, Any]:
    notes = "\n".join(f"- {n['agent']}: {n['text'][:200]}" for n in pad.notes[-5:])
    critique = (
        f"## Critique\n\nGoal: {goal}\n\n### Observations\n{notes or '_No notes yet._'}\n\n"
        "### Risks\n- Verify claims against sources\n- Confirm write actions before applying\n"
    )
    test = _call(assistant, "run_tests", params, goal)
    if not test.get("missing"):
        critique += f"\n### Tests\n{test.get('message') or test.get('error') or ''}\n"
    return {
        "ok": True,
        "message": critique[:3000],
        "action": "critique",
        "tests": test if not test.get("missing") else None,
    }


def _run_operations(assistant: Any, goal: str, params: dict[str, Any]) -> dict[str, Any]:
    for action in ("workstation_diagnose", "workstation_status"):
        r = _call(assistant, action, params, goal)
        if not r.get("missing"):
            return r
    return {"ok": False, "error": "No workstation actions available", "missing": True}


def _run_automation_status() -> dict[str, Any]:
    try:
        from jarvis.automation.home import home_snapshot

        snap = home_snapshot()
        s = snap.get("summary") or {}
        msg = (
            f"Automation: engine={'running' if s.get('engine_running') else 'stopped'}; "
            f"rules {s.get('rules_enabled', 0)} enabled; failures {s.get('failures_recent', 0)}."
        )
        return {"ok": True, "message": msg, "action": "automation_status", "data": s}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "missing": True}
