"""Projects HTTP API — workspace identity layer."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_routes(app, assistant) -> None:
    @app.get("/api/projects")
    def projects_list(include_qa: bool = False, include_archived: bool = False):
        from jarvis.project_registry import registry_snapshot

        return {"ok": True, **registry_snapshot(include_qa=include_qa, include_archived=include_archived)}

    @app.get("/api/projects/home")
    def projects_home(slug: str = ""):
        from jarvis.project_services import project_home

        return project_home(slug or None)

    @app.get("/api/projects/status")
    def projects_status(slug: str = ""):
        from jarvis.project_services import project_status

        return project_status(slug or None)

    @app.get("/api/projects/briefing")
    def projects_briefing_get(slug: str = ""):
        from jarvis.project_services import project_briefing

        return project_briefing(slug or None)

    @app.post("/api/projects/briefing")
    async def projects_briefing_post(request: Request):
        from jarvis.project_services import project_briefing

        body = await request.json()
        return project_briefing((body.get("slug") or "").strip() or None)

    @app.post("/api/projects/continue")
    async def projects_continue(request: Request):
        from jarvis.project_services import continue_project

        body = await request.json()
        return continue_project((body.get("slug") or "").strip() or None)

    @app.get("/api/projects/suggest")
    def projects_suggest(q: str = ""):
        from jarvis.project_services import suggest_projects

        return suggest_projects(q)

    @app.post("/api/projects")
    async def projects_create(request: Request):
        from jarvis.project_registry import create_project
        from jarvis.project_services import switch_project

        body = await request.json()
        title = (body.get("title") or "").strip()
        if not title:
            return JSONResponse(status_code=400, content={"ok": False, "message": "title required"})
        meta = create_project(
            title,
            description=body.get("description") or "",
            git_path=(body.get("git_path") or "").strip() or None,
            qa_artifact=bool(body.get("qa_artifact")),
            origin=(body.get("origin") or "").strip() or None,
        )
        switch = None
        if body.get("activate", True):
            switch = switch_project(meta["slug"])
        return {"ok": True, "project": meta, "switch": switch}

    @app.post("/api/projects/switch")
    async def projects_switch(request: Request):
        from jarvis.project_services import switch_project

        body = await request.json()
        slug = (body.get("slug") or "").strip()
        try:
            result = switch_project(slug)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": result.get("ok", True), **result}

    @app.post("/api/projects/import-git")
    async def projects_import_git(request: Request):
        from jarvis.project_registry import import_git_repo
        from jarvis.project_services import switch_project

        body = await request.json()
        path = (body.get("path") or "").strip()
        if not path:
            return JSONResponse(status_code=400, content={"ok": False, "message": "path required"})
        try:
            meta = import_git_repo(path, title=body.get("title") or "")
            switch = switch_project(meta["slug"])
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": True, "project": meta, "switch": switch}

    @app.get("/api/projects/active")
    def projects_active():
        from jarvis.active_project import get_active_project, identity_for_slug, get_active_slug

        slug = get_active_slug()
        return {
            "ok": True,
            "project": get_active_project(),
            "identity": identity_for_slug(slug),
            "slug": slug,
        }

    @app.post("/api/projects/{slug}/archive")
    def projects_archive(slug: str):
        from jarvis.active_project import get_active_slug, set_active_slug
        from jarvis.project_registry import archive_project

        ok = archive_project(slug, archived=True)
        cleared_active = False
        if ok and get_active_slug() == slug:
            # Archiving the active workspace must not leave identity pointing at a tombstone.
            set_active_slug("")
            cleared_active = True
        return {"ok": ok, "cleared_active": cleared_active}

    @app.post("/api/projects/{slug}/restore")
    def projects_restore(slug: str):
        from jarvis.project_registry import archive_project

        return {"ok": archive_project(slug, archived=False)}

    @app.patch("/api/projects/{slug}")
    async def projects_update(slug: str, request: Request):
        from jarvis.project_registry import update_project

        body = await request.json()
        meta = update_project(
            slug,
            title=body.get("title"),
            description=body.get("description"),
            git_path=body.get("git_path") if "git_path" in body else None,
        )
        if not meta:
            return JSONResponse(status_code=404, content={"ok": False, "message": "not found"})
        return {"ok": True, "project": meta}

    @app.get("/api/projects/{slug}/export")
    def projects_export(slug: str):
        from jarvis.project_services import export_project

        return export_project(slug)

    @app.get("/api/projects/{slug}")
    def projects_get(slug: str):
        from jarvis.project_services import project_home

        return project_home(slug)
