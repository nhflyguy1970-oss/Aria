"""Gallery product HTTP API."""

from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse, Response


def register_routes(app, assistant) -> None:
    @app.get("/api/gallery/home")
    def gallery_home():
        from jarvis.gallery_product.home import gallery_home_snapshot

        return gallery_home_snapshot(assistant)

    @app.get("/api/gallery/v2")
    def gallery_list_v2(
        offset: int = 0,
        limit: int = 48,
        q: str = "",
        sort: str = "newest",
        include_artifacts: bool = False,
        kinds: str = "",
        project: str = "",
        favorites: bool = False,
        collection: str = "",
    ):
        from jarvis.gallery_product.library import list_images

        return list_images(
            offset=offset,
            limit=limit,
            query=q,
            sort=sort,
            include_artifacts=include_artifacts,
            kinds=kinds,
            project=project,
            favorites_only=favorites,
            collection_id=collection,
        )

    @app.post("/api/gallery/generate")
    async def gallery_generate(request: Request):
        from jarvis.gallery_product.activity_bridge import emit_gallery_event
        from jarvis.gallery_product.generate import submit_generate

        body = await request.json()
        result = submit_generate(assistant, **{k: v for k, v in body.items() if k != "source"})
        if result.get("ok"):
            emit_gallery_event(
                "gallery_generate_queued",
                str(body.get("prompt") or "")[:120],
                job_id=result.get("job_id"),
            )
        return result

    @app.post("/api/gallery/variation")
    async def gallery_variation(request: Request):
        from jarvis.gallery_product.generate import submit_variation

        body = await request.json()
        return submit_variation(
            assistant,
            path=str(body.get("path") or ""),
            prompt=str(body.get("prompt") or ""),
        )

    @app.post("/api/gallery/soft-delete")
    async def gallery_soft_delete(request: Request):
        from jarvis.gallery_product.activity_bridge import emit_gallery_event
        from jarvis.gallery_product.library import resolve_image
        from jarvis.gallery_product.soft_delete import soft_delete

        body = await request.json()
        name = str(body.get("name") or "")
        path = resolve_image(name)
        if not path:
            return JSONResponse(status_code=404, content={"ok": False, "message": "Not found"})
        out = soft_delete(path)
        if out.get("ok"):
            emit_gallery_event("gallery_soft_delete", name, trash_id=out.get("trash_id"))
        return out

    @app.post("/api/gallery/restore")
    async def gallery_restore(request: Request):
        from jarvis.gallery_product.soft_delete import restore

        body = await request.json()
        return restore(str(body.get("trash_id") or body.get("id") or ""))

    @app.post("/api/gallery/purge")
    async def gallery_purge(request: Request):
        from jarvis.gallery_product.soft_delete import purge

        body = await request.json()
        return purge(str(body.get("trash_id") or body.get("id") or ""))

    @app.get("/api/gallery/trash")
    def gallery_trash():
        from jarvis.gallery_product.soft_delete import list_trash

        return list_trash()

    @app.get("/api/gallery/meta/{name}")
    def gallery_meta_get(name: str):
        from jarvis.gallery_product.metadata import get_meta
        from jarvis.gallery_product.visibility import is_restricted_for_viewer

        if is_restricted_for_viewer(name):
            return {"ok": True, "restricted": True, "meta": {"uncensored": True}}
        return {"ok": True, "meta": get_meta(name)}

    @app.post("/api/gallery/meta/{name}")
    async def gallery_meta_set(name: str, request: Request):
        from jarvis.gallery_product.metadata import set_meta

        body = await request.json()
        return set_meta(name, body.get("meta") or body)

    @app.delete("/api/gallery/meta/{name}")
    def gallery_meta_delete(name: str):
        from jarvis.gallery_product.metadata import delete_meta

        return delete_meta(name)

    @app.post("/api/gallery/meta/{name}/vision")
    def gallery_meta_vision(name: str):
        from jarvis.gallery_product.library import resolve_image
        from jarvis.gallery_product.metadata import generate_vision_meta

        path = resolve_image(name)
        if not path:
            return JSONResponse(status_code=404, content={"ok": False, "message": "Not found"})
        return generate_vision_meta(name, str(path), assistant=assistant)

    @app.get("/api/gallery/favorites")
    def gallery_favorites():
        from jarvis.gallery_product.collections import list_favorites

        return list_favorites()

    @app.post("/api/gallery/favorites/toggle")
    async def gallery_fav_toggle(request: Request):
        from jarvis.gallery_product.collections import toggle_favorite

        body = await request.json()
        return toggle_favorite(str(body.get("name") or ""))

    @app.get("/api/gallery/collections")
    def gallery_collections():
        from jarvis.gallery_product.collections import list_collections

        return list_collections()

    @app.post("/api/gallery/collections")
    async def gallery_collections_create(request: Request):
        from jarvis.gallery_product.collections import create_collection

        body = await request.json()
        return create_collection(str(body.get("title") or "Collection"), names=body.get("names") or [])

    @app.post("/api/gallery/collections/add")
    async def gallery_collections_add(request: Request):
        from jarvis.gallery_product.collections import add_to_collection

        body = await request.json()
        return add_to_collection(str(body.get("id") or ""), str(body.get("name") or ""))

    @app.post("/api/gallery/clusters")
    def gallery_clusters():
        from jarvis.gallery_product.similarity import cluster_similar

        return cluster_similar()

    @app.post("/api/gallery/storyboard-suggest")
    async def gallery_storyboard_suggest(request: Request):
        from jarvis.gallery_product.storyboard import suggest_storyboard_order

        body = await request.json()
        return suggest_storyboard_order(body.get("names") or [])

    @app.post("/api/gallery/voice")
    async def gallery_voice(request: Request):
        from jarvis.gallery_product.voice_bridge import handle_voice_command

        body = await request.json()
        return handle_voice_command(str(body.get("text") or ""), assistant=assistant)

    @app.post("/api/gallery/vision-coding")
    async def gallery_vision_coding(request: Request):
        from jarvis.gallery_product.vision_to_coding import vision_to_coding

        body = await request.json()
        return vision_to_coding(
            assistant,
            image_path=str(body.get("path") or ""),
            hint=str(body.get("hint") or ""),
        )

    @app.post("/api/gallery/save-documents")
    async def gallery_save_documents(request: Request):
        from jarvis.gallery_product.library import resolve_image
        from jarvis.gallery_product.metadata import get_meta
        from jarvis.gallery_product.visibility import is_restricted_for_viewer

        body = await request.json()
        name = str(body.get("name") or "")
        if is_restricted_for_viewer(name):
            return {"ok": False, "message": "Restricted image — cannot export caption in censored mode"}
        path = resolve_image(name)
        if not path:
            return {"ok": False, "message": "Image not found"}
        meta = get_meta(name)
        title = body.get("title") or f"Gallery: {name}"
        text = (
            f"Source image: {name}\n"
            f"Prompt: {meta.get('prompt') or ''}\n"
            f"Caption: {meta.get('caption') or meta.get('vision_description') or ''}\n"
            f"Path: {path}\n"
        )
        try:
            from jarvis.handlers.registry import call_action, has_action

            action = "documents_add" if has_action("documents_add") else (
                "document_add" if has_action("document_add") else ""
            )
            if action:
                return call_action(assistant, action, {"title": title, "text": text, "content": text}, title)
        except Exception as exc:
            return {"ok": False, "message": str(exc)}
        return {"ok": True, "extracted": True, "text": text, "message": "Caption ready (Documents action unavailable)"}

    @app.get("/api/gallery/placeholder")
    def gallery_restricted_placeholder():
        """Tiny SVG placeholder for restricted thumbs (no content leak)."""
        svg = (
            "<svg xmlns='http://www.w3.org/2000/svg' width='384' height='384'>"
            "<defs><filter id='b'><feGaussianBlur stdDeviation='12'/></filter></defs>"
            "<rect width='100%' height='100%' fill='#1a1a1a'/>"
            "<rect width='100%' height='100%' fill='#444' filter='url(#b)' opacity='0.5'/>"
            "<text x='50%' y='48%' fill='#ccc' font-size='18' text-anchor='middle' "
            "font-family='sans-serif'>Restricted</text>"
            "<text x='50%' y='58%' fill='#888' font-size='12' text-anchor='middle' "
            "font-family='sans-serif'>Uncensored profile required</text>"
            "</svg>"
        )
        return Response(content=svg.encode("utf-8"), media_type="image/svg+xml")
