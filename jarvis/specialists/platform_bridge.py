"""Optional AI-Platform bridge — never replaces Aria orchestration."""

from __future__ import annotations

from typing import Any


def platform_coordinate_optional(goal: str, *, agent_ids: list[str] | None = None) -> dict[str, Any]:
    """Soft-call AI-Platform AgentManager if importable. Advisory only."""
    try:
        from aiplatform.agents.manager import AgentManager  # type: ignore
    except Exception as exc:
        return {
            "ok": False,
            "available": False,
            "error": f"AI-Platform agents not available: {exc}",
            "note": "Aria Specialist Team remains the primary orchestrator.",
        }
    try:
        mgr = AgentManager()
        coordinate = getattr(mgr, "coordinate", None)
        if not callable(coordinate):
            return {"ok": False, "available": True, "error": "coordinate() missing"}
        result = coordinate(goal, agent_ids=agent_ids)
        return {
            "ok": True,
            "available": True,
            "result": result,
            "note": "Advisory bridge only — Aria specialists own execution.",
        }
    except Exception as exc:
        return {"ok": False, "available": True, "error": str(exc)}
