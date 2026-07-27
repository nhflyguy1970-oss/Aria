"""Chat / voice handlers for Projects workspace identity."""

from __future__ import annotations

import re

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


def _resolve_slug(assistant, params: dict, message: str) -> str:
    slug = (params.get("slug") or params.get("project") or "").strip()
    if slug:
        return slug
    text = message or ""
    for pat in (
        r"\b(?:switch|open|use|continue|briefing|status)\s+(?:to\s+)?(?:project\s+)?([\w-]+)\b",
        r"\bproject\s+([\w-]+)\b",
    ):
        m = re.search(pat, text, re.I)
        if m:
            candidate = m.group(1).strip().lower()
            if candidate not in ("list", "status", "briefing", "home", "current", "active", "journal"):
                return candidate
    return (getattr(assistant.session, "project_slug", None) or assistant.session.memory_namespace or "").strip()


@register_action("project_switch", module="projects", description="Switch active project workspace")
def project_switch(assistant, params: dict, message: str) -> dict:
    from jarvis.project_registry import get_project, list_projects
    from jarvis.project_services import switch_project

    slug = _resolve_slug(assistant, params, message)
    slug = re.sub(r"[^\w-]+", "-", slug.lower()).strip("-")
    if not slug or slug in ("default", "none", "clear"):
        result = switch_project("")
        msg = result.pop("message", None) or "Cleared active project."
        return ok(msg, module="projects", **result)

    meta = get_project(slug)
    if not meta:
        # fuzzy title match
        for p in list_projects():
            if slug in (p.get("title") or "").lower().replace(" ", "-") or slug == p.get("slug"):
                meta = p
                slug = p["slug"]
                break
    if not meta:
        return err(
            f"Unknown project `{slug}`. Say **list projects** or create one first.",
            module="projects",
        )
    try:
        result = switch_project(slug)
    except ValueError as exc:
        return err(str(exc), module="projects")
    msg = result.pop("message", None) or f"Switched to **{slug}**."
    return ok(msg, module="projects", **result)


@register_action("project_list", module="projects", description="List projects")
def project_list(assistant, params: dict, message: str) -> dict:
    from jarvis.active_project import get_active_slug
    from jarvis.project_registry import list_projects

    active = get_active_slug()
    projects = list_projects(include_archived=bool(params.get("include_archived")))
    if not projects:
        return ok(
            "No projects yet. Say **create project named My App** or open Projects to import a git repo.",
            module="projects",
        )
    lines = []
    for p in projects:
        mark = " ← active" if p.get("slug") == active else ""
        arch = " [archived]" if p.get("archived") else ""
        git = f" · `{p['git_path']}`" if p.get("git_path") else ""
        lines.append(f"• **{p.get('title') or p['slug']}** (`{p['slug']}`){arch}{git}{mark}")
    return ok("**Projects** (workspace identity)\n\n" + "\n".join(lines), module="projects", projects=projects)


@register_action("project_current", module="projects", description="Show current project")
def project_current(assistant, params: dict, message: str) -> dict:
    from jarvis.active_project import get_active_project, get_active_slug, identity_for_slug

    slug = get_active_slug()
    if not slug:
        return ok("No active project. Say **list projects** or **switch project …**.", module="projects")
    meta = get_active_project() or {}
    identity = identity_for_slug(slug)
    body = (
        f"**Current project:** {meta.get('title') or slug} (`{slug}`)\n\n"
        f"✓ Coding root: `{identity.get('coding_root') or '—'}`\n"
        f"✓ Memory namespace: `{identity.get('memory_namespace')}`\n"
        f"✓ Knowledge namespace: `{identity.get('knowledge_namespace')}`\n"
        f"✓ Git: `{identity.get('git_path') or '—'}`\n"
        f"✓ Browser session: `{identity.get('browser_session')}`"
    )
    return ok(body, module="projects", slug=slug, identity=identity)


@register_action("project_status", module="projects", description="Project workspace status")
def project_status_handler(assistant, params: dict, message: str) -> dict:
    from jarvis.project_services import project_status

    slug = _resolve_slug(assistant, params, message)
    if slug in ("default", "status", "project"):
        slug = ""
    result = project_status(slug or None)
    if not result.get("ok"):
        return err(result.get("message") or "Could not load status.", module="projects")
    msg = result.pop("message", None) or result.pop("status", None) or "Status"
    return ok(msg, module="projects", **result)


@register_action("project_continue", module="projects", description="Continue / restore project workspace")
def project_continue(assistant, params: dict, message: str) -> dict:
    from jarvis.project_services import continue_project

    slug = (params.get("slug") or "").strip()
    if not slug:
        m = re.search(r"\bcontinue\s+(?:project\s+)?([\w-]+)\b", message or "", re.I)
        if m and m.group(1).lower() not in ("project", "working", "work"):
            slug = m.group(1)
    result = continue_project(slug or None)
    if not result.get("ok"):
        return err(result.get("message") or "Could not continue project.", module="projects")
    msg = result.pop("message", None) or "Continued."
    return ok(msg, module="projects", **result)


@register_action("project_briefing", module="projects", description="Generate project briefing")
def project_briefing_handler(assistant, params: dict, message: str) -> dict:
    from jarvis.project_services import project_briefing

    slug = (params.get("slug") or "").strip()
    result = project_briefing(slug or None)
    if not result.get("ok"):
        return err(result.get("message") or "No project for briefing.", module="projects")
    msg = result.pop("briefing", None) or result.pop("message", None) or "Briefing ready."
    return ok(msg, module="projects", **result)


@register_action("project_create", module="projects", description="Create a new project")
def project_create(assistant, params: dict, message: str) -> dict:
    from jarvis.project_registry import create_project
    from jarvis.project_services import switch_project

    title = (params.get("title") or params.get("name") or "").strip()
    if not title:
        m = re.search(
            r"\b(?:create|new)\s+project\s+(?:named\s+|called\s+)?(.+)$",
            message or "",
            re.I,
        )
        title = (m.group(1).strip(" .\"'") if m else "")
    if not title:
        return err("Name the project. Example: **create project named Lab Bench**", module="projects")
    meta = create_project(title, description=params.get("description") or "")
    switch = switch_project(meta["slug"])
    return ok(
        f"Created and activated **{meta.get('title')}** (`{meta['slug']}`).\n\n{switch.get('message', '')}",
        module="projects",
        project=meta,
        switch=switch,
    )


@register_action("project_home", module="projects", description="Open project home summary")
def project_home_handler(assistant, params: dict, message: str) -> dict:
    from jarvis.project_services import project_home, project_status

    result = project_status(_resolve_slug(assistant, params, message) or None)
    if not result.get("ok"):
        return err(result.get("message") or "No project.", module="projects")
    home = result.pop("home", None) or project_home()
    msg = result.pop("message", None) or result.pop("status", None) or ""
    extra = ""
    if home.get("today", {}).get("journal_preview"):
        extra = f"\n\n**Today:** {home['today']['journal_preview']}"
    return ok(
        msg + extra + "\n\n_Open the Projects view for the full Project Home._",
        module="projects",
        home=home,
    )
