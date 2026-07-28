"""Built-in pipeline templates — honest, meaningful first-run work."""

from __future__ import annotations

from typing import Any

# Template catalog: friendly metadata + real registry actions (not demo logs).
TEMPLATES: dict[str, dict[str, Any]] = {
    "morning_routine": {
        "id": "morning_routine",
        "name": "Morning Routine",
        "description": (
            "Generate your daily briefing, consolidate memory, refresh the document index, "
            "update the knowledge graph, and verify Mission Control health."
        ),
        "tags": ["daily", "briefing", "memory", "documents"],
        "documentation": (
            "Use as a scheduled morning pipeline. Each step uses the Automation Action Registry. "
            "Schedule via an Automation Rule with action workflow_dag_run."
        ),
        "entry": "brief",
        "steps": [
            {
                "id": "brief",
                "name": "Daily briefing",
                "action": "briefing",
                "params": {},
                "on_success": ["memory"],
                "on_failure": ["memory"],
                "retries": 1,
                "retry_delay_sec": 1.0,
                "timeout_sec": 60,
            },
            {
                "id": "memory",
                "name": "Consolidate memory",
                "action": "memory_consolidate",
                "params": {},
                "on_success": ["docs"],
                "on_failure": ["docs"],
                "retries": 1,
                "timeout_sec": 90,
            },
            {
                "id": "docs",
                "name": "Reindex documents",
                "action": "documents_reindex",
                "params": {},
                "on_success": ["graph"],
                "on_failure": ["graph"],
                "retries": 0,
                "timeout_sec": 180,
            },
            {
                "id": "graph",
                "name": "Knowledge graph note",
                "action": "builtin:graph_note",
                "params": {"text": "Morning routine completed — library and memory refreshed"},
                "on_success": ["health"],
                "retries": 0,
                "timeout_sec": 30,
            },
            {
                "id": "health",
                "name": "Health verification",
                "action": "builtin:health_check",
                "params": {},
                "retries": 0,
                "timeout_sec": 15,
            },
        ],
    },
    "doc_ingest": {
        "id": "doc_ingest",
        "name": "Document Ingest Pipeline",
        "description": "Rebuild the document search index and record a knowledge-graph refresh note.",
        "tags": ["documents", "knowledge"],
        "documentation": "Run after adding documents, or schedule on a folder watch via Automation.",
        "entry": "index",
        "steps": [
            {
                "id": "index",
                "name": "Reindex documents",
                "action": "documents_reindex",
                "params": {},
                "on_success": ["graph"],
                "retries": 1,
                "timeout_sec": 180,
            },
            {
                "id": "graph",
                "name": "Update knowledge graph",
                "action": "builtin:graph_note",
                "params": {"text": "Document library refreshed"},
                "retries": 0,
                "timeout_sec": 30,
            },
        ],
    },
    "evening_wrap": {
        "id": "evening_wrap",
        "name": "Evening Wrap-Up",
        "description": "Consolidate memory and sync knowledge sources at end of day.",
        "tags": ["daily", "memory", "knowledge"],
        "documentation": "Schedule in the evening via Automation Rule.",
        "entry": "memory",
        "steps": [
            {
                "id": "memory",
                "name": "Consolidate memory",
                "action": "memory_consolidate",
                "on_success": ["sync"],
                "retries": 1,
                "timeout_sec": 90,
            },
            {
                "id": "sync",
                "name": "Sync knowledge",
                "action": "knowledge_sync",
                "retries": 1,
                "timeout_sec": 120,
            },
        ],
    },
}


def list_template_meta() -> list[dict[str, Any]]:
    out = []
    for tid, tpl in TEMPLATES.items():
        out.append(
            {
                "id": tid,
                "name": tpl.get("name") or tid,
                "description": tpl.get("description") or "",
                "tags": list(tpl.get("tags") or []),
                "documentation": tpl.get("documentation") or "",
                "step_count": len(tpl.get("steps") or []),
            }
        )
    return out


def get_template(template_id: str) -> dict[str, Any] | None:
    tpl = TEMPLATES.get(template_id)
    if not tpl:
        return None
    return dict(tpl)
