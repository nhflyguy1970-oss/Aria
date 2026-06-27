"""Projects HTTP API."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_routes(app, assistant) -> None:
    @app.get("/api/projects")
    def projects_list():
        from jarvis.project_registry import registry_snapshot

        return {"ok": True, **registry_snapshot()}

    @app.post("/api/projects")
    async def projects_create(request: Request):
        from jarvis.project_registry import create_project

        body = await request.json()
        title = (body.get("title") or "").strip()
        if not title:
            return JSONResponse(status_code=400, content={"ok": False, "message": "title required"})
        meta = create_project(title, description=body.get("description") or "")
        return {"ok": True, "project": meta}

    @app.post("/api/projects/switch")
    async def projects_switch(request: Request):
        from jarvis.active_project import set_active_slug

        body = await request.json()
        slug = (body.get("slug") or "").strip()
        try:
            set_active_slug(slug)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": True, "slug": slug}

    @app.post("/api/projects/import-git")
    async def projects_import_git(request: Request):
        from jarvis.active_project import set_active_slug
        from jarvis.project_registry import import_git_repo

        body = await request.json()
        path = (body.get("path") or "").strip()
        if not path:
            return JSONResponse(status_code=400, content={"ok": False, "message": "path required"})
        try:
            meta = import_git_repo(path, title=body.get("title") or "")
            set_active_slug(meta["slug"])
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": True, "project": meta}

    @app.post("/api/projects/{slug}/archive")
    def projects_archive(slug: str):
        from jarvis.project_registry import archive_project

        return {"ok": archive_project(slug, archived=True)}

    @app.get("/api/projects/active")
    def projects_active():
        from jarvis.active_project import get_active_project

        return {"ok": True, "project": get_active_project()}
