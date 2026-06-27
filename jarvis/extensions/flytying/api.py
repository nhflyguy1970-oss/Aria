"""Fly-tying REST API."""

from __future__ import annotations

import json

from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from jarvis.flytying import bridge
from jarvis.flytying.chat import chat_turn, chat_turn_stream, get_model_setting, set_model_setting
from jarvis.flytying.knowledge import seed_memory, sync_library, sync_status


def register_routes(app, assistant) -> None:
    if assistant is not None and getattr(assistant, "memory", None):
        try:
            seed_memory(assistant.memory)
        except Exception:
            pass

    @app.get("/api/flytying/status")
    def api_flytying_status():
        st = bridge.status()
        lib = sync_status()
        lib["blackfly"] = {
            "loaded": st.get("loaded"),
            "scraped_db_path": st.get("scraped_db_path"),
            "record_count": st.get("record_count"),
            "scraped_path": st.get("scraped_path"),
            "scraped_count": st.get("scraped_count"),
            "gold_path": st.get("gold_path"),
            "gold_count": st.get("gold_count"),
            "recipe_source": st.get("recipe_source"),
            "recipe_count": st.get("recipe_count"),
            "rag_import": st.get("blackfly_import"),
        }
        return {
            "ok": True,
            **st,
            "library": lib,
            "loaded": st.get("loaded"),
            "scraped_db_path": st.get("scraped_db_path"),
            "record_count": st.get("record_count"),
        }

    @app.get("/api/flytying/model")
    def api_flytying_model_get():
        return {"ok": True, **get_model_setting()}

    @app.post("/api/flytying/model")
    async def api_flytying_model_set(request: Request):
        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        model = (body.get("model") or "").strip()
        return {"ok": True, **set_model_setting(model)}

    @app.get("/api/flytying/recipes")
    def api_flytying_recipes(
        q: str = "",
        type: str = "",
        limit: int = 50,
        offset: int = 0,
        min_quality: float = 0,
        favorites_only: bool = False,
        hook_size: int = 0,
    ):
        from jarvis.flytying.search import unified_search

        cache_key = f"{q}|{type}|{limit}|{offset}|{min_quality}|{favorites_only}|{hook_size}"
        from jarvis.cache_state import get_flytying_list_cache, set_flytying_list_cache

        cached = get_flytying_list_cache(cache_key)
        if cached is not None:
            return cached
        if not bridge.gold_available():
            return JSONResponse(
                status_code=503,
                content={"ok": False, "message": "Blackfly scraped database missing", "loaded": False},
            )
        payload = unified_search(
            q,
            fly_type=type or None,
            limit=max(1, min(limit, 200)),
            offset=max(0, offset),
            min_quality=min_quality,
            favorites_only=favorites_only,
            hook_size=hook_size or None,
        )
        result = {"ok": True, **payload}
        set_flytying_list_cache(cache_key, result)
        return result

    @app.get("/api/flytying/health")
    def api_flytying_health():
        from jarvis.flytying.library_health import library_health

        return {"ok": True, **library_health()}

    @app.get("/api/flytying/hatch")
    def api_flytying_hatch(month: int = 0):
        from jarvis.flytying.hatch import hatch_context

        return {"ok": True, **hatch_context(month=month or None)}

    @app.get("/api/flytying/seasonal")
    def api_flytying_seasonal(month: int = 0, limit: int = 8):
        return bridge.seasonal_suggestions(month=month or None, limit=max(1, min(limit, 20)))

    @app.get("/api/flytying/user")
    def api_flytying_user():
        from jarvis.flytying.user_store import user_state

        return {"ok": True, **user_state()}

    @app.post("/api/flytying/materials")
    async def api_flytying_materials_save(request: Request):
        from jarvis.flytying.user_store import replace_inventory_items, replace_materials, save_materials

        body = await request.json()
        raw_items = body.get("items")
        if isinstance(raw_items, list) and bool(body.get("replace")):
            return replace_inventory_items(raw_items)
        raw = body.get("materials") or body.get("materials_text") or ""
        if isinstance(raw, str):
            materials = [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]
        elif isinstance(raw, list):
            materials = [str(m).strip() for m in raw if str(m).strip()]
        else:
            materials = []
        if bool(body.get("replace")):
            return replace_materials(materials)
        return save_materials(materials)

    @app.post("/api/flytying/materials/lookup")
    async def api_flytying_materials_lookup(request: Request):
        from jarvis.flytying.barcode import lookup_barcode

        body = await request.json()
        code = (body.get("barcode") or body.get("code") or "").strip()
        if not code:
            return JSONResponse(status_code=400, content={"ok": False, "message": "barcode required"})
        online = bool(body.get("online", True))
        return {"ok": True, **lookup_barcode(code, online=online)}

    @app.post("/api/flytying/materials/scan")
    async def api_flytying_materials_scan(request: Request):
        from jarvis.flytying.user_store import scan_barcode_into_inventory

        body = await request.json()
        code = (body.get("barcode") or body.get("code") or "").strip()
        if not code:
            return JSONResponse(status_code=400, content={"ok": False, "message": "barcode required"})
        return scan_barcode_into_inventory(
            code,
            name=(body.get("name") or "").strip(),
            brand=(body.get("brand") or "").strip(),
            learn=bool(body.get("learn", True)),
            online_lookup=bool(body.get("online", True)),
        )

    @app.post("/api/flytying/materials/add")
    async def api_flytying_materials_add(request: Request):
        from jarvis.flytying.user_store import add_inventory_item, add_structured_item

        body = await request.json()
        what = (body.get("what") or "").strip()
        if what:
            return add_structured_item(
                what,
                color=(body.get("color") or "").strip(),
                size=(body.get("size") or "").strip(),
                brand=(body.get("brand") or "").strip(),
                notes=(body.get("notes") or "").strip(),
                source=(body.get("source") or "manual").strip(),
                barcode=(body.get("barcode") or "").strip(),
            )
        name = (body.get("name") or "").strip()
        if not name:
            return JSONResponse(status_code=400, content={"ok": False, "message": "what or name required"})
        return add_inventory_item(
            name,
            barcode=(body.get("barcode") or "").strip(),
            source=(body.get("source") or "manual").strip(),
            brand=(body.get("brand") or "").strip(),
            notes=(body.get("notes") or "").strip(),
            qty=body.get("qty"),
        )

    @app.patch("/api/flytying/materials/item/{item_id}")
    async def api_flytying_materials_update(item_id: str, request: Request):
        from jarvis.flytying.user_store import update_inventory_item

        body = await request.json()
        result = update_inventory_item(item_id, body if isinstance(body, dict) else {})
        if not result.get("ok"):
            code = 404 if result.get("message") == "not found" else 400
            return JSONResponse(status_code=code, content=result)
        return result

    @app.delete("/api/flytying/materials/item/{item_id}")
    def api_flytying_materials_remove(item_id: str):
        from jarvis.flytying.user_store import remove_inventory_item

        return remove_inventory_item(item_id)

    @app.get("/api/flytying/materials/barcode-map")
    def api_flytying_barcode_map_list():
        from jarvis.flytying.barcode import list_barcode_mappings

        data = list_barcode_mappings()
        rows = [{"barcode": k, **v} for k, v in sorted(data.items(), key=lambda x: x[0])]
        return {"ok": True, "count": len(rows), "mappings": rows}

    @app.post("/api/flytying/materials/barcode/learn")
    async def api_flytying_barcode_learn(request: Request):
        from jarvis.flytying.barcode import learn_barcode_mapping

        body = await request.json()
        return learn_barcode_mapping(
            (body.get("barcode") or body.get("code") or "").strip(),
            (body.get("name") or "").strip(),
            brand=(body.get("brand") or "").strip(),
            notes=(body.get("notes") or "").strip(),
        )

    @app.delete("/api/flytying/materials/barcode/{barcode}")
    def api_flytying_barcode_delete(barcode: str):
        from jarvis.flytying.barcode import delete_barcode_mapping

        return delete_barcode_mapping(barcode)

    @app.post("/api/flytying/materials/label")
    async def api_flytying_materials_label(request: Request):
        from urllib.parse import quote

        from jarvis.flytying.barcode import make_custom_barcode

        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        name = (body.get("name") or "").strip()
        if not name:
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        code = (body.get("barcode") or "").strip() or make_custom_barcode(name)
        return {
            "ok": True,
            "name": name,
            "barcode": code,
            "label_url": f"/api/flytying/materials/label/{quote(code, safe='')}?name={quote(name)}",
        }

    @app.get("/api/flytying/materials/label/{barcode}")
    def api_flytying_materials_label_html(barcode: str, name: str = ""):
        from html import escape
        from jarvis.flytying.barcode import normalize_barcode

        code = normalize_barcode(barcode)
        label = (name or "").strip() or code
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={code}"
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Label — {escape(label)}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 1.5rem; }}
.label {{ border: 2px solid #333; padding: 1rem; max-width: 14rem; text-align: center; }}
.name {{ font-weight: 700; font-size: 1rem; margin-bottom: 0.5rem; word-break: break-word; }}
.code {{ font-family: monospace; font-size: 0.85rem; margin-top: 0.5rem; }}
@media print {{ body {{ margin: 0; }} .label {{ border: 1px solid #000; }} }}
</style></head><body>
<div class="label">
  <div class="name">{escape(label)}</div>
  <img src="{escape(qr_url)}" width="180" height="180" alt="QR" />
  <div class="code">{escape(code)}</div>
</div>
<p class="muted"><button onclick="window.print()">Print</button></p>
</body></html>"""
        from starlette.responses import HTMLResponse

        return HTMLResponse(html)

    @app.post("/api/flytying/materials/scan-image")
    async def api_flytying_materials_scan_image(request: Request):
        from jarvis.flytying.barcode import decode_barcodes_from_image, pyzbar_status

        form = await request.form()
        upload = form.get("file") or form.get("image")
        if upload is None:
            return JSONResponse(status_code=400, content={"ok": False, "message": "file required"})
        data = await upload.read()
        if not data:
            return JSONResponse(status_code=400, content={"ok": False, "message": "empty file"})
        codes, err = decode_barcodes_from_image(data)
        if not codes:
            hint = err or "No barcode in image — try Camera (Chrome/Edge) or a USB scanner."
            return {
                "ok": True,
                "found": False,
                "barcodes": [],
                "pyzbar": pyzbar_status(),
                "message": hint,
            }
        return {"ok": True, "found": True, "barcodes": codes, "barcode": codes[0], "pyzbar": pyzbar_status()}

    @app.post("/api/flytying/favorites/toggle")
    async def api_flytying_favorite_toggle(request: Request):
        from jarvis.flytying.user_store import toggle_favorite

        body = await request.json()
        return toggle_favorite((body.get("recipe_id") or body.get("id") or "").strip())

    @app.post("/api/flytying/queue/add")
    async def api_flytying_queue_add(request: Request):
        from jarvis.flytying.user_store import add_to_queue

        body = await request.json()
        return add_to_queue(
            (body.get("recipe_id") or body.get("id") or "").strip(),
            name=(body.get("name") or "").strip(),
        )

    @app.post("/api/flytying/queue/remove")
    async def api_flytying_queue_remove(request: Request):
        from jarvis.flytying.user_store import remove_from_queue

        body = await request.json()
        return remove_from_queue((body.get("recipe_id") or body.get("id") or "").strip())

    @app.post("/api/flytying/notes")
    async def api_flytying_notes_save(request: Request):
        from jarvis.flytying.user_store import save_note

        body = await request.json()
        return save_note(
            (body.get("recipe_id") or body.get("id") or "").strip(),
            (body.get("note") or body.get("text") or "").strip(),
        )

    @app.get("/api/flytying/recipes/{name_or_id}/export")
    def api_flytying_recipe_export(name_or_id: str, format: str = "markdown"):
        text = bridge.export_recipe_markdown(name_or_id, fmt=format)
        if not text:
            return JSONResponse(status_code=404, content={"ok": False, "message": "not found"})
        return {"ok": True, "format": format, "content": text}

    @app.get("/api/flytying/recipes/{name_or_id}/similar")
    def api_flytying_recipe_similar(name_or_id: str, limit: int = 6):
        from jarvis.flytying import index as recipe_index

        rows = recipe_index.similar_recipes(name_or_id, limit=max(1, min(limit, 12)))
        return {"ok": True, "count": len(rows), "results": rows}

    @app.post("/api/flytying/compare")
    async def api_flytying_compare(request: Request):
        body = await request.json()
        ids = body.get("recipe_ids") or body.get("ids") or []
        if not isinstance(ids, list) or not ids:
            return JSONResponse(status_code=400, content={"ok": False, "message": "recipe_ids required"})
        return bridge.compare_recipes_by_id([str(i).strip() for i in ids if str(i).strip()])

    @app.get("/api/flytying/videos")
    def api_flytying_videos(q: str = "", limit: int = 80):
        rows = bridge.list_videos(q=q, limit=max(1, min(limit, 200)))
        return {"ok": True, "count": len(rows), "results": rows}

    @app.get("/api/flytying/videos/custom")
    def api_flytying_videos_custom_list():
        from jarvis.flytying.videos_store import list_custom_videos

        rows = list_custom_videos()
        return {"ok": True, "count": len(rows), "results": rows}

    @app.post("/api/flytying/videos/custom")
    async def api_flytying_videos_custom_add(request: Request):
        from jarvis.flytying.videos_store import add_custom_video

        body = await request.json()
        url = (body.get("url") or "").strip()
        title = (body.get("title") or "").strip()
        result = add_custom_video(url, title=title)
        if not result.get("ok"):
            return JSONResponse(status_code=400, content=result)
        return result

    @app.delete("/api/flytying/videos/custom")
    async def api_flytying_videos_custom_delete(request: Request):
        from jarvis.flytying.videos_store import remove_custom_video

        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        key = (body.get("key") or "").strip()
        result = remove_custom_video(key)
        if not result.get("ok"):
            return JSONResponse(status_code=404, content=result)
        return result

    @app.post("/api/flytying/videos/discover")
    async def api_flytying_videos_discover(request: Request):
        from jarvis.flytying.video_fetch import discover_videos_from_url

        body = await request.json()
        url = (body.get("url") or "").strip()
        if not url:
            return JSONResponse(status_code=400, content={"ok": False, "message": "url required"})
        videos = discover_videos_from_url(url)
        return {"ok": True, "count": len(videos), "results": videos}

    @app.get("/api/flytying/nightly/status")
    def api_flytying_nightly_status():
        from jarvis.flytying.nightly import nightly_status

        return {"ok": True, **nightly_status()}

    @app.post("/api/flytying/nightly/run")
    async def api_flytying_nightly_run(request: Request):
        from jarvis.flytying.nightly import run_nightly_flytying_learning

        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        force = bool(body.get("force"))
        memory = getattr(assistant, "memory", None) if assistant else None
        return run_nightly_flytying_learning(memory=memory, force=force)

    @app.get("/api/flytying/images/{name:path}")
    def api_flytying_image(name: str):
        path = bridge.resolve_image_file(name)
        if not path:
            return JSONResponse(status_code=404, content={"ok": False, "message": "not found"})
        media = "image/jpeg"
        suffix = path.suffix.lower()
        if suffix == ".png":
            media = "image/png"
        elif suffix == ".webp":
            media = "image/webp"
        elif suffix == ".gif":
            media = "image/gif"
        return FileResponse(path, media_type=media)

    @app.get("/api/flytying/search")
    def api_flytying_search(q: str = "", type: str = "", limit: int = 8):
        from jarvis.flytying.search import unified_search

        if not bridge.gold_available():
            return JSONResponse(
                status_code=503,
                content={"ok": False, "message": "Blackfly scraped database missing"},
            )
        payload = unified_search(q, fly_type=type or None, limit=max(1, min(limit, 25)))
        return {"ok": True, "query": q, **payload}

    @app.get("/api/flytying/recipes/{name_or_id}")
    def api_flytying_recipe(name_or_id: str):
        row = bridge.get_recipe(name_or_id)
        if not row:
            return JSONResponse(status_code=404, content={"ok": False, "message": "not found"})
        return {"ok": True, **row}

    @app.post("/api/flytying/ask")
    async def api_flytying_ask(request: Request):
        if not bridge.gold_available():
            return JSONResponse(
                status_code=503,
                content={"ok": False, "message": "Blackfly scraped database missing"},
            )
        body = await request.json()
        question = (body.get("question") or body.get("q") or "").strip()
        if not question:
            return JSONResponse(status_code=400, content={"ok": False, "message": "question required"})
        result = bridge.ask_fly_tying(
            question,
            fly_type=(body.get("type") or body.get("fly_type") or None),
            limit=int(body.get("limit") or 4),
        )
        return result

    @app.post("/api/flytying/chat")
    async def api_flytying_chat(request: Request):
        body = await request.json()
        messages = body.get("messages") or []
        if not isinstance(messages, list):
            return JSONResponse(status_code=400, content={"ok": False, "message": "messages must be a list"})
        if not bridge.gold_available():
            return JSONResponse(
                status_code=503,
                content={"ok": False, "message": "Blackfly scraped database missing", "loaded": False},
            )
        fly_type = body.get("type") or body.get("fly_type") or None
        model = (body.get("model") or "").strip()
        use_stream = bool(body.get("stream"))

        if use_stream:
            from jarvis.async_util import stream_sync_iter

            def _produce():
                yield from chat_turn_stream(messages, fly_type=fly_type, model=model)

            async def event_stream():
                async for event in stream_sync_iter(_produce, thread_name="jarvis-flytying-chat"):
                    yield f"data: {json.dumps(event, default=str)}\n\n"

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        result = chat_turn(messages, fly_type=fly_type, model=model)
        if not result.get("ok"):
            return JSONResponse(
                status_code=503 if "unavailable" in str(result.get("message", "")).lower() else 500,
                content=result,
            )
        return result

    @app.post("/api/flytying/from-materials")
    async def api_flytying_from_materials(request: Request):
        body = await request.json()
        raw = body.get("materials") or body.get("materials_text") or ""
        if isinstance(raw, str):
            materials = [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]
        elif isinstance(raw, list):
            materials = [str(m).strip() for m in raw if str(m).strip()]
        else:
            materials = []
        if not materials:
            return JSONResponse(status_code=400, content={"ok": False, "message": "materials required"})
        hits = bridge.suggest_from_materials(materials, limit=int(body.get("limit") or 8))
        from jarvis.flytying.user_store import list_inventory_items, list_materials

        explain = bool(body.get("explain", False))
        chat_result: dict = {"answer": "", "model": "", "recipes": hits}
        if explain:
            question = (
                "I have these tying materials: "
                + ", ".join(materials)
                + ". Which flies from the library fit best, and can you suggest one custom pattern?"
            )
            chat_result = chat_turn(
                [{"role": "user", "content": question}],
                fly_type=(body.get("type") or body.get("fly_type") or None),
                model=(body.get("model") or "").strip(),
            )
        return {
            "ok": True,
            "materials": materials,
            "inventory": list_inventory_items(),
            "materials_count": len(list_materials()),
            "matches": hits,
            "answer": chat_result.get("answer") or "",
            "model": chat_result.get("model"),
            "recipes": chat_result.get("recipes") or hits,
        }

    @app.post("/api/flytying/library/sync")
    async def api_flytying_library_sync(request: Request):
        body = {}
        if request.headers.get("content-type", "").startswith("application/json"):
            body = await request.json()
        result = sync_library(force=bool(body.get("force")))
        if assistant is not None and getattr(assistant, "memory", None):
            seed_memory(assistant.memory)
        return result

    @app.get("/api/flytying/library/status")
    def api_flytying_library_status():
        st = bridge.status()
        return {
            "ok": True,
            **sync_status(),
            "loaded": st.get("loaded"),
            "scraped_db_path": st.get("scraped_db_path"),
            "record_count": st.get("record_count"),
            "blackfly_loaded": st.get("blackfly_loaded"),
            "scraped_path": st.get("scraped_path"),
            "scraped_count": st.get("scraped_count"),
            "gold_path": st.get("gold_path"),
            "gold_count": st.get("gold_count"),
            "recipe_source": st.get("recipe_source"),
            "recipe_count": st.get("recipe_count"),
            "enablement": st.get("blackfly_enablement"),
        }

    @app.post("/api/flytying/gold/build")
    async def api_flytying_gold_build(request: Request):
        if not bridge.available():
            return JSONResponse(
                status_code=503,
                content={"ok": False, "message": "Blackfly unavailable"},
            )
        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        result = bridge.build_gold(
            min_quality=float(body.get("min_quality") or 70),
            build_index=bool(body.get("build_index", True)),
        )
        if result.get("ok"):
            sync_library(force=True)
            if assistant is not None and getattr(assistant, "memory", None):
                seed_memory(assistant.memory)
        return result
