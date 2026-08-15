"""Projects workspace services — home dashboard, briefing, continue, suggestions.

Projects is Aria's Workspace Identity Layer — not a PM / issue tracker.
"""

from __future__ import annotations

import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.project_services")


def _clip(text: str, n: int = 140) -> str:
    t = (text or "").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def _today() -> str:
    return datetime.now().date().isoformat()


def switch_project(slug: str) -> dict[str, Any]:
    from jarvis.active_project import set_active_slug

    payload = set_active_slug(slug)
    effects = payload.get("effects") or {}
    return {
        "ok": bool(effects.get("ok", True)) and not effects.get("errors"),
        "slug": payload.get("slug") or slug,
        "effects": effects,
        "identity": (effects.get("identity") or {}),
        "message": _effects_message(effects),
    }


def clear_project() -> dict[str, Any]:
    return switch_project("")


def _effects_message(effects: dict[str, Any]) -> str:
    changed = effects.get("changed") or {}
    identity = effects.get("identity") or {}
    lines = []
    if identity.get("slug"):
        lines.append(f"Active workspace: **{identity.get('title') or identity['slug']}** (`{identity['slug']}`)")
    else:
        lines.append("Cleared active project.")
    mapping = [
        ("coding_root", "Coding root"),
        ("memory_namespace", "Memory namespace"),
        ("knowledge_namespace", "Knowledge namespace"),
        ("checkpoint_namespace", "Checkpoint"),
        ("project_slug", "Project identity"),
    ]
    for key, label in mapping:
        if key in changed:
            lines.append(f"✓ {label}: `{changed[key]}`")
    if effects.get("browser_session"):
        lines.append(f"✓ Browser session: `{effects['browser_session']}`")
    if effects.get("git_path"):
        lines.append(f"✓ Git repository: `{effects['git_path']}`")
    for err in effects.get("errors") or []:
        lines.append(f"⚠ {err}")
    return "\n".join(lines)


def continue_project(slug: str | None = None) -> dict[str, Any]:
    """One action restores full workspace identity for a project."""
    from jarvis.active_project import get_active_slug

    target = (slug or get_active_slug() or "").strip()
    if not target:
        return {"ok": False, "message": "No project to continue. Switch to a project first."}
    result = switch_project(target)
    home = project_home(target)
    result["home"] = home
    result["continue"] = {
        "coding_root": (result.get("identity") or {}).get("coding_root"),
        "memory_namespace": (result.get("identity") or {}).get("memory_namespace"),
        "knowledge_namespace": (result.get("identity") or {}).get("knowledge_namespace"),
        "browser_session": (result.get("identity") or {}).get("browser_session"),
        "git_path": (result.get("identity") or {}).get("git_path"),
        "checkpoint": (home.get("ai_context") or {}).get("checkpoint"),
        "journal_today": (home.get("today") or {}).get("journal_preview"),
    }
    result["message"] = (
        f"**Continued project `{target}`**\n\n"
        + result.get("message", "")
        + "\n\nUse Project Home or say **project briefing** for where you left off."
    )
    return result


def project_home(slug: str | None = None) -> dict[str, Any]:
    from jarvis.active_project import get_active_slug, identity_for_slug
    from jarvis.project_registry import get_project, list_projects

    active = get_active_slug()
    target = (slug or active or "").strip()
    # Owner picker: never surface archived or QA/cert artifacts.
    projects = list_projects(include_archived=False, include_qa=False)
    if not target:
        return {
            "ok": True,
            "active": "",
            "project": None,
            "identity": identity_for_slug(""),
            "projects": projects,
            "effects": _empty_effects(),
            "continue_working": [],
            "today": {},
            "coding": {},
            "ai_context": {},
            "journal": {},
            "memory": {},
            "knowledge": {},
            "quick_actions": _quick_actions(""),
        }

    meta = get_project(target)
    if not meta:
        return {"ok": False, "message": f"Unknown project: {target}", "active": active}

    identity = identity_for_slug(target)
    coding = _coding_section(identity)
    today = _today_workspace(target, identity, coding=coding)
    ai = _ai_context(target, identity)
    journal = _journal_section(target)
    memory = _memory_section(target)
    knowledge = _knowledge_section(target, identity)

    return {
        "ok": True,
        "active": active,
        "is_active": active == target,
        "project": meta,
        "identity": identity,
        "projects": projects,
        "effects": {
            "coding_root": identity.get("coding_root") or "—",
            "memory_namespace": identity.get("memory_namespace") or "—",
            "knowledge_namespace": identity.get("knowledge_namespace") or "—",
            "browser_session": identity.get("browser_session") or "—",
            "checkpoint": identity.get("checkpoint_namespace") or "—",
            "git_repository": identity.get("git_path") or "—",
            "workspace": identity.get("workspace_root") or "—",
        },
        "continue_working": [
            {"id": "coding", "label": "Resume Coding", "view": "chat"},
            {"id": "journal", "label": "Open Today's Journal", "view": "journal", "tab": "projects"},
            {"id": "documents", "label": "Open Documents", "view": "documents"},
            {"id": "memory", "label": "Open Memory", "view": "memory"},
            {"id": "checkpoint", "label": "Open Checkpoint", "view": "memory", "focus": "checkpoint"},
            {"id": "ai", "label": "Continue AI Session", "view": "chat"},
        ],
        "today": today,
        "coding": coding,
        "ai_context": ai,
        "journal": journal,
        "memory": memory,
        "knowledge": knowledge,
        "quick_actions": _quick_actions(target, archived=bool(meta.get("archived"))),
        "recent_activity": _recent_activity(target, today, coding, journal),
    }


def _empty_effects() -> dict[str, str]:
    return {
        "coding_root": "—",
        "memory_namespace": "default",
        "knowledge_namespace": "—",
        "browser_session": "—",
        "checkpoint": "—",
        "git_repository": "—",
        "workspace": "—",
    }


def _quick_actions(slug: str, *, archived: bool = False) -> list[dict[str, str]]:
    if not slug:
        return [
            {"id": "create", "label": "New Project"},
            {"id": "import", "label": "Import Repository"},
        ]
    actions = [
        {"id": "rename", "label": "Rename"},
        {"id": "open_folder", "label": "Open Folder"},
        {"id": "import", "label": "Import Repository"},
        {"id": "export", "label": "Export"},
        {"id": "briefing", "label": "Project Briefing"},
        {"id": "continue", "label": "Continue Project"},
    ]
    if archived:
        actions.append({"id": "restore", "label": "Restore"})
    else:
        actions.append({"id": "archive", "label": "Archive"})
    return actions


def _git_status(root: str) -> dict[str, Any]:
    if not root or not Path(root).is_dir():
        return {"ok": False, "branch": "", "status": "", "commits_today": []}
    try:
        branch = subprocess.run(
            ["git", "-C", root, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        status = subprocess.run(
            ["git", "-C", root, "status", "-sb"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        log_proc = subprocess.run(
            ["git", "-C", root, "log", f"--since={_today()} 00:00:00", "--oneline", "-8"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        commits = [ln.strip() for ln in (log_proc.stdout or "").splitlines() if ln.strip()]
        return {
            "ok": True,
            "branch": (branch.stdout or "").strip() if branch.returncode == 0 else "",
            "status": (status.stdout or "").strip() if status.returncode == 0 else "",
            "commits_today": commits,
        }
    except Exception as exc:
        return {"ok": False, "branch": "", "status": str(exc), "commits_today": []}


def _coding_section(identity: dict[str, Any]) -> dict[str, Any]:
    root = identity.get("coding_root") or identity.get("git_path") or ""
    git = _git_status(root)
    indexed = False
    try:
        from jarvis.knowledge.git_sync import list_repo_states

        for st in list_repo_states():
            path = getattr(st, "path", None) or getattr(st, "repo_path", None) or ""
            if path and root and Path(str(path)).resolve() == Path(root).resolve():
                indexed = True
                break
    except Exception:
        pass
    return {
        "repository": root or "—",
        "branch": git.get("branch") or "—",
        "git_status": git.get("status") or "—",
        "coding_root": identity.get("coding_root") or "—",
        "knowledge_index": "indexed" if indexed else "not indexed",
        "workspace_session": identity.get("workspace_root") or "—",
        "commits_today": git.get("commits_today") or [],
    }


def _today_workspace(slug: str, identity: dict[str, Any], *, coding: dict[str, Any] | None = None) -> dict[str, Any]:
    journal_preview = ""
    bullets: list[str] = []
    try:
        from jarvis.project_journal import ProjectJournal

        j = ProjectJournal(slug)
        j.ensure(title=slug)
        page = j.daily_get(_today())
        for b in (page.get("bullets") or [])[-6:]:
            bullets.append(_clip(b.get("content") or "", 120))
        journal_preview = " · ".join(bullets[:3]) if bullets else "(empty today)"
    except Exception as exc:
        journal_preview = f"(journal unavailable: {exc})"

    coding = coding if coding is not None else _coding_section(identity)
    memories: list[str] = []
    candidates: list[dict] = []
    try:
        from jarvis.memory_services import list_candidates

        for c in (list_candidates(status="pending").get("candidates") or [])[:8]:
            if (c.get("namespace") or "") in (slug, f"project:{slug}", "default"):
                if (c.get("namespace") or "") in (slug, f"project:{slug}") or slug in (c.get("content") or ""):
                    candidates.append({"id": c.get("id"), "content": _clip(c.get("content") or "", 100)})
    except Exception:
        pass
    try:
        from jarvis.assistant_instance import get_assistant

        mem = get_assistant().memory
        # Local namespace listing only — never pay ACM semantic search on every Project Home poll.
        rows = []
        if hasattr(mem, "list_entries"):
            rows = mem.list_entries(namespace=slug, limit=5) or []
        elif hasattr(mem, "list"):
            rows = mem.list(namespace=slug, limit=5) or []
        elif hasattr(mem, "get_all"):
            rows = [e for e in (mem.get_all() or []) if (e.get("namespace") or "") == slug][:5]
        for h in rows:
            memories.append(_clip(h.get("content") or h.get("text") or str(h), 100))
    except Exception:
        pass

    open_files: list[str] = []
    try:
        from jarvis.editor_context import get_context

        ctx = get_context(max_age_s=600)
        if ctx and (ctx.relative_file or ctx.active_file):
            open_files.append(ctx.relative_file or ctx.active_file)
    except Exception:
        pass

    return {
        "date": _today(),
        "journal_preview": journal_preview,
        "journal_bullets": bullets,
        "recent_commits": coding.get("commits_today") or [],
        "open_files": open_files,
        "recent_conversations": [],
        "recent_memories": memories,
        "pending_candidates": candidates,
    }


def _ai_context(slug: str, identity: dict[str, Any]) -> dict[str, Any]:
    checkpoint = ""
    try:
        from jarvis.assistant_instance import get_assistant

        mem = get_assistant().memory
        ns = identity.get("checkpoint_namespace") or slug
        cp = None
        if hasattr(mem, "latest_checkpoint"):
            cp = mem.latest_checkpoint(ns) or mem.latest_checkpoint()
        if cp:
            checkpoint = _clip(cp.get("content") or "", 400)
    except Exception:
        pass
    return {
        "checkpoint": checkpoint or "(none yet — say save where I left off)",
        "project_summary": "",
        "recent_learning": [],
        "memory_namespace": identity.get("memory_namespace"),
        "knowledge_namespace": identity.get("knowledge_namespace"),
        "relevant_documents": [],
        "recent_retrieval": [],
    }


def _journal_section(slug: str) -> dict[str, Any]:
    try:
        from jarvis.project_journal import ProjectJournal

        j = ProjectJournal(slug)
        j.ensure(title=slug)
        days = sorted((j.data.get("daily_log") or {}).keys(), reverse=True)
        today = _today()
        page = j.daily_get(today) if today in (j.data.get("daily_log") or {}) else {}
        return {
            "slug": slug,
            "today": today,
            "today_bullets": len(page.get("bullets") or []),
            "recent_days": days[:10],
            "day_count": len(days),
            "deep_link": f"journal?tab=projects&slug={slug}",
        }
    except Exception as exc:
        return {"slug": slug, "error": str(exc), "deep_link": f"journal?tab=projects&slug={slug}"}


def _memory_section(slug: str) -> dict[str, Any]:
    candidates: list[dict] = []
    recent: list[str] = []
    try:
        from jarvis.memory_services import list_candidates

        for c in (list_candidates(status="pending").get("candidates") or [])[:12]:
            ns = c.get("namespace") or ""
            if ns in (slug, f"project:{slug}"):
                candidates.append({"id": c.get("id"), "content": _clip(c.get("content") or "", 100)})
    except Exception:
        pass
    try:
        from jarvis.assistant_instance import get_assistant

        mem = get_assistant().memory
        # Fast local namespace read — Project Home must not call semantic search (SYS-P01 class).
        rows = []
        if hasattr(mem, "list_entries"):
            rows = mem.list_entries(namespace=slug, limit=6) or []
        elif hasattr(mem, "list"):
            rows = mem.list(namespace=slug, limit=6) or []
        elif hasattr(mem, "get_all"):
            rows = [e for e in (mem.get_all() or []) if (e.get("namespace") or "") == slug][:6]
        for h in rows:
            recent.append(_clip(h.get("content") or h.get("text") or "", 100))
    except Exception:
        pass
    return {
        "namespace": slug,
        "recent_memories": recent,
        "candidates": candidates,
        "deep_link": "memory",
    }


def _knowledge_section(slug: str, identity: dict[str, Any]) -> dict[str, Any]:
    repos: list[dict] = []
    try:
        from jarvis.knowledge.git_sync import list_repo_states

        root = identity.get("git_path") or identity.get("coding_root") or ""
        for st in list_repo_states():
            path = str(getattr(st, "path", None) or getattr(st, "repo_path", None) or "")
            ns = str(getattr(st, "namespace", "") or "")
            if ns == f"project:{slug}" or (root and path and Path(path).resolve() == Path(root).resolve()):
                repos.append(
                    {
                        "path": path,
                        "namespace": ns or f"project:{slug}",
                        "dirty": bool(getattr(st, "dirty", False)),
                        "branch": getattr(st, "branch", "") or "",
                    }
                )
    except Exception:
        pass
    return {
        "namespace": identity.get("knowledge_namespace"),
        "indexed_repositories": repos,
        "coverage": "ready" if repos else "pending",
        "deep_link": "documents",
    }


def _recent_activity(slug: str, today: dict, coding: dict, journal: dict) -> list[str]:
    items: list[str] = []
    for c in (coding.get("commits_today") or [])[:3]:
        items.append(f"commit: {c}")
    if journal.get("today_bullets"):
        items.append(f"journal: {journal['today_bullets']} bullet(s) today")
    for m in (today.get("recent_memories") or [])[:2]:
        items.append(f"memory: {m}")
    return items


def project_briefing(slug: str | None = None) -> dict[str, Any]:
    """User-initiated project briefing — where we left off."""
    from jarvis.active_project import get_active_slug

    target = (slug or get_active_slug() or "").strip()
    if not target:
        return {"ok": False, "message": "No active project. Switch to a project first."}
    home = project_home(target)
    if not home.get("ok"):
        return home
    meta = home.get("project") or {}
    today = home.get("today") or {}
    coding = home.get("coding") or {}
    ai = home.get("ai_context") or {}
    journal = home.get("journal") or {}
    memory = home.get("memory") or {}

    lines = [
        f"# Project briefing — {meta.get('title') or target}",
        "",
        f"**Slug:** `{target}`",
        f"**Status:** {'archived' if meta.get('archived') else 'active'}",
        "",
        "## Where we left off",
        ai.get("checkpoint") or "(no checkpoint)",
        "",
        "## Current objective",
        meta.get("description") or "(no description set)",
        "",
        "## Recent commits",
    ]
    commits = coding.get("commits_today") or []
    if commits:
        lines.extend(f"- {c}" for c in commits[:6])
    else:
        lines.append("- (none today)")
    lines.extend(["", "## Today's journal"])
    bullets = today.get("journal_bullets") or []
    if bullets:
        lines.extend(f"- {b}" for b in bullets[:6])
    else:
        lines.append("- (empty)")
    lines.extend(["", "## Recent memories"])
    mems = memory.get("recent_memories") or today.get("recent_memories") or []
    if mems:
        lines.extend(f"- {m}" for m in mems[:5])
    else:
        lines.append("- (none found)")
    lines.extend(
        [
            "",
            "## Coding",
            f"- Root: `{coding.get('coding_root')}`",
            f"- Branch: `{coding.get('branch')}`",
            f"- Index: {coding.get('knowledge_index')}",
            "",
            "## Open questions",
            "- Review checkpoint and journal for blockers.",
            "- Say **continue project** to restore the full workspace.",
        ]
    )
    text = "\n".join(lines)
    return {
        "ok": True,
        "slug": target,
        "briefing": text,
        "home": home,
        "message": text,
    }


def suggest_projects(hint: str = "") -> dict[str, Any]:
    """Suggest projects from context — never auto-switch."""
    from jarvis.project_registry import list_projects

    projects = list_projects()
    hint_l = (hint or "").lower()
    scored: list[tuple[int, dict]] = []
    for p in projects:
        score = 0
        blob = f"{p.get('title')} {p.get('slug')} {p.get('description')} {p.get('git_path')}".lower()
        if hint_l and hint_l in blob:
            score += 5
        if p.get("last_opened"):
            score += 2
        if p.get("git_path"):
            score += 1
        scored.append((score, p))
    scored.sort(key=lambda x: (-x[0], -(1 if x[1].get("updated") else 0)))
    suggestions = [
        {
            "slug": p["slug"],
            "title": p.get("title") or p["slug"],
            "reason": "matches conversation" if hint_l and hint_l in f"{p.get('title')} {p.get('slug')}".lower() else "recent workspace",
            "confirm_required": True,
        }
        for _, p in scored[:5]
    ]
    return {
        "ok": True,
        "suggestions": suggestions,
        "message": "Confirm before switching — Aria never auto-switches projects.",
    }


def export_project(slug: str) -> dict[str, Any]:
    from jarvis.project_registry import get_project
    from jarvis.active_project import identity_for_slug

    meta = get_project(slug)
    if not meta:
        return {"ok": False, "message": f"Unknown project: {slug}"}
    return {
        "ok": True,
        "export": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "project": {k: v for k, v in meta.items() if k != "paths"},
            "identity": identity_for_slug(slug),
            "paths": meta.get("paths"),
        },
    }


def project_status(slug: str | None = None) -> dict[str, Any]:
    home = project_home(slug)
    if not home.get("ok"):
        return home
    identity = home.get("identity") or {}
    coding = home.get("coding") or {}
    lines = [
        f"**Project:** { (home.get('project') or {}).get('title') or identity.get('slug') or 'none'}",
        f"**Slug:** `{identity.get('slug') or '—'}`",
        f"**Coding root:** `{identity.get('coding_root') or '—'}`",
        f"**Memory NS:** `{identity.get('memory_namespace') or '—'}`",
        f"**Knowledge NS:** `{identity.get('knowledge_namespace') or '—'}`",
        f"**Git:** `{identity.get('git_path') or '—'}`",
        f"**Branch:** `{coding.get('branch') or '—'}`",
        f"**Browser:** `{identity.get('browser_session') or '—'}`",
    ]
    return {"ok": True, "status": "\n".join(lines), "home": home, "message": "\n".join(lines)}
