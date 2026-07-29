"""Experimental Vision features — env-gated, same Vision engine."""

from __future__ import annotations

import os
from typing import Any


def experimental_flags() -> dict[str, bool]:
    return {
        "continuous_scene": os.getenv("JARVIS_VISION_EXP_CONTINUOUS", "0") == "1",
        "temporal_compare": os.getenv("JARVIS_VISION_EXP_TEMPORAL", "0") == "1",
        "knowledge_graph_link": os.getenv("JARVIS_VISION_EXP_KG", "0") == "1",
        "ha_camera_snapshot": os.getenv("JARVIS_VISION_EXP_HA_CAMERA", "0") == "1",
        "visual_memory_clustering": os.getenv("JARVIS_VISION_EXP_CLUSTER", "0") == "1",
        "scene_timeline": os.getenv("JARVIS_VISION_EXP_TIMELINE", "0") == "1",
    }


def experimental_status() -> dict[str, Any]:
    flags = experimental_flags()
    return {
        "ok": True,
        "experimental": True,
        "message": "Experimental Vision features are opt-in and share the same Vision engine.",
        "flags": flags,
        "enabled": [k for k, v in flags.items() if v],
        "consent_required": True,
    }


def ha_camera_snapshot_if_enabled(entity_id: str = "") -> dict[str, Any]:
    if not experimental_flags().get("ha_camera_snapshot"):
        return {"ok": False, "error": "ha_camera_snapshot disabled", "experimental": True}
    return {
        "ok": False,
        "error": "HA camera snapshot requires explicit operator confirmation UI",
        "experimental": True,
        "entity_id": entity_id,
        "requires_confirmation": True,
    }


def temporal_compare(path_a: str, path_b: str, *, assistant=None) -> dict[str, Any]:
    """Compare two captures over time — same compare pipeline."""
    if not experimental_flags().get("temporal_compare"):
        return {"ok": False, "error": "temporal_compare disabled", "experimental": True}
    from jarvis.vision_product.engine import analyze

    return {
        **analyze(
            path=path_a,
            path2=path_b,
            action="compare",
            question="Compare these two captures over time. Note what changed.",
            source="experimental_temporal",
            assistant=assistant,
            force=True,
        ),
        "experimental": "temporal_compare",
    }


def link_knowledge_graph(analysis: str, *, path: str = "") -> dict[str, Any]:
    if not experimental_flags().get("knowledge_graph_link"):
        return {"ok": False, "error": "knowledge_graph_link disabled", "experimental": True}
    # Stage only — never silent Memory / KG writes
    return {
        "ok": True,
        "experimental": "knowledge_graph_link",
        "requires_confirmation": True,
        "staged": {"path": path, "analysis": (analysis or "")[:2000]},
        "message": "Knowledge graph link staged — confirm in Connections / Memory (never auto-written).",
    }


def cluster_visual_memory(*, limit: int = 20) -> dict[str, Any]:
    if not experimental_flags().get("visual_memory_clustering"):
        return {"ok": False, "error": "visual_memory_clustering disabled", "experimental": True}
    from jarvis.vision_product.history import list_history

    rows = list_history(limit=limit)
    # Naive clustering by task for operator review
    buckets: dict[str, list[str]] = {}
    for r in rows:
        buckets.setdefault(str(r.get("task") or "other"), []).append(str(r.get("id")))
    return {
        "ok": True,
        "experimental": "visual_memory_clustering",
        "clusters": buckets,
        "message": "Clusters are read-only summaries of Vision history — not silent Memory ingest.",
    }


def scene_timeline(*, limit: int = 30) -> dict[str, Any]:
    if not experimental_flags().get("scene_timeline"):
        return {"ok": False, "error": "scene_timeline disabled", "experimental": True}
    from jarvis.vision_product.history import list_history

    rows = list_history(limit=limit)
    timeline = [
        {
            "id": r.get("id"),
            "ts": r.get("ts"),
            "task": r.get("task"),
            "path": r.get("path"),
            "summary": (r.get("analysis") or r.get("ocr") or "")[:160],
        }
        for r in rows
    ]
    return {"ok": True, "experimental": "scene_timeline", "timeline": timeline}


def continuous_scene_status() -> dict[str, Any]:
    enabled = experimental_flags().get("continuous_scene")
    return {
        "ok": True,
        "experimental": "continuous_scene",
        "enabled": bool(enabled),
        "running": False,
        "message": "Continuous scene assistant is opt-in only — never always-on ambient camera.",
        "requires_consent": True,
    }
