"""Promote learned workflows → reviewable DAG drafts (never automatic)."""

from __future__ import annotations

import uuid
from typing import Any


def learned_to_dag_draft(slug: str) -> dict[str, Any]:
    """Convert a learned workflow into a pipeline draft for user review."""
    from jarvis.workflow_learning import list_workflows, load_workflow

    wf = load_workflow(slug)
    if not wf:
        for item in list_workflows():
            if item.get("slug") == slug:
                wf = load_workflow(str(item.get("slug") or slug)) or item
                break
    if not wf:
        return {"ok": False, "error": "learned_workflow_not_found", "confirmation_required": True}

    steps_in = wf.get("steps") or wf.get("actions") or []
    steps: list[dict[str, Any]] = []
    for i, raw in enumerate(steps_in):
        if isinstance(raw, str):
            action = raw
            name = raw.replace("_", " ").title()
            params: dict[str, Any] = {}
        elif isinstance(raw, dict):
            action = str(raw.get("action") or raw.get("name") or f"step_{i}")
            name = str(raw.get("name") or action)
            params = dict(raw.get("params") or {})
        else:
            continue
        # Map free actions toward registry when possible
        mapped = _map_action(action)
        sid = f"s{i + 1}"
        step = {
            "id": sid,
            "name": name,
            "action": mapped,
            "params": params,
            "on_success": [],
            "on_failure": [],
            "retries": 0,
        }
        if steps:
            steps[-1]["on_success"] = [sid]
        steps.append(step)

    if not steps:
        return {
            "ok": False,
            "error": "learned_workflow_has_no_steps",
            "confirmation_required": True,
        }

    draft = {
        "id": f"draft_{uuid.uuid4().hex[:8]}",
        "name": f"{wf.get('name') or slug} (from learned)",
        "version": 1,
        "entry": steps[0]["id"],
        "variables": {},
        "tags": ["promoted", "learned"],
        "description": f"Promoted from learned workflow `{slug}`. Review before saving.",
        "documentation": "Learned → DAG promotion is manual. Edit actions to registry IDs as needed.",
        "steps": steps,
        "template_id": None,
        "source": {"kind": "learned_workflow", "slug": slug},
        "confirmation_required": True,
        "auto_save": False,
        "auto_run": False,
    }
    return {
        "ok": True,
        "draft": draft,
        "explanation": "Review this draft, edit steps, then Save. Nothing is scheduled or run automatically.",
        "confirmation_required": True,
        "preview": "\n".join(f"· {s['name']} → `{s['action']}`" for s in steps),
    }


def _map_action(action: str) -> str:
    a = (action or "").strip()
    aliases = {
        "consolidate": "memory_consolidate",
        "memory": "memory_consolidate",
        "reindex": "documents_reindex",
        "documents": "documents_reindex",
        "sync": "knowledge_sync",
        "brief": "briefing",
        "morning_briefing": "briefing",
        "maintain": "maintenance",
    }
    return aliases.get(a, a)
