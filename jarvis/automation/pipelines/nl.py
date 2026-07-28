"""Natural language → pipeline DAG drafts (never auto-save or auto-run)."""

from __future__ import annotations

import re
import uuid
from typing import Any

from jarvis.automation.pipelines.templates import TEMPLATES


def parse_nl_pipeline(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {"ok": False, "error": "Empty request", "confirmation_required": True}

    lower = raw.lower()
    draft: dict[str, Any] = {
        "id": f"draft_{uuid.uuid4().hex[:8]}",
        "name": raw[:80],
        "version": 1,
        "entry": "",
        "variables": {},
        "tags": ["nl-draft"],
        "description": f"Draft from: {raw[:120]}",
        "documentation": "Natural-language draft — review before saving. Never auto-run.",
        "steps": [],
        "template_id": None,
        "confirmation_required": True,
        "auto_save": False,
        "auto_run": False,
    }

    # Prefer known templates when intent matches
    if re.search(r"morning|briefing|start.*(day|morning)", lower):
        tpl = TEMPLATES["morning_routine"]
        draft.update(
            {
                "name": "Morning Routine (draft)",
                "template_id": "morning_routine",
                "entry": tpl["entry"],
                "steps": [dict(s) for s in tpl["steps"]],
                "tags": list(tpl.get("tags") or []) + ["nl-draft"],
                "description": tpl.get("description"),
            }
        )
        return {
            "ok": True,
            "draft": draft,
            "explanation": "Matched Morning Routine template. Review steps, then Save — never auto-runs.",
            "confirmation_required": True,
            "preview": _preview(draft),
        }

    if re.search(r"evening|wrap.?up|end of day", lower):
        tpl = TEMPLATES["evening_wrap"]
        draft.update(
            {
                "name": "Evening Wrap-Up (draft)",
                "template_id": "evening_wrap",
                "entry": tpl["entry"],
                "steps": [dict(s) for s in tpl["steps"]],
                "tags": list(tpl.get("tags") or []) + ["nl-draft"],
                "description": tpl.get("description"),
            }
        )
        return {
            "ok": True,
            "draft": draft,
            "explanation": "Matched Evening Wrap-Up template. Review before saving.",
            "confirmation_required": True,
            "preview": _preview(draft),
        }

    steps: list[dict[str, Any]] = []

    def add(action: str, name: str, **extra: Any) -> None:
        sid = f"s{len(steps)+1}"
        step = {
            "id": sid,
            "name": name,
            "action": action,
            "params": extra.pop("params", {}),
            "on_success": [],
            "on_failure": [],
            "retries": 0,
            **extra,
        }
        if steps:
            steps[-1]["on_success"] = [sid]
        steps.append(step)

    if re.search(r"reindex|index.*(doc|pdf)|document", lower):
        add("documents_reindex", "Reindex documents", timeout_sec=180)
    if re.search(r"memory|consolidat", lower):
        add("memory_consolidate", "Consolidate memory", timeout_sec=90)
    if re.search(r"knowledge|sync", lower):
        add("knowledge_sync", "Sync knowledge", timeout_sec=120)
    if re.search(r"briefing", lower):
        add("briefing", "Daily briefing", timeout_sec=60)
    if re.search(r"graph|knowledge graph", lower):
        add(
            "builtin:graph_note",
            "Knowledge graph note",
            params={"text": "Pipeline NL draft note"},
            timeout_sec=30,
        )
    if re.search(r"maintenance|nightly", lower):
        add("maintenance", "System maintenance", timeout_sec=120)

    # Coding → docs pattern
    if re.search(r"after coding|update documentation|docs after", lower):
        steps = []
        add("builtin:log", "Marker: coding complete", params={"msg": "coding complete"})
        add("documents_reindex", "Refresh documentation index", timeout_sec=180)
        add(
            "builtin:graph_note",
            "Note documentation update",
            params={"text": "Documentation refreshed after coding"},
        )

    if not steps:
        # Generic reviewable skeleton
        add("briefing", "Step 1: Briefing (edit me)")
        add("memory_consolidate", "Step 2: Memory (edit me)")

    draft["steps"] = steps
    draft["entry"] = steps[0]["id"] if steps else ""
    if re.search(r"friday|weekly", lower):
        draft["tags"] = list(draft.get("tags") or []) + ["weekly"]
        draft["schedule_hint"] = {
            "kind": "cron",
            "expression": "0 9 * * 5",
            "note": "Suggested Friday 09:00 — create Automation Rule with workflow_dag_run after save.",
        }

    return {
        "ok": True,
        "draft": draft,
        "explanation": "Generated a reviewable pipeline draft. Save explicitly — never auto-saves or auto-runs.",
        "confirmation_required": True,
        "preview": _preview(draft),
    }


def _preview(draft: dict[str, Any]) -> str:
    lines = [f"Pipeline: {draft.get('name')}", f"Steps ({len(draft.get('steps') or [])}):"]
    for s in draft.get("steps") or []:
        lines.append(f"  · {s.get('name')} → `{s.get('action')}`")
    return "\n".join(lines)
