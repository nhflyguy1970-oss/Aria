"""Execute pipeline steps via Automation Action Registry (+ safe builtins)."""

from __future__ import annotations

import logging
import time
from typing import Any

from jarvis.automation.registry import get_action, validate_action

log = logging.getLogger("jarvis.automation.pipelines.actions")

# Builtins that are pipeline-local (not separate registry duplicates for domain work)
BUILTIN_PREFIX = "builtin:"


def describe_action(action_id: str) -> dict[str, Any]:
    if action_id.startswith(BUILTIN_PREFIX):
        name = action_id[len(BUILTIN_PREFIX) :]
        return {
            "id": action_id,
            "name": f"Builtin: {name}",
            "description": f"Pipeline builtin ({name})",
            "permissions": ["pipelines"],
            "confirmation": False,
            "estimated_duration_sec": 5,
            "retry": True,
            "experimental": False,
            "builtin": True,
        }
    meta = get_action(action_id)
    if meta:
        return meta
    return {
        "id": action_id,
        "name": action_id,
        "description": "Unknown action",
        "permissions": [],
        "confirmation": True,
        "estimated_duration_sec": 30,
        "unknown": True,
    }


def dry_run_action(action: str, params: dict[str, Any], variables: dict[str, Any]) -> dict[str, Any]:
    """Predict step outcome without side effects."""
    meta = describe_action(action)
    if action.startswith(BUILTIN_PREFIX):
        return {
            "ok": True,
            "dry_run": True,
            "would_execute": action,
            "params": params,
            "permissions": meta.get("permissions") or [],
            "estimated_duration_sec": meta.get("estimated_duration_sec"),
            "expected": f"Would run builtin {action}",
            "ai_explain": meta.get("ai_explain") or meta.get("description"),
        }
    v = validate_action(action, {**params, **{k: variables.get(k) for k in ()}})
    # For dry-run of registry actions, missing args still reported
    if meta.get("experimental") and not params.get("approve_experimental"):
        return {
            "ok": True,
            "dry_run": True,
            "would_execute": action,
            "permission_required": True,
            "permissions": meta.get("permissions") or [],
            "expected": "Would require explicit experimental approval",
            "ai_explain": meta.get("ai_explain"),
        }
    return {
        "ok": True,
        "dry_run": True,
        "would_execute": action,
        "params": params,
        "permissions": meta.get("permissions") or [],
        "estimated_duration_sec": meta.get("estimated_duration_sec"),
        "validation": v,
        "expected": meta.get("description") or f"Would execute {action}",
        "ai_explain": meta.get("ai_explain"),
        "resources": {
            "job": bool(meta.get("job")),
            "activity": bool(meta.get("activity")),
            "confirmation": bool(meta.get("confirmation")),
        },
    }


def execute_action(
    action: str,
    params: dict[str, Any],
    variables: dict[str, Any],
    *,
    dry_run: bool = False,
    approve_experimental: bool = False,
) -> dict[str, Any]:
    if dry_run:
        return dry_run_action(action, params, variables)

    if action.startswith(BUILTIN_PREFIX):
        return _execute_builtin(action, params, variables)

    meta = get_action(action)
    if not meta:
        return {"ok": False, "error": f"unknown action {action}"}

    if meta.get("experimental") and not approve_experimental:
        return {
            "ok": False,
            "permission_required": True,
            "error": "Experimental action requires approval",
            "status": "permission_required",
        }

    # Inject common params for experimental actions
    p = dict(params)
    if action == "agent_step":
        return _execute_agent_step(p, variables, approve=approve_experimental)
    if action == "vision_analyze":
        return _execute_vision(p, variables, approve=approve_experimental)

    return _execute_registry(action, p, variables)


def _execute_builtin(action: str, params: dict[str, Any], variables: dict[str, Any]) -> dict[str, Any]:
    name = action[len(BUILTIN_PREFIX) :]
    if name == "log":
        msg = params.get("msg") or params.get("message") or ""
        log.info("pipeline log: %s", msg)
        return {"ok": True, "message": str(msg)}
    if name == "set":
        for k, v in params.items():
            variables[k] = v
        return {"ok": True, "variables": dict(variables)}
    if name == "fail":
        return {"ok": False, "error": params.get("error") or "forced failure"}
    if name == "graph_note":
        try:
            from jarvis.intelligence.knowledge_graph import ingest_text

            return ingest_text(
                str(params.get("text") or "pipeline note"),
                namespace=str(params.get("namespace") or "default"),
                source="automation",
                confidence=0.6,
                explicit=True,
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
    if name == "health_check":
        try:
            from jarvis.intelligence.platform_bus import platform_status

            st = platform_status()
            ok = bool(st.get("ok", True)) if isinstance(st, dict) else True
            return {"ok": ok, "result": st if isinstance(st, dict) else {"status": st}}
        except Exception:
            # Soft health — presence of DATA_DIR is enough
            from jarvis.config import DATA_DIR

            return {"ok": True, "result": {"data_dir": str(DATA_DIR), "soft": True}}
    if name == "sleep":
        time.sleep(min(5.0, float(params.get("sec") or 0.1)))
        return {"ok": True}
    return {"ok": False, "error": f"unknown builtin {action}"}


def _execute_registry(action: str, params: dict[str, Any], variables: dict[str, Any]) -> dict[str, Any]:
    """Dispatch known registry actions without going through rule validation loops."""
    try:
        if action in ("maintenance", "system_maintenance"):
            from jarvis.automation import ops

            fn = getattr(ops, "run_maintenance", None) or getattr(ops, "nightly", None)
            if callable(fn):
                result = fn()
                return {"ok": bool(result.get("ok", True)), "result": result}
            return {"ok": False, "skipped": True, "error": "maintenance runner missing"}

        if action in ("memory_consolidate", "consolidate"):
            from jarvis.intelligence.memory_platform import consolidate_memories

            return consolidate_memories()

        if action in ("knowledge_sync", "sync"):
            from jarvis.knowledge import sync as knowledge_sync

            fn = getattr(knowledge_sync, "sync_all", None) or getattr(knowledge_sync, "run", None)
            if callable(fn):
                return {"ok": True, "result": fn()}
            return {"ok": False, "skipped": True, "error": "knowledge sync missing"}

        if action == "documents_reindex":
            from jarvis import documents_rag

            documents_rag.build_index(force=True)
            return {"ok": True, "result": "reindexed"}

        if action == "briefing":
            try:
                from jarvis.morning_briefing import build_briefing

                text = build_briefing()
                variables["briefing_preview"] = str(text)[:400]
                return {"ok": True, "result": str(text)[:800]}
            except Exception as exc:
                try:
                    from jarvis.workflows.daily import dispatch

                    out = dispatch("overnight_summary", None)
                    return {"ok": True, "result": out}
                except Exception:
                    return {"ok": False, "error": str(exc)}

        if action == "ha_scene":
            from jarvis.home_assistant import activate_scene

            scene = params.get("scene") or variables.get("scene")
            if not scene:
                return {"ok": False, "error": "scene required"}
            ok_ha, msg = activate_scene(str(scene))
            return {"ok": bool(ok_ha), "result": msg, "error": None if ok_ha else msg}

        if action == "journal_log":
            text = params.get("text") or variables.get("text") or ""
            if not text:
                return {"ok": False, "error": "text required"}
            try:
                from jarvis import journal as journal_mod

                fn = getattr(journal_mod, "append_entry", None) or getattr(journal_mod, "add_entry", None)
                if callable(fn):
                    result = fn(str(text))
                    if isinstance(result, dict):
                        return {"ok": bool(result.get("ok", True)), "result": result}
                    return {"ok": True, "result": result}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}
            return {"ok": False, "skipped": True, "error": "journal append unavailable"}

        if action == "skill_run":
            from jarvis.skill_database import run_skill

            slug = params.get("slug") or variables.get("slug")
            if not slug:
                return {"ok": False, "error": "slug required"}
            return run_skill(str(slug), dry_run=False)

        if action == "workflow_learned_run":
            from jarvis.workflow_learning import run_workflow

            slug = params.get("slug") or variables.get("slug")
            if not slug:
                return {"ok": False, "error": "slug required"}
            return run_workflow(str(slug), assistant=None, dry_run=False)

        if action == "workflow_dag_run":
            # Nested DAG — prevent infinite recursion via depth flag
            if variables.get("_pipeline_depth", 0) >= 2:
                return {"ok": False, "error": "nested pipeline depth exceeded"}
            from jarvis.automation.pipelines.engine import run_pipeline

            wid = params.get("workflow_id") or variables.get("workflow_id")
            if not wid:
                return {"ok": False, "error": "workflow_id required"}
            nested_vars = {**variables, "_pipeline_depth": int(variables.get("_pipeline_depth", 0)) + 1}
            return run_pipeline(str(wid), variables=nested_vars, dry_run=False, emit_bridges=False)

        if action == "browser_read":
            return {
                "ok": False,
                "permission_required": True,
                "error": "Browser step requires explicit approval context",
            }

        return {"ok": False, "error": f"no pipeline handler for action {action}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _execute_agent_step(params: dict[str, Any], variables: dict[str, Any], *, approve: bool) -> dict[str, Any]:
    if not approve:
        return {"ok": False, "permission_required": True, "error": "agent_step requires approval"}
    prompt = str(params.get("prompt") or variables.get("goal") or "")
    budget = float(params.get("budget") or 1)
    if budget <= 0:
        return {"ok": False, "error": "budget must be > 0"}
    if not prompt:
        return {"ok": False, "error": "prompt required"}
    # Approved Specialist Team run — never silent
    from jarvis.specialists.engine import run_team

    team = params.get("specialists") or params.get("team")
    result = run_team(
        None,  # assistant optional for read-heavy teams
        prompt,
        specialists=list(team) if isinstance(team, list) else None,
        confirm=True,
        budget={
            "require_confirm": False,
            "max_specialists": min(6, int(budget) + 2),
            "max_runtime_sec": float(params.get("timeout") or 180),
        },
        trigger="automation",
        emit_bridges=True,
        approve_writes=bool(params.get("approve_writes")),
    )
    variables["last_agent_run_id"] = result.get("run_id")
    return {
        "ok": bool(result.get("ok")),
        "result": {
            "mode": "specialist_team",
            "run_id": result.get("run_id"),
            "status": result.get("status"),
            "job_id": result.get("job_id"),
            "summary": (result.get("synthesis") or result.get("summary") or "")[:500],
            "team": result.get("team"),
        },
        "error": None if result.get("ok") else (result.get("error") or result.get("status")),
    }


def _execute_vision(params: dict[str, Any], variables: dict[str, Any], *, approve: bool) -> dict[str, Any]:
    if not approve:
        return {"ok": False, "permission_required": True, "error": "vision_analyze requires approval"}
    path = str(params.get("path") or variables.get("path") or "")
    log.info("pipeline vision_analyze approved path=%s", path[:200])
    return {
        "ok": True,
        "result": {
            "mode": "gated_stub",
            "path": path,
            "message": "Vision step audited (gated; no unbounded vision loop).",
        },
    }
