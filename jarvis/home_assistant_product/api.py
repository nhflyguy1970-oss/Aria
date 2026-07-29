"""Smart Home product HTTP API."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_product_routes(app, assistant) -> None:
    """Register /api/smarthome/product* routes (call after core HA / smarthome routes)."""

    @app.get("/api/smarthome/product")
    def smarthome_product_status():
        from jarvis.home_assistant_product.engine import product_status

        return product_status()

    @app.get("/api/smarthome/product/home")
    def smarthome_product_home():
        from jarvis.home_assistant_product.engine import home_payload

        return home_payload()

    @app.get("/api/smarthome/product/state")
    def smarthome_state_get():
        from jarvis.home_assistant_product.status_bus import get_smarthome_state

        return {"ok": True, **get_smarthome_state()}

    @app.get("/api/smarthome/product/settings")
    def smarthome_settings_get():
        from jarvis.home_assistant_product.settings import load_settings

        return {"ok": True, **load_settings()}

    @app.post("/api/smarthome/product/settings")
    async def smarthome_settings_set(request: Request):
        from jarvis.home_assistant_product.settings import save_settings

        body = await request.json()
        return {"ok": True, **save_settings(body)}

    @app.get("/api/smarthome/product/profiles")
    def smarthome_profiles_list():
        from jarvis.home_assistant_product.profiles import active_profile_id, list_profiles

        return {"ok": True, "profiles": list_profiles(), "active": active_profile_id()}

    @app.post("/api/smarthome/product/profiles")
    async def smarthome_profiles_create(request: Request):
        from jarvis.home_assistant_product.profiles import create_profile

        body = await request.json()
        return {"ok": True, "profile": create_profile(body)}

    @app.post("/api/smarthome/product/profiles/{profile_id}/activate")
    def smarthome_profiles_activate(profile_id: str):
        from jarvis.home_assistant_product.profiles import activate_profile

        try:
            return {"ok": True, "profile": activate_profile(profile_id)}
        except ValueError:
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})

    @app.post("/api/smarthome/product/profiles/{profile_id}/duplicate")
    def smarthome_profiles_dup(profile_id: str):
        from jarvis.home_assistant_product.profiles import duplicate_profile

        profile = duplicate_profile(profile_id)
        if not profile:
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})
        return {"ok": True, "profile": profile}

    @app.delete("/api/smarthome/product/profiles/{profile_id}")
    def smarthome_profiles_delete(profile_id: str):
        from jarvis.home_assistant_product.profiles import delete_profile

        if not delete_profile(profile_id):
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})
        return {"ok": True, "deleted": profile_id}

    @app.get("/api/smarthome/product/profiles/export")
    def smarthome_profiles_export():
        from jarvis.home_assistant_product.profiles import export_profiles

        return {"ok": True, **export_profiles()}

    @app.post("/api/smarthome/product/profiles/import")
    async def smarthome_profiles_import(request: Request):
        from jarvis.home_assistant_product.profiles import import_profiles

        return import_profiles(await request.json())

    @app.get("/api/smarthome/product/history")
    def smarthome_history(limit: int = 50, q: str = "", kind: str = "", reveal: bool = False):
        from jarvis.config import is_uncensored
        from jarvis.home_assistant_product.history import list_history, presentation_for_profile

        censored = not is_uncensored()
        rows = [
            presentation_for_profile(r, censored=censored, reveal=reveal)
            for r in list_history(limit=limit, q=q, kind=kind)
        ]
        return {"ok": True, "history": rows}

    @app.get("/api/smarthome/product/mission")
    def smarthome_mission():
        from jarvis.home_assistant_product.mission_bridge import smarthome_mission_panel

        return {"ok": True, **smarthome_mission_panel()}

    @app.get("/api/smarthome/product/recovery")
    def smarthome_recovery():
        from jarvis.home_assistant_product.engine import recovery_status

        return recovery_status()

    @app.get("/api/smarthome/product/entities/search")
    def smarthome_entities_search(
        q: str = "",
        domain: str = "",
        room: str = "",
        favorites_only: bool = False,
        recent: bool = False,
        limit: int = 40,
    ):
        from jarvis.home_assistant_product.entities import search

        return search(
            q=q,
            domain=domain,
            room=room,
            favorites_only=favorites_only,
            recent=recent,
            limit=limit,
        )

    @app.post("/api/smarthome/product/entities/resolve")
    async def smarthome_entities_resolve(request: Request):
        from jarvis.home_assistant_product.entities import resolve

        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        return resolve(
            str(body.get("q") or body.get("query") or body.get("target") or ""),
            domain=(body.get("domain") or None),
            limit=int(body.get("limit") or 5),
        )

    @app.get("/api/smarthome/product/favorites")
    def smarthome_favorites_list():
        from jarvis.home_assistant_product.favorites import favorites_payload

        return favorites_payload()

    @app.post("/api/smarthome/product/favorites/pin")
    async def smarthome_favorites_pin(request: Request):
        from jarvis.home_assistant_product.favorites import pin

        body = await request.json()
        eid = str(body.get("entity_id") or "").strip()
        if not eid:
            return JSONResponse(status_code=400, content={"ok": False, "message": "entity_id required"})
        try:
            return {"ok": True, "entity_ids": pin(eid)}
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.post("/api/smarthome/product/favorites/unpin")
    async def smarthome_favorites_unpin(request: Request):
        from jarvis.home_assistant_product.favorites import unpin

        body = await request.json()
        eid = str(body.get("entity_id") or "").strip()
        if not eid:
            return JSONResponse(status_code=400, content={"ok": False, "message": "entity_id required"})
        return {"ok": True, "entity_ids": unpin(eid)}

    @app.post("/api/smarthome/product/favorites/reorder")
    async def smarthome_favorites_reorder(request: Request):
        from jarvis.home_assistant_product.favorites import reorder

        body = await request.json()
        ids = body.get("entity_ids") or body.get("order") or []
        if not isinstance(ids, list):
            return JSONResponse(status_code=400, content={"ok": False, "message": "entity_ids list required"})
        return {"ok": True, "entity_ids": reorder(ids)}

    @app.get("/api/smarthome/product/rooms")
    def smarthome_rooms_list():
        from jarvis.home_assistant_product.rooms import list_rooms

        return {"ok": True, "rooms": list_rooms()}

    @app.post("/api/smarthome/product/rooms")
    async def smarthome_rooms_upsert(request: Request):
        from jarvis.home_assistant_product.rooms import upsert_room

        body = await request.json()
        try:
            return {"ok": True, "room": upsert_room(body)}
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.delete("/api/smarthome/product/rooms/{room_id}")
    def smarthome_rooms_delete(room_id: str):
        from jarvis.home_assistant_product.rooms import delete_room

        if not delete_room(room_id):
            return JSONResponse(status_code=404, content={"ok": False, "message": "room_not_found"})
        return {"ok": True, "deleted": room_id}

    @app.post("/api/smarthome/product/control")
    async def smarthome_control(request: Request):
        from jarvis.home_assistant_product.engine import control_device

        body = await request.json()
        target = str(body.get("target") or body.get("entity_id") or "").strip()
        if not target:
            return JSONResponse(status_code=400, content={"ok": False, "message": "target required"})
        return control_device(
            target,
            str(body.get("action") or "toggle"),
            brightness=body.get("brightness") if body.get("brightness") is not None else body.get("brightness_pct"),
            color_name=body.get("color_name") or body.get("color"),
            rgb=body.get("rgb"),
            hs=body.get("hs"),
            color_temp_kelvin=body.get("color_temp_kelvin"),
            transition=body.get("transition"),
            source=str(body.get("source") or "api"),
        )

    @app.post("/api/smarthome/product/scene")
    async def smarthome_scene(request: Request):
        from jarvis.home_assistant_product.engine import activate_scene

        body = await request.json()
        scene = str(body.get("scene") or body.get("entity_id") or body.get("preset") or "").strip()
        if not scene:
            return JSONResponse(status_code=400, content={"ok": False, "message": "scene required"})
        return activate_scene(scene, source=str(body.get("source") or "api"))

    @app.get("/api/smarthome/product/house-status")
    def smarthome_house_status(limit: int = 10):
        from jarvis.home_assistant_product.engine import house_status

        return house_status(limit=limit)

    @app.post("/api/smarthome/product/vision/camera")
    async def smarthome_vision_camera(request: Request):
        from jarvis.home_assistant_product.vision_bridge import analyze_camera

        body = await request.json()
        return analyze_camera(
            path=str(body.get("path") or ""),
            entity_id=str(body.get("entity_id") or body.get("camera") or ""),
            question=str(body.get("question") or ""),
            confirmed=bool(body.get("confirmed")),
            assistant=assistant,
            force=bool(body.get("force", True)),
        )

    @app.post("/api/smarthome/product/voice/home")
    async def smarthome_voice_home(request: Request):
        from jarvis.home_assistant_product.voice_bridge import home_command

        body = await request.json()
        command = str(body.get("command") or body.get("action") or "").strip()
        if not command:
            return JSONResponse(status_code=400, content={"ok": False, "message": "command required"})
        return home_command(
            command,
            target=str(body.get("target") or body.get("entity_id") or ""),
            scene=str(body.get("scene") or ""),
            brightness=body.get("brightness"),
            color_name=body.get("color_name") or body.get("color"),
            assistant=assistant,
            speak=body.get("speak", True) is not False,
        )

    @app.get("/api/smarthome/product/planner/candidates")
    def smarthome_planner_candidates(kind: str = "home_tasks", scene: str = ""):
        from jarvis.home_assistant_product.planner_bridge import planner_candidates

        return planner_candidates(kind=kind, scene=scene)

    @app.get("/api/smarthome/product/calendar/candidates")
    def smarthome_calendar_candidates(kind: str = "ha_mode", scene: str = "", days: int = 1):
        from jarvis.home_assistant_product.calendar_bridge import calendar_candidates

        return calendar_candidates(kind=kind, scene=scene, days=days)

    @app.get("/api/smarthome/product/automation/candidates")
    def smarthome_automation_candidates(kind: str = "webhook_scene", scene: str = "", entity_id: str = ""):
        from jarvis.home_assistant_product.automation_bridge import automation_candidates

        return automation_candidates(kind=kind, scene=scene, entity_id=entity_id)

    @app.get("/api/smarthome/product/cheatsheet")
    def smarthome_cheatsheet():
        from jarvis.home_assistant_product.cheatsheet import cheatsheet_payload

        return cheatsheet_payload()

    @app.get("/api/smarthome/product/experimental")
    def smarthome_experimental():
        from jarvis.home_assistant_product.experimental import experimental_status

        return experimental_status()

    @app.post("/api/smarthome/product/experimental/kg")
    async def smarthome_exp_kg(request: Request):
        from jarvis.home_assistant_product.experimental import link_knowledge_graph

        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        return link_knowledge_graph(
            entity_id=str(body.get("entity_id") or ""),
            room=str(body.get("room") or ""),
            summary=str(body.get("summary") or ""),
        )


def register_routes(app, assistant) -> None:
    register_product_routes(app, assistant)
