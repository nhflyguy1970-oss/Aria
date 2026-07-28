"""Lightweight pipeline canvas data — visualizes existing pipelines; does not replace JSON/form editor."""

from __future__ import annotations

from typing import Any

from jarvis.automation.pipelines.storage import get_pipeline


def canvas_model(pipeline_id: str) -> dict[str, Any]:
    """Return nodes/edges for a simple read-oriented canvas."""
    wf = get_pipeline(pipeline_id)
    if not wf:
        return {"ok": False, "error": "not_found"}

    nodes = []
    edges = []
    for i, s in enumerate(wf.get("steps") or []):
        nodes.append(
            {
                "id": s["id"],
                "label": s.get("name") or s["id"],
                "action": s.get("action"),
                "x": 40 + (i % 4) * 180,
                "y": 40 + (i // 4) * 100,
                "entry": s["id"] == wf.get("entry"),
                "when": s.get("when") or "",
                "retries": s.get("retries") or 0,
            }
        )
        for tgt in s.get("on_success") or s.get("next") or []:
            edges.append({"from": s["id"], "to": tgt, "kind": "success"})
        for tgt in s.get("on_failure") or []:
            edges.append({"from": s["id"], "to": tgt, "kind": "failure"})

    return {
        "ok": True,
        "pipeline_id": pipeline_id,
        "name": wf.get("name"),
        "version": wf.get("version"),
        "nodes": nodes,
        "edges": edges,
        "note": "Read-only visualization. Edit via JSON/Form editor — not an n8n clone.",
    }
