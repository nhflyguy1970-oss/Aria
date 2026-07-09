"""Daily AI workflow — proactive answers Jeff uses every morning."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger("jarvis.workflows.daily")


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _since_yesterday() -> float:
    return (_utc_now() - timedelta(hours=24)).timestamp()


def what_am_i_working_on(assistant: Any) -> dict[str, Any]:
    parts: list[str] = []
    try:
        from jarvis.active_project import get_active_slug

        slug = get_active_slug()
        if slug:
            parts.append(f"**Active project:** `{slug}`")
    except Exception:
        pass

    try:
        from jarvis.planner_store import load_planner

        planner = load_planner()
        tasks = [t for t in (planner.get("tasks") or []) if not t.get("done")][:5]
        if tasks:
            parts.append("**Open planner tasks:**")
            for task in tasks:
                parts.append(f"- {task.get('title') or task.get('text') or task}")
    except Exception:
        pass

    try:
        hits = assistant.memory.search("current project task working on", limit=5)
        if hits:
            parts.append("**Recent memory:**")
            for hit in hits[:3]:
                parts.append(f"- {(hit.get('content') or '')[:160]}")
    except Exception:
        pass

    message = (
        "\n".join(parts)
        if parts
        else "No active project or tasks detected. Say what you want to focus on."
    )
    return {"ok": True, "message": message, "type": "daily_workflow"}


def what_changed_since_yesterday(assistant: Any) -> dict[str, Any]:
    lines: list[str] = ["## Changes since yesterday", ""]
    since = _since_yesterday()

    try:
        from jarvis.knowledge.git_sync import list_repo_states

        changed = []
        for st in list_repo_states():
            sync_ts = st.last_sync or st.last_successful_sync or st.last_indexed
            if sync_ts and sync_ts >= (_utc_now() - timedelta(hours=24)).strftime("%Y-%m-%d"):
                head = (st.head or "")[:8]
                changed.append(f"- **{st.label}** — commit `{head}` on `{st.branch}`")
        if changed:
            lines.append("**Git repositories:**")
            lines.extend(changed)
    except Exception as exc:
        logger.debug("git changes: %s", exc)

    try:
        from jarvis.modules.journal import _today, _yesterday

        today = _today()
        yesterday = _yesterday()
        if yesterday and yesterday.get("bullets"):
            lines.append("\n**Yesterday's journal:**")
            for bullet in yesterday.get("bullets", [])[:5]:
                lines.append(f"- {bullet.get('text', '')[:120]}")
        if today and today.get("bullets"):
            lines.append("\n**Today so far:**")
            for bullet in today.get("bullets", [])[:3]:
                lines.append(f"- {bullet.get('text', '')[:120]}")
    except Exception:
        pass

    try:
        from jarvis.automation.ops import last_maintenance

        maint = last_maintenance()
        if maint.get("ok") and maint.get("finished_at", 0) >= since:
            lines.append(f"\n**Overnight maintenance:** completed ({maint.get('elapsed_ms', 0)}ms)")
    except Exception:
        pass

    if len(lines) <= 2:
        lines.append("_No significant changes detected in the last 24 hours._")

    return {"ok": True, "message": "\n".join(lines), "type": "daily_workflow"}


def anything_broken() -> dict[str, Any]:
    from jarvis.workstation.operations import diagnose, format_report

    report = diagnose(force=True)
    message = format_report(force=True)
    return {
        "ok": report.get("ok", False),
        "message": message,
        "data": report,
        "type": "daily_workflow",
    }


def repos_need_attention() -> dict[str, Any]:
    from jarvis.knowledge.git_sync import list_repo_states

    states = list_repo_states()
    attention = [s for s in states if s.dirty or s.open_prs]
    if not attention:
        return {
            "ok": True,
            "message": "All tracked repositories look clean — no dirty trees or open PRs.",
            "repos": 0,
        }

    lines = ["## Repositories needing attention", ""]
    for st in attention[:8]:
        flags = []
        if st.dirty:
            flags.append("dirty")
        if st.open_prs:
            flags.append(f"{len(st.open_prs)} PR(s)")
        lines.append(f"- **{st.label}** (`{st.branch}`) — {', '.join(flags)}")
    return {"ok": True, "message": "\n".join(lines), "repos": len(attention)}


def overnight_summary(assistant: Any) -> dict[str, Any]:
    parts = [
        what_changed_since_yesterday(assistant).get("message", ""),
        "",
        repos_need_attention().get("message", ""),
    ]
    broken = anything_broken()
    if not broken.get("ok"):
        parts.extend(["", broken.get("message", "")])

    try:
        from jarvis.jobs.checkpointed import list_jobs

        recent = [j for j in list_jobs() if j.created_at >= _since_yesterday()][:5]
        if recent:
            parts.append("\n**Agent jobs (24h):**")
            for job in recent:
                parts.append(f"- `{job.id}` {job.status}: {job.goal[:80]}")
    except Exception:
        pass

    return {"ok": True, "message": "\n".join(p for p in parts if p), "type": "daily_workflow"}


def what_should_i_work_on_next(assistant: Any) -> dict[str, Any]:
    lines: list[str] = ["## Suggested next steps", ""]

    broken = anything_broken()
    if not broken.get("ok"):
        issues = (broken.get("data") or {}).get("issues") or []
        critical = [i for i in issues if i.get("severity") == "critical"]
        if critical:
            lines.append(f"1. Fix **{critical[0].get('label')}** — required component offline")
            return {"ok": True, "message": "\n".join(lines)}

    repos = repos_need_attention()
    if repos.get("repos", 0) > 0:
        lines.append("1. Review repositories with dirty trees or open PRs")
        lines.append("2. Continue your active project task")

    try:
        from jarvis.planner_store import load_planner

        tasks = [t for t in (load_planner().get("tasks") or []) if not t.get("done")]
        if tasks:
            top = tasks[0]
            lines.append(f"1. **{top.get('title') or top.get('text')}** (planner)")
    except Exception:
        pass

    if len(lines) == 2:
        lines.append("1. Set an active project and describe what you want to accomplish today")

    return {"ok": True, "message": "\n".join(lines), "type": "daily_workflow"}


def review_current_branch() -> dict[str, Any]:
    try:
        import subprocess
        from pathlib import Path

        from jarvis.active_project import get_active_slug
        from jarvis.project_registry import get_project

        slug = get_active_slug()
        repo = ""
        if slug:
            meta = get_project(slug) or {}
            repo = str(meta.get("git_path") or "").strip()
        if not repo:
            from jarvis.config import PROJECT_ROOT

            repo = str(PROJECT_ROOT)
        repo_path = Path(repo).expanduser().resolve()
        if not repo_path.is_dir():
            return {"ok": False, "message": "No active project with a git repository."}

        branch = subprocess.run(
            ["git", "-C", str(repo_path), "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(repo_path), "status", "--short"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        log = subprocess.run(
            ["git", "-C", str(repo_path), "log", "--oneline", "-5"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()

        lines = [
            f"## Branch review — `{branch}`",
            f"Repo: `{repo_path}`",
            "",
            "**Recent commits:**",
            log or "_none_",
        ]
        if status:
            lines.extend(["", "**Uncommitted changes:**", f"```\n{status[:2000]}\n```"])
        else:
            lines.append("\nWorking tree clean.")
        return {"ok": True, "message": "\n".join(lines), "branch": branch}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def today_recommendations(assistant: Any) -> dict[str, Any]:
    sections = [
        overnight_summary(assistant),
        what_should_i_work_on_next(assistant),
    ]
    try:
        from jarvis.personalization.store import format_preferences_markdown, snapshot

        prefs = format_preferences_markdown(snapshot())
        if "No preferences learned" not in prefs:
            sections.append({"ok": True, "message": prefs})
    except Exception:
        pass

    message = "\n\n---\n\n".join(s.get("message", "") for s in sections if s.get("message"))
    return {"ok": True, "message": message, "type": "daily_workflow"}


def dispatch(intent: str, assistant: Any) -> dict[str, Any]:
    """Route a daily workflow intent to the right handler."""
    key = (intent or "").strip().lower().replace(" ", "_")
    handlers = {
        "what_am_i_working_on": lambda: what_am_i_working_on(assistant),
        "what_changed_since_yesterday": lambda: what_changed_since_yesterday(assistant),
        "anything_broken": anything_broken,
        "repos_need_attention": repos_need_attention,
        "overnight_summary": lambda: overnight_summary(assistant),
        "what_should_i_work_on_next": lambda: what_should_i_work_on_next(assistant),
        "review_current_branch": review_current_branch,
        "today_recommendations": lambda: today_recommendations(assistant),
    }
    handler = handlers.get(key)
    if handler is None:
        return {"ok": False, "message": f"Unknown daily workflow: {intent}"}
    return handler()
