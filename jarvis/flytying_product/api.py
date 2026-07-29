"""Fly Tying product HTTP API."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse, Response


def register_product_routes(app, assistant) -> None:
    """Register /api/flytying/product* routes (call after core flytying extension routes)."""

    @app.get("/api/flytying/product")
    def flytying_product_status():
        from jarvis.flytying_product.engine import product_status

        return product_status()

    @app.get("/api/flytying/product/home")
    def flytying_product_home():
        from jarvis.flytying_product.engine import home_payload

        return home_payload()

    @app.get("/api/flytying/product/state")
    def flytying_state_get():
        from jarvis.flytying_product.status_bus import get_flytying_state

        return {"ok": True, **get_flytying_state()}

    @app.get("/api/flytying/product/settings")
    def flytying_settings_get():
        from jarvis.flytying_product.settings import load_settings

        return {"ok": True, **load_settings()}

    @app.post("/api/flytying/product/settings")
    async def flytying_settings_set(request: Request):
        from jarvis.flytying_product.settings import save_settings

        body = await request.json()
        return {"ok": True, **save_settings(body)}

    @app.get("/api/flytying/product/profiles")
    def flytying_profiles_list():
        from jarvis.flytying_product.profiles import active_profile_id, list_profiles

        return {"ok": True, "profiles": list_profiles(), "active": active_profile_id()}

    @app.post("/api/flytying/product/profiles")
    async def flytying_profiles_create(request: Request):
        from jarvis.flytying_product.profiles import create_profile

        body = await request.json()
        return {"ok": True, "profile": create_profile(body)}

    @app.post("/api/flytying/product/profiles/{profile_id}/activate")
    def flytying_profiles_activate(profile_id: str):
        from jarvis.flytying_product.profiles import activate_profile

        try:
            return {"ok": True, "profile": activate_profile(profile_id)}
        except ValueError:
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})

    @app.post("/api/flytying/product/profiles/{profile_id}/duplicate")
    def flytying_profiles_dup(profile_id: str):
        from jarvis.flytying_product.profiles import duplicate_profile

        profile = duplicate_profile(profile_id)
        if not profile:
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})
        return {"ok": True, "profile": profile}

    @app.delete("/api/flytying/product/profiles/{profile_id}")
    def flytying_profiles_delete(profile_id: str):
        from jarvis.flytying_product.profiles import delete_profile

        if not delete_profile(profile_id):
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})
        return {"ok": True, "deleted": profile_id}

    @app.get("/api/flytying/product/profiles/export")
    def flytying_profiles_export():
        from jarvis.flytying_product.profiles import export_profiles

        return {"ok": True, **export_profiles()}

    @app.post("/api/flytying/product/profiles/import")
    async def flytying_profiles_import(request: Request):
        from jarvis.flytying_product.profiles import import_profiles

        return import_profiles(await request.json())

    @app.get("/api/flytying/product/sessions")
    def flytying_sessions_list(limit: int = 50):
        from jarvis.flytying_product.sessions import active_session, list_sessions

        return {"ok": True, "sessions": list_sessions(limit=limit), "active": active_session()}

    @app.get("/api/flytying/product/sessions/active")
    def flytying_sessions_active():
        from jarvis.flytying_product.sessions import active_session

        session = active_session()
        return {"ok": True, "session": session}

    @app.post("/api/flytying/product/sessions/start")
    async def flytying_sessions_start(request: Request):
        from jarvis.flytying_product.sessions import start_session

        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        return {
            "ok": True,
            "session": start_session(
                recipe_id=str(body.get("recipe_id") or ""),
                recipe_name=str(body.get("recipe_name") or ""),
                notes=str(body.get("notes") or ""),
                materials_checklist=body.get("materials_checklist"),
            ),
        }

    @app.post("/api/flytying/product/sessions/{session_id}/pause")
    def flytying_sessions_pause(session_id: str):
        from jarvis.flytying_product.sessions import pause_session

        try:
            return {"ok": True, "session": pause_session(session_id)}
        except ValueError:
            return JSONResponse(status_code=404, content={"ok": False, "message": "session_not_found"})

    @app.post("/api/flytying/product/sessions/{session_id}/resume")
    def flytying_sessions_resume(session_id: str):
        from jarvis.flytying_product.sessions import resume_session

        try:
            return {"ok": True, "session": resume_session(session_id)}
        except ValueError:
            return JSONResponse(status_code=404, content={"ok": False, "message": "session_not_found"})

    @app.post("/api/flytying/product/sessions/{session_id}/next")
    def flytying_sessions_next(session_id: str):
        from jarvis.flytying_product.sessions import next_step

        try:
            return {"ok": True, "session": next_step(session_id)}
        except ValueError:
            return JSONResponse(status_code=404, content={"ok": False, "message": "session_not_found"})

    @app.post("/api/flytying/product/sessions/{session_id}/prev")
    def flytying_sessions_prev(session_id: str):
        from jarvis.flytying_product.sessions import prev_step

        try:
            return {"ok": True, "session": prev_step(session_id)}
        except ValueError:
            return JSONResponse(status_code=404, content={"ok": False, "message": "session_not_found"})

    @app.post("/api/flytying/product/sessions/{session_id}/complete")
    def flytying_sessions_complete(session_id: str):
        from jarvis.flytying_product.sessions import complete_session

        try:
            return {"ok": True, "session": complete_session(session_id)}
        except ValueError:
            return JSONResponse(status_code=404, content={"ok": False, "message": "session_not_found"})

    @app.patch("/api/flytying/product/sessions/{session_id}")
    async def flytying_sessions_update(session_id: str, request: Request):
        from jarvis.flytying_product.sessions import update_session

        body = await request.json()
        try:
            return {"ok": True, "session": update_session(session_id, body)}
        except ValueError:
            return JSONResponse(status_code=404, content={"ok": False, "message": "session_not_found"})

    @app.get("/api/flytying/product/history")
    def flytying_history(limit: int = 50, q: str = "", kind: str = "", reveal: bool = False):
        from jarvis.config import is_uncensored
        from jarvis.flytying_product.history import list_history, presentation_for_profile

        censored = not is_uncensored()
        rows = [
            presentation_for_profile(r, censored=censored, reveal=reveal)
            for r in list_history(limit=limit, q=q, kind=kind)
        ]
        return {"ok": True, "history": rows}

    @app.get("/api/flytying/product/mission")
    def flytying_mission():
        from jarvis.flytying_product.mission_bridge import flytying_mission_panel

        return {"ok": True, **flytying_mission_panel()}

    @app.get("/api/flytying/product/recovery")
    def flytying_recovery():
        from jarvis.flytying_product.engine import recovery_status

        return recovery_status()

    @app.get("/api/flytying/product/inventory")
    def flytying_inventory():
        from jarvis.flytying_product.inventory import inventory_summary

        return inventory_summary()

    @app.post("/api/flytying/product/suggest")
    async def flytying_suggest(request: Request):
        from jarvis.flytying_product.engine import suggest_from_materials

        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        raw = body.get("materials") or body.get("materials_text") or []
        if isinstance(raw, str):
            materials = [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]
        elif isinstance(raw, list):
            materials = [str(m).strip() for m in raw if str(m).strip()]
        else:
            materials = []
        return suggest_from_materials(materials or None, limit=int(body.get("limit") or 8), source="api")

    @app.post("/api/flytying/product/vision/identify-material")
    async def flytying_vision_material(request: Request):
        from jarvis.flytying_product.vision_bridge import identify_material

        body = await request.json()
        path = (body.get("path") or "").strip()
        if not path:
            return JSONResponse(status_code=400, content={"ok": False, "message": "path required"})
        return identify_material(
            path,
            assistant=assistant,
            question=str(body.get("question") or ""),
            force=bool(body.get("force", True)),
        )

    @app.post("/api/flytying/product/vision/identify-fly")
    async def flytying_vision_fly(request: Request):
        from jarvis.flytying_product.vision_bridge import identify_finished_fly

        body = await request.json()
        path = (body.get("path") or "").strip()
        if not path:
            return JSONResponse(status_code=400, content={"ok": False, "message": "path required"})
        return identify_finished_fly(
            path,
            assistant=assistant,
            question=str(body.get("question") or ""),
            force=bool(body.get("force", True)),
            suggest_limit=int(body.get("limit") or 6),
        )

    @app.post("/api/flytying/product/vision/confirm-inventory")
    async def flytying_vision_confirm(request: Request):
        from jarvis.flytying_product.vision_bridge import confirm_inventory_draft

        body = await request.json()
        return confirm_inventory_draft(body.get("draft") or body, confirmed=bool(body.get("confirmed")))

    @app.post("/api/flytying/product/voice/bench")
    async def flytying_voice_bench(request: Request):
        from jarvis.flytying_product.voice_bridge import bench_command

        body = await request.json()
        command = str(body.get("command") or body.get("action") or "").strip()
        if not command:
            return JSONResponse(status_code=400, content={"ok": False, "message": "command required"})
        return bench_command(
            command,
            session_id=str(body.get("session_id") or ""),
            assistant=assistant,
            speak=body.get("speak", True) is not False,
        )

    @app.get("/api/flytying/product/hatch/packs")
    def flytying_hatch_packs():
        from jarvis.flytying_product.hatch_packs import list_packs

        return {"ok": True, "packs": list_packs()}

    @app.get("/api/flytying/product/hatch/packs/{pack_id}")
    def flytying_hatch_pack_get(pack_id: str):
        from jarvis.flytying_product.hatch_packs import load_pack

        pack = load_pack(pack_id)
        if not pack:
            return JSONResponse(status_code=404, content={"ok": False, "message": "pack_not_found"})
        return {"ok": True, "pack": pack}

    @app.post("/api/flytying/product/hatch/packs/import")
    async def flytying_hatch_pack_import(request: Request):
        from jarvis.flytying_product.hatch_packs import import_pack

        body = await request.json()
        return import_pack(body.get("pack") or body, path=str(body.get("path") or ""))

    @app.post("/api/flytying/product/hatch/packs/{pack_id}/activate")
    def flytying_hatch_pack_activate(pack_id: str):
        from jarvis.flytying_product.hatch_packs import activate_pack

        result = activate_pack(pack_id)
        if not result.get("ok"):
            return JSONResponse(status_code=404, content=result)
        return result

    @app.get("/api/flytying/product/hatch/packs/{pack_id}/export")
    def flytying_hatch_pack_export(pack_id: str):
        from jarvis.flytying_product.hatch_packs import export_pack

        result = export_pack(pack_id)
        if not result.get("ok"):
            return JSONResponse(status_code=404, content=result)
        return result

    @app.post("/api/flytying/product/gallery/link")
    async def flytying_gallery_link(request: Request):
        from jarvis.flytying_product.gallery_bridge import link_finished_fly

        body = await request.json()
        name = str(body.get("name") or body.get("filename") or "").strip()
        if not name:
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        return link_finished_fly(
            name,
            recipe_id=str(body.get("recipe_id") or ""),
            recipe_name=str(body.get("recipe_name") or ""),
            session_id=str(body.get("session_id") or ""),
            notes=str(body.get("notes") or ""),
            collection=str(body.get("collection") or "Finished flies"),
        )

    @app.get("/api/flytying/product/gallery/finished")
    def flytying_gallery_finished(limit: int = 40):
        from jarvis.flytying_product.gallery_bridge import list_finished_fly_links

        return list_finished_fly_links(limit=limit)

    @app.get("/api/flytying/product/cheatsheet")
    def flytying_cheatsheet():
        from jarvis.flytying_product.cheatsheet import cheatsheet_payload

        return cheatsheet_payload()

    @app.get("/api/flytying/product/experimental")
    def flytying_experimental():
        from jarvis.flytying_product.experimental import experimental_status

        return experimental_status()

    @app.post("/api/flytying/product/qr/local")
    async def flytying_qr_local(request: Request):
        from jarvis.flytying_product.qr_local import generate_qr

        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        data = str(body.get("data") or body.get("barcode") or body.get("text") or "").strip()
        result = generate_qr(
            data,
            fmt=str(body.get("format") or body.get("fmt") or "svg"),
            size=int(body.get("size") or 180),
            border=int(body.get("border") or 2),
        )
        if body.get("raw_svg") and result.get("svg"):
            return Response(content=result["svg"], media_type="image/svg+xml")
        return result

    @app.get("/api/flytying/product/planner/candidates")
    def flytying_planner_candidates(kind: str = "tie_this_week", month: int = 0):
        from jarvis.flytying_product.planner_bridge import planner_candidates

        return planner_candidates(kind=kind, month=month or None)

    @app.get("/api/flytying/product/calendar/candidates")
    def flytying_calendar_candidates(kind: str = "hatch_weeks", month: int = 0, session_id: str = ""):
        from jarvis.flytying_product.calendar_bridge import calendar_candidates

        return calendar_candidates(kind=kind, month=month or None, session_id=session_id)


# Alias matching vision_product.api.register_routes naming
def register_routes(app, assistant) -> None:
    register_product_routes(app, assistant)
