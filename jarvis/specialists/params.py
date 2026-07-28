"""Role-specific parameter synthesis for specialists."""

from __future__ import annotations

from typing import Any

from jarvis.specialists.scratchpad import SharedScratchpad


def build_params(specialist_id: str, goal: str, pad: SharedScratchpad, extras: dict[str, Any] | None = None) -> dict[str, Any]:
    extras = extras or {}
    prior = "\n".join(n["text"] for n in pad.notes[-4:]) if pad.notes else ""
    ctx = prior[:3000]

    if specialist_id == "planner":
        return {
            "title": goal[:120],
            "description": ctx or goal,
            "query": goal,
            "task": goal,
        }
    if specialist_id == "researcher":
        return {"query": goal, "refresh": False, "context": ctx, "limit": 8}
    if specialist_id == "coder":
        return {
            "task": goal,
            "path": extras.get("path") or ".",
            "message": goal,
            "query": goal,
            "context": ctx,
        }
    if specialist_id == "writer":
        return {
            "draft": True,
            "title": f"Draft: {goal[:80]}",
            "text": f"Write a clear draft for:\n{goal}\n\nContext:\n{ctx}",
            "query": goal,
        }
    if specialist_id in ("critic", "reviewer"):
        return {"query": goal, "task": goal, "context": ctx, "message": f"Review findings for: {goal}\n{ctx[:1000]}"}
    if specialist_id == "memory":
        return {"query": goal, "limit": 10}
    if specialist_id == "documents":
        return {"query": goal, "limit": 8, "cite": True}
    if specialist_id == "graph":
        return {"query": goal, "limit": 8}
    if specialist_id == "vision":
        return {
            "path": extras.get("path") or extras.get("image") or "",
            "query": goal,
            "ocr": bool(extras.get("ocr")),
        }
    if specialist_id == "voice":
        return {"query": goal}
    if specialist_id == "home":
        return {"query": goal}
    if specialist_id == "operations":
        return {"query": goal, "task": "diagnose"}
    if specialist_id == "automation":
        return {"query": goal}
    return {"query": goal, "task": goal, "title": goal[:120], "context": ctx}
