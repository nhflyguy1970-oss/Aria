"""One answer to "what is ARIA doing?".

Every number here is read from the subsystem that owns it — missions, workflows,
research, coding, model health, MCP providers. Nothing is cached or recomputed,
so the status cannot drift from reality, and a subsystem that is unavailable is
reported as unavailable rather than as zero.
"""

from __future__ import annotations

import logging
from typing import Any

from jarvis.integration import lifecycle, policy

log = logging.getLogger("jarvis.integration.status")


def _safe(loader, label: str) -> tuple[Any, str]:
    """Read a subsystem, distinguishing "nothing" from "could not ask"."""
    try:
        return loader(), ""
    except Exception as exc:  # noqa: BLE001 - one subsystem must not blind the rest
        log.info("environment status: %s unavailable: %s", label, exc)
        return None, f"{type(exc).__name__}: {exc}"


def _workflows(limit: int) -> dict[str, Any]:
    from jarvis import autonomous_workflows as wf

    rows = wf.list_workflows(limit=limit)
    active = []
    for row in rows:
        state = lifecycle.unify("workflow", row["state"])
        if state in lifecycle.LIVE:
            snapshot = wf.status(row["id"]) or {}
            active.append(
                {
                    "workflow_id": row["id"],
                    "name": row["name"],
                    "state": state,
                    "subsystem_state": row["state"],
                    "current_step": snapshot.get("current_step", ""),
                    "succeeded": snapshot.get("succeeded", 0),
                    "steps_total": snapshot.get("steps_total", 0),
                    "agents": (snapshot.get("usage") or {}).get("agents", []),
                    "elapsed_s": snapshot.get("elapsed_s"),
                    "controllable": True,
                }
            )
    return {
        "total": len(rows),
        "active": active,
        "states": _count(lifecycle.unify, "workflow", (r["state"] for r in rows)),
    }


def _missions(limit: int) -> dict[str, Any]:
    from jarvis import missions

    rows = missions.list_missions(limit=limit)
    active = [
        {
            "mission_id": r["id"],
            "objective": r["objective"][:120],
            "state": lifecycle.unify("mission", r["state"]),
            "progress": f"{r['completed_steps']}/{r['total_steps']}",
        }
        for r in rows
        if lifecycle.unify("mission", r["state"]) in lifecycle.LIVE
    ]
    worker = missions.worker.status()
    return {
        "total": len(rows),
        "active": active,
        "states": _count(lifecycle.unify, "mission", (r["state"] for r in rows)),
        "worker": {
            "running": worker.get("running"),
            "pending": worker.get("pending"),
            "current": worker.get("current_mission"),
        },
    }


def _research(limit: int) -> dict[str, Any]:
    from jarvis.research import store as research_store

    rows = research_store.list_jobs(limit=limit)
    return {
        "total": len(rows),
        "active": [
            {
                # research_jobs keys its rows "id", like every other store here.
                "research_id": r["id"],
                "objective": (r.get("objective") or "")[:100],
                "state": lifecycle.unify("research", r.get("status", "")),
            }
            for r in rows
            if lifecycle.unify("research", r.get("status", "")) in lifecycle.LIVE
        ],
    }


def _coding(limit: int) -> dict[str, Any]:
    from jarvis.dev_agent import store as dev_store

    rows = dev_store.list_tasks(limit=limit)
    return {
        "total": len(rows),
        "active": [
            {
                "task_id": r["id"],
                "objective": (r.get("objective") or "")[:100],
                "state": lifecycle.unify("coding", r.get("phase", "")),
            }
            for r in rows
            if lifecycle.unify("coding", r.get("phase", "")) in lifecycle.LIVE
        ],
    }


def _models() -> dict[str, Any]:
    from jarvis import model_routing

    health = model_routing.snapshot()
    counters = model_routing.counters()
    return {
        "tracked": len(health),
        "avoided": [h["model_id"] for h in health if h.get("avoided")],
        "recent": counters.get("top_models", {}),
        "invocations": counters.get("total", 0),
        "with_fallback": counters.get("with_fallback", 0),
    }


def _providers() -> dict[str, Any]:
    from jarvis import mcp

    providers = mcp.list_providers()
    return {
        "configured": len(providers),
        "executable": [p.provider_id for p in providers if p.may_execute()],
    }


def _count(mapper, kind: str, states) -> dict[str, int]:
    counts: dict[str, int] = {}
    for state in states:
        unified = mapper(kind, state)
        counts[unified] = counts.get(unified, 0) + 1
    return counts


def environment_status(*, limit: int = 50) -> dict[str, Any]:
    """The whole environment in one structure, with unavailability made explicit."""
    sections: dict[str, Any] = {}
    unavailable: dict[str, str] = {}

    for name, loader in (
        ("workflows", lambda: _workflows(limit)),
        ("missions", lambda: _missions(limit)),
        ("research", lambda: _research(limit)),
        ("coding", lambda: _coding(limit)),
        ("models", _models),
        ("providers", _providers),
    ):
        value, error = _safe(loader, name)
        if error:
            unavailable[name] = error
        sections[name] = value if value is not None else {"unavailable": True}

    active_states: list[str] = []
    for section in ("workflows", "missions", "research", "coding"):
        data = sections.get(section) or {}
        active_states.extend(item["state"] for item in (data.get("active") or []))

    busy = bool(active_states)
    # What the last restart picked up. Startup logging is emitted before the
    # service's handlers are attached, so this is the only place an operator can
    # actually see that recovery ran.
    from jarvis.integration import recovery as _recovery

    startup = _recovery.last_startup_recovery()
    return {
        "state": lifecycle.summarise(active_states) if busy else "idle",
        "busy": busy,
        "doing": _doing(sections),
        "policy": policy.snapshot(),
        "startup_recovery": (
            {
                "total": startup["total"],
                "recovered": startup["recovered"],
                "at": startup.get("at"),
                "errors": startup["errors"],
            }
            if startup
            else None
        ),
        **sections,
        "unavailable": unavailable,
        "controls": {
            "pause": "workflow_pause",
            "resume": "workflow_resume",
            "cancel": "workflow_cancel",
            "recover": "aria_recover",
            "provenance": "aria_provenance",
        },
    }


def _doing(sections: dict[str, Any]) -> list[str]:
    """A plain-language answer to what is happening right now."""
    lines: list[str] = []
    for item in (sections.get("workflows") or {}).get("active") or []:
        step = f" at step {item['current_step']}" if item.get("current_step") else ""
        agents = ", ".join(item.get("agents") or []) or "no agent yet"
        lines.append(
            f"workflow {item['workflow_id']} ({item['name']}) is {item['state']}{step}"
            f" — {item['succeeded']}/{item['steps_total']} steps done, using {agents}"
        )
    for item in (sections.get("research") or {}).get("active") or []:
        lines.append(f"research {item['research_id']} is {item['state']}: {item['objective']}")
    for item in (sections.get("coding") or {}).get("active") or []:
        lines.append(f"coding task {item['task_id']} is {item['state']}: {item['objective']}")
    for item in (sections.get("missions") or {}).get("active") or []:
        if not any(item["mission_id"] in line for line in lines):
            lines.append(f"mission {item['mission_id']} is {item['state']} ({item['progress']})")
    return lines or ["nothing is running"]
