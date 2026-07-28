"""Versioned Automation Action Registry — permissions, confirmations, categories."""

from __future__ import annotations

from typing import Any

REGISTRY_VERSION = 1

# Experimental stubs marked experimental=True — architecture only / gated
ACTIONS: dict[str, dict[str, Any]] = {
    "maintenance": {
        "name": "System maintenance",
        "description": "Run knowledge sync, memory consolidate, workstation diagnose",
        "permissions": ["system"],
        "arguments": {},
        "version": 1,
        "category": "system",
        "confirmation": False,
        "estimated_duration_sec": 60,
        "retry": True,
        "activity": True,
        "job": True,
        "ai_explain": "Keeps Aria healthy overnight.",
    },
    "memory_consolidate": {
        "name": "Consolidate memory",
        "description": "Promote and tidy memory hierarchy",
        "permissions": ["memory"],
        "arguments": {},
        "version": 1,
        "category": "memory",
        "confirmation": False,
        "estimated_duration_sec": 30,
        "retry": True,
        "activity": True,
        "job": False,
        "ai_explain": "Organizes long-term memory.",
    },
    "knowledge_sync": {
        "name": "Sync knowledge",
        "description": "Sync knowledge registry sources",
        "permissions": ["knowledge"],
        "arguments": {},
        "version": 1,
        "category": "knowledge",
        "confirmation": False,
        "estimated_duration_sec": 45,
        "retry": True,
        "activity": True,
        "job": True,
        "ai_explain": "Refreshes knowledge sources.",
    },
    "documents_reindex": {
        "name": "Reindex documents",
        "description": "Rebuild document search index",
        "permissions": ["documents"],
        "arguments": {},
        "version": 1,
        "category": "documents",
        "confirmation": False,
        "estimated_duration_sec": 90,
        "retry": True,
        "activity": True,
        "job": True,
        "ai_explain": "Makes new documents searchable.",
    },
    "briefing": {
        "name": "Morning briefing",
        "description": "Generate morning briefing markdown",
        "permissions": ["chat", "planner"],
        "arguments": {},
        "version": 1,
        "category": "planner",
        "confirmation": False,
        "estimated_duration_sec": 20,
        "retry": True,
        "activity": True,
        "job": False,
        "ai_explain": "Summarizes your day.",
    },
    "ha_scene": {
        "name": "Home Assistant scene",
        "description": "Activate an HA scene",
        "permissions": ["home_assistant"],
        "arguments": {"scene": {"type": "string", "required": True}},
        "version": 1,
        "category": "home",
        "confirmation": True,
        "estimated_duration_sec": 5,
        "retry": True,
        "activity": True,
        "job": False,
        "ai_explain": "Controls your home via Home Assistant.",
    },
    "journal_log": {
        "name": "Journal entry",
        "description": "Append text to bullet journal",
        "permissions": ["journal"],
        "arguments": {"text": {"type": "string", "required": True}},
        "version": 1,
        "category": "journal",
        "confirmation": False,
        "estimated_duration_sec": 2,
        "retry": False,
        "activity": True,
        "job": False,
        "ai_explain": "Writes a journal note.",
    },
    "skill_run": {
        "name": "Run skill",
        "description": "Execute a reusable skill procedure",
        "permissions": ["skills"],
        "arguments": {"slug": {"type": "string", "required": True}},
        "version": 1,
        "category": "skills",
        "confirmation": True,
        "estimated_duration_sec": 30,
        "retry": False,
        "activity": True,
        "job": True,
        "ai_explain": "Runs a saved procedure.",
    },
    "workflow_learned_run": {
        "name": "Run learned workflow",
        "description": "Execute a learned action sequence",
        "permissions": ["workflows"],
        "arguments": {"slug": {"type": "string", "required": True}},
        "version": 1,
        "category": "workflows",
        "confirmation": True,
        "estimated_duration_sec": 45,
        "retry": False,
        "activity": True,
        "job": True,
        "ai_explain": "Replays a sequence Aria learned from your usage.",
    },
    "workflow_dag_run": {
        "name": "Run pipeline (DAG)",
        "description": "Execute a multi-step Automation pipeline (workflow DAG)",
        "permissions": ["workflows", "pipelines"],
        "arguments": {
            "workflow_id": {"type": "string", "required": True},
            "variables": {"type": "object", "required": False},
        },
        "version": 2,
        "category": "workflows",
        "confirmation": True,
        "estimated_duration_sec": 90,
        "retry": True,
        "activity": True,
        "job": True,
        "ai_explain": "Runs a saved multi-step pipeline under Automation. Schedule via Rules; observe via Activity and Job Center.",
    },
    # Experimental — registered but gated
    "agent_step": {
        "name": "Agent step (experimental)",
        "description": "Run a bounded agent step with approval",
        "permissions": ["agents", "approval"],
        "arguments": {"prompt": {"type": "string", "required": True}, "budget": {"type": "number"}},
        "version": 1,
        "category": "experimental",
        "confirmation": True,
        "estimated_duration_sec": 120,
        "retry": False,
        "activity": True,
        "job": True,
        "ai_explain": "Experimental agent action — requires approval and budget.",
        "experimental": True,
    },
    "vision_analyze": {
        "name": "Vision analyze (experimental)",
        "description": "Analyze an image as an automation step",
        "permissions": ["vision"],
        "arguments": {"path": {"type": "string"}},
        "version": 1,
        "category": "experimental",
        "confirmation": True,
        "estimated_duration_sec": 30,
        "retry": True,
        "activity": True,
        "job": False,
        "ai_explain": "Experimental vision action.",
        "experimental": True,
    },
    "browser_read": {
        "name": "Browser read (experimental)",
        "description": "Read a page via browser agent",
        "permissions": ["browser"],
        "arguments": {"url": {"type": "string"}},
        "version": 1,
        "category": "experimental",
        "confirmation": True,
        "estimated_duration_sec": 45,
        "retry": True,
        "activity": True,
        "job": True,
        "ai_explain": "Experimental browser action.",
        "experimental": True,
    },
}


def list_actions(*, include_experimental: bool = False) -> list[dict[str, Any]]:
    out = []
    for key, meta in ACTIONS.items():
        if meta.get("experimental") and not include_experimental:
            continue
        out.append({"id": key, **meta})
    return out


def get_action(action_id: str) -> dict[str, Any] | None:
    meta = ACTIONS.get(action_id)
    if not meta:
        # aliases
        aliases = {
            "system_maintenance": "maintenance",
            "consolidate": "memory_consolidate",
            "sync": "knowledge_sync",
        }
        meta = ACTIONS.get(aliases.get(action_id, ""), None)
        if not meta:
            return None
        action_id = aliases.get(action_id, action_id)
    return {"id": action_id, **meta}


def validate_action(action_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = get_action(action_id)
    if not meta:
        return {"ok": False, "error": f"Unknown action: {action_id}", "status": "skipped"}
    if meta.get("experimental"):
        return {
            "ok": False,
            "error": "Experimental action — enable explicitly and confirm",
            "status": "permission_required",
            "action": meta,
        }
    params = params or {}
    missing = []
    for arg, spec in (meta.get("arguments") or {}).items():
        if spec.get("required") and not params.get(arg):
            missing.append(arg)
    if missing:
        return {"ok": False, "error": f"Missing arguments: {', '.join(missing)}", "action": meta}
    return {"ok": True, "action": meta}


def registry_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "version": REGISTRY_VERSION,
        "actions": list_actions(include_experimental=True),
    }
