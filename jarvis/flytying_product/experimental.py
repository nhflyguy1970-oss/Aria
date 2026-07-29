"""Experimental Fly Tying features — env-gated, same Fly Tying engine."""

from __future__ import annotations

import os
from typing import Any


def experimental_flags() -> dict[str, bool]:
    return {
        "knowledge_graph": os.getenv("JARVIS_FLYTYING_EXP_KG", "0") == "1",
        "bench_lighting": os.getenv("JARVIS_FLYTYING_EXP_HA_LIGHT", "0") == "1"
        or os.getenv("JARVIS_FLYTYING_EXP_HA_LIGHTING", "0") == "1",
        "session_coach": os.getenv("JARVIS_FLYTYING_EXP_COACH", "0") == "1"
        or os.getenv("JARVIS_FLYTYING_EXP_SESSION_COACH", "0") == "1",
        "pattern_evolution": os.getenv("JARVIS_FLYTYING_EXP_EVOLVE", "0") == "1"
        or os.getenv("JARVIS_FLYTYING_EXP_PATTERN_EVOLUTION", "0") == "1",
        "trip_advisor": os.getenv("JARVIS_FLYTYING_EXP_TRIP", "0") == "1"
        or os.getenv("JARVIS_FLYTYING_EXP_TRIP_ADVISOR", "0") == "1",
        "regional_intelligence": os.getenv("JARVIS_FLYTYING_EXP_REGIONAL", "0") == "1",
        "material_clustering": os.getenv("JARVIS_FLYTYING_EXP_CLUSTER", "0") == "1",
    }


def experimental_status() -> dict[str, Any]:
    flags = experimental_flags()
    return {
        "ok": True,
        "experimental": True,
        "message": "Experimental Fly Tying features are opt-in and share the same Fly Tying engine.",
        "flags": flags,
        "enabled": [k for k, v in flags.items() if v],
        "consent_required": True,
    }


def link_knowledge_graph(*, recipe_id: str = "", summary: str = "") -> dict[str, Any]:
    if not experimental_flags().get("knowledge_graph"):
        return {"ok": False, "error": "knowledge_graph disabled", "experimental": True}
    return {
        "ok": True,
        "experimental": "knowledge_graph",
        "requires_confirmation": True,
        "staged": {"recipe_id": recipe_id, "summary": (summary or "")[:2000]},
        "message": "Knowledge graph link staged — confirm in Connections / Memory (never auto-written).",
    }


def bench_lighting_if_enabled(scene: str = "bench", *, entity_id: str = "") -> dict[str, Any]:
    if not experimental_flags().get("bench_lighting"):
        return {"ok": False, "error": "bench_lighting disabled", "experimental": True}
    return {
        "ok": False,
        "error": "HA bench lighting requires explicit operator confirmation",
        "experimental": True,
        "scene": scene,
        "entity_id": entity_id,
        "requires_confirmation": True,
        "note": "Home Assistant owns scenes — Fly Tying only requests.",
    }


def session_coach_hint(*, session_id: str = "") -> dict[str, Any]:
    if not experimental_flags().get("session_coach"):
        return {"ok": False, "error": "session_coach disabled", "experimental": True}
    from jarvis.flytying_product.sessions import get_session
    from jarvis.flytying_product.voice_bridge import _current_step_text

    session = get_session(session_id)
    if not session:
        return {"ok": False, "error": "no_session", "experimental": True}
    return {
        "ok": True,
        "experimental": "session_coach",
        "hint": _current_step_text(session),
        "session_id": session.get("id"),
        "step_idx": session.get("step_idx"),
        "message": "Coach hints are read-only guidance — never auto-advance without Voice/bench command.",
    }


def material_clusters(*, limit: int = 20) -> dict[str, Any]:
    if not experimental_flags().get("material_clustering"):
        return {"ok": False, "error": "material_clustering disabled", "experimental": True}
    from jarvis.flytying.user_store import list_inventory_items

    buckets: dict[str, list[str]] = {}
    for item in list_inventory_items()[: max(1, min(limit, 100))]:
        what = str(item.get("what") or item.get("name") or "other").lower().split()[0]
        buckets.setdefault(what, []).append(str(item.get("name") or item.get("id") or ""))
    return {
        "ok": True,
        "experimental": "material_clustering",
        "clusters": buckets,
        "message": "Clusters are read-only inventory summaries.",
    }


def trip_advisor_preview(*, region: str = "", month: int | None = None) -> dict[str, Any]:
    if not experimental_flags().get("trip_advisor"):
        return {"ok": False, "error": "trip_advisor disabled", "experimental": True}
    from jarvis.flytying.hatch import hatch_context

    ctx = hatch_context(month=month)
    return {
        "ok": True,
        "experimental": "trip_advisor",
        "region": region or ctx.get("region"),
        "hatch": ctx,
        "message": "Trip advisor is a preview — Planner/Calendar bridges create candidates, not bookings.",
    }
