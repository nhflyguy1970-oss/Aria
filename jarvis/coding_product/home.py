"""Coding Home snapshot — primary destination for software development."""

from __future__ import annotations

from typing import Any

from jarvis.coding_product.guardrails import assess_coding_root, guardrail_banner
from jarvis.coding_product.terminology import BOUNDARIES, TERMINOLOGY


def _coding_model() -> dict[str, Any]:
    """Active coding model from settings file (no Ollama ping)."""
    try:
        from jarvis.config import is_uncensored
        from jarvis.model_store import ROLE_LABELS, _load_raw

        data = _load_raw() or {}
        mode = "uncensored" if is_uncensored() else "standard"
        bank = data.get(mode) or data.get("standard") or {}
        tag = str(bank.get("coding") or bank.get("coder") or "")
        return {
            "role": "coding",
            "role_label": ROLE_LABELS.get("coding", "Coding"),
            "model": tag,
            "provider": "ollama",
            "card": None,
            "models_deep_link": "models",
        }
    except Exception as exc:
        return {
            "role": "coding",
            "role_label": "Coding",
            "model": "",
            "provider": "",
            "error": str(exc),
            "models_deep_link": "models",
        }


def _open_proposals(assistant: Any | None) -> list[dict[str, Any]]:
    if assistant is None:
        return []
    items = []
    for pid, prop in (assistant.pending_proposals or {}).items():
        files = prop.get("files") or []
        if not files and prop.get("path"):
            files = [{"path": prop["path"]}]
        items.append(
            {
                "id": pid,
                "summary": (prop.get("explanation") or "")[:200],
                "mode": prop.get("mode"),
                "syntax_ok": prop.get("syntax_ok"),
                "files": [f.get("path") for f in files if f.get("path")],
                "status": "pending",
            }
        )
    return items[:20]


def _git_summary(root: str) -> dict[str, Any]:
    if not root:
        return {"is_repo": False}
    try:
        from pathlib import Path

        from jarvis import git_util

        p = Path(root)
        if not git_util.is_repo(p):
            return {"is_repo": False, "path": root}
        return {
            "is_repo": True,
            "path": root,
            "branch": git_util.current_branch(p) or "",
            "status_short": (git_util.status(p) or "")[:800],
            "has_changes": git_util.has_local_changes(p),
        }
    except Exception as exc:
        return {"is_repo": False, "error": str(exc), "path": root}


def _recent_jobs(limit: int = 8) -> list[dict[str, Any]]:
    try:
        from jarvis.coding_jobs import list_recent
        from jarvis.coding_product.job_links import enrich_coding_job

        return [enrich_coding_job(j) for j in list_recent(limit)]
    except Exception:
        return []


def _lsp_status() -> dict[str, Any]:
    try:
        from jarvis.lsp import tools_status

        return {"ok": True, "tools": tools_status()}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "note": "LSP available via /api/lsp/*"}


def _last_coding_task() -> dict[str, Any] | None:
    try:
        from jarvis.coding_tasks import TaskManager

        tm = TaskManager()
        tasks = sorted(tm._tasks.values(), key=lambda t: t.updated_at, reverse=True)
        if not tasks:
            return None
        for t in tasks:
            if t.status in ("paused", "running"):
                return t.to_dict()
        return tasks[0].to_dict()
    except Exception:
        return None


def coding_home_snapshot(assistant: Any | None = None) -> dict[str, Any]:
    if assistant is None:
        try:
            from jarvis.assistant_instance import get_assistant

            assistant = get_assistant()
        except Exception:
            assistant = None

    guardrails = assess_coding_root(assistant)
    write_target = guardrails.get("write_target") or guardrails.get("coding_root") or ""
    model = _coding_model()
    open_props = _open_proposals(assistant)

    history_preview = []
    try:
        from jarvis.coding_product.history import list_history

        history_preview = list_history(limit=8).get("items") or []
    except Exception:
        history_preview = []

    prefs = {}
    try:
        from jarvis.coding_product.preferences import preference_suggestions

        prefs = preference_suggestions()
    except Exception:
        prefs = {}

    return {
        "ok": True,
        "product": "coding",
        "title": "Coding",
        "philosophy": BOUNDARIES.get("philosophy"),
        "boundaries": BOUNDARIES,
        "terminology": TERMINOLOGY,
        "guardrails": guardrails,
        "banner": guardrail_banner(guardrails),
        "active_project": guardrails.get("active_project"),
        "coding_root": guardrails.get("coding_root"),
        "write_target": write_target,
        "repository": guardrails.get("repository"),
        "git": _git_summary(write_target),
        "model": model,
        "open_proposals": open_props,
        "proposal_history": history_preview,
        "recent_jobs": _recent_jobs(),
        "lsp": _lsp_status(),
        "last_coding_task": _last_coding_task(),
        "preferences": prefs,
        "quick_actions": [
            {"id": "fix_selection", "label": "Fix selection", "chat": "fix selection"},
            {"id": "explain", "label": "Explain selection", "chat": "explain selection"},
            {"id": "run_tests", "label": "Run tests", "chat": "run tests for"},
            {"id": "agent", "label": "Coding agent", "chat": "implement "},
            {"id": "vision_fix", "label": "Vision bug fix", "experimental": True},
            {"id": "spec_to_code", "label": "Spec → code", "experimental": True},
        ],
        "links": {
            "projects": "projects",
            "job_center": "jobs",
            "models": "models",
            "activity": "activity",
            "chat": "chat",
            "planner": "planner",
        },
        "empty_states": {
            "no_root": not bool(guardrails.get("coding_root") or write_target),
            "no_proposals": not open_props,
            "no_history": not history_preview,
            "no_jobs": not _recent_jobs(1),
        },
        "shortcut": "Ctrl+Shift+C",
    }
