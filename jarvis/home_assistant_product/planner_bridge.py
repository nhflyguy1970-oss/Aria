"""Planner bridge — focus / home candidates (preview only)."""

from __future__ import annotations

from typing import Any


def planner_candidates(*, kind: str = "focus_home", title: str = "", notes: str = "") -> dict[str, Any]:
    kind = (kind or "focus_home").strip().lower()
    candidates: list[dict[str, Any]] = []
    if kind in ("focus_home", "focus"):
        candidates.append(
            {
                "title": title or "Start focus with Focus mode lights",
                "notes": notes or "Confirm to activate Smart Home focus preset via Planner",
                "kind": kind,
                "preset": "focus mode",
                "source": "smarthome_planner",
                "selected": True,
            }
        )
    elif kind in ("end_focus", "relax"):
        candidates.append(
            {
                "title": title or "End focus — Relax lights",
                "notes": notes or "Confirm to activate relax preset",
                "kind": kind,
                "preset": "relax",
                "source": "smarthome_planner",
                "selected": True,
            }
        )
    else:
        candidates.append(
            {
                "title": title or "Smart Home task",
                "notes": notes,
                "kind": kind,
                "source": "smarthome",
                "selected": True,
            }
        )
    return {
        "ok": True,
        "product": "Smart Home",
        "target": "Planner",
        "requires_confirmation": True,
        "kind": kind,
        "candidates": candidates,
        "message": "Preview only — confirm in Planner.",
        "pipeline": "smarthome_planner_bridge",
    }
