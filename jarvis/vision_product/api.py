"""Vision product HTTP API."""

from __future__ import annotations

from fastapi import File, Form, Request, UploadFile
from fastapi.responses import JSONResponse


def register_routes(app, assistant) -> None:
    @app.get("/api/vision/product")
    def vision_product_status():
        from jarvis.vision_product.engine import product_status

        return product_status()

    @app.get("/api/vision/state")
    def vision_state_get():
        from jarvis.vision_product.status_bus import get_vision_state

        return {"ok": True, **get_vision_state()}

    @app.get("/api/vision/honesty")
    def vision_honesty(task: str = "describe"):
        from jarvis.vision_product.honesty import honesty_report

        return honesty_report(task=task)

    @app.get("/api/vision/actions")
    def vision_actions():
        from jarvis.vision_product.engine import action_rail

        return {"ok": True, "actions": action_rail()}

    @app.post("/api/vision/analyze")
    async def vision_analyze(request: Request):
        from jarvis.vision_product.engine import analyze

        body = await request.json()
        return analyze(
            path=body.get("path"),
            path2=body.get("path2"),
            action=str(body.get("action") or "describe"),
            question=str(body.get("question") or body.get("prompt") or ""),
            crop=body.get("crop"),
            source=str(body.get("source") or "api"),
            assistant=assistant,
            import_target=str(body.get("import_target") or ""),
            speak=bool(body.get("speak")),
            force=bool(body.get("force")),
        )

    @app.post("/api/vision/ocr")
    async def vision_ocr(request: Request):
        from jarvis.vision_product.engine import analyze

        body = await request.json()
        action = "ocr_structured" if body.get("structured") else "ocr"
        return analyze(
            path=body.get("path"),
            action=action,
            source=str(body.get("source") or "api"),
            assistant=assistant,
            force=True,
        )

    @app.post("/api/vision/import")
    async def vision_import_route(request: Request):
        from jarvis.vision_product.import_pipeline import vision_import

        body = await request.json()
        return vision_import(
            path=body.get("path"),
            ocr_text=str(body.get("ocr_text") or ""),
            target=str(body.get("target") or "preview"),
            section=str(body.get("section") or "daily"),
            source=str(body.get("source") or "api"),
            assistant=assistant,
            structured=bool(body.get("structured")),
        )

    @app.post("/api/vision/import/apply")
    async def vision_import_apply(request: Request):
        from jarvis.vision_product.import_pipeline import apply_import

        body = await request.json()
        return apply_import(body.get("preview") or body, confirmed=bool(body.get("confirmed")))

    @app.get("/api/vision/settings/unified")
    def vision_settings_unified_get():
        from jarvis.vision_product.settings import load_settings

        return {"ok": True, **load_settings()}

    @app.post("/api/vision/settings/unified")
    async def vision_settings_unified_set(request: Request):
        from jarvis.vision_product.settings import save_settings

        body = await request.json()
        return {"ok": True, **save_settings(body)}

    @app.get("/api/vision/profiles")
    def vision_profiles_list():
        from jarvis.vision_product.profiles import active_profile_id, list_profiles

        return {"ok": True, "profiles": list_profiles(), "active": active_profile_id()}

    @app.post("/api/vision/profiles")
    async def vision_profiles_create(request: Request):
        from jarvis.vision_product.profiles import create_profile

        body = await request.json()
        return {"ok": True, "profile": create_profile(body)}

    @app.post("/api/vision/profiles/{profile_id}/activate")
    def vision_profiles_activate(profile_id: str):
        from jarvis.vision_product.profiles import activate_profile

        try:
            return {"ok": True, "profile": activate_profile(profile_id)}
        except ValueError:
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})

    @app.post("/api/vision/profiles/{profile_id}/duplicate")
    def vision_profiles_dup(profile_id: str):
        from jarvis.vision_product.profiles import duplicate_profile

        profile = duplicate_profile(profile_id)
        if not profile:
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})
        return {"ok": True, "profile": profile}

    @app.delete("/api/vision/profiles/{profile_id}")
    def vision_profiles_delete(profile_id: str):
        from jarvis.vision_product.profiles import delete_profile

        if not delete_profile(profile_id):
            return JSONResponse(status_code=404, content={"ok": False, "message": "profile_not_found"})
        return {"ok": True, "deleted": profile_id}

    @app.get("/api/vision/profiles/export")
    def vision_profiles_export():
        from jarvis.vision_product.profiles import export_profiles

        return {"ok": True, **export_profiles()}

    @app.post("/api/vision/profiles/import")
    async def vision_profiles_import(request: Request):
        from jarvis.vision_product.profiles import import_profiles

        return import_profiles(await request.json())

    @app.get("/api/vision/history")
    def vision_history(limit: int = 50, q: str = "", reveal: bool = False):
        from jarvis.config import is_uncensored
        from jarvis.vision_product.history import list_history, presentation_for_profile

        censored = not is_uncensored()
        rows = [
            presentation_for_profile(r, censored=censored, reveal=reveal)
            for r in list_history(limit=limit, q=q)
        ]
        return {"ok": True, "history": rows}

    @app.post("/api/vision/batch")
    async def vision_batch(request: Request):
        from jarvis.vision_product.batch import start_batch

        body = await request.json()
        return start_batch(
            list(body.get("paths") or []),
            action=str(body.get("action") or "describe"),
            source=str(body.get("source") or "api"),
            assistant=assistant,
        )

    @app.get("/api/vision/batch")
    def vision_batch_list():
        from jarvis.vision_product.batch import list_jobs

        return {"ok": True, "jobs": list_jobs()}

    @app.post("/api/vision/batch/{job_id}/cancel")
    def vision_batch_cancel(job_id: str):
        from jarvis.vision_product.batch import cancel_job

        return cancel_job(job_id)

    @app.post("/api/vision/batch/{job_id}/retry")
    def vision_batch_retry(job_id: str):
        from jarvis.vision_product.batch import retry_job

        return retry_job(job_id, assistant=assistant)

    @app.get("/api/vision/mission")
    def vision_mission():
        from jarvis.vision_product.mission_bridge import vision_mission_panel

        return {"ok": True, **vision_mission_panel()}

    @app.get("/api/vision/experimental")
    def vision_experimental():
        from jarvis.vision_product.experimental import experimental_status

        return experimental_status()

    @app.get("/api/vision/experimental/timeline")
    def vision_exp_timeline():
        from jarvis.vision_product.experimental import scene_timeline

        return scene_timeline()

    @app.get("/api/vision/experimental/clusters")
    def vision_exp_clusters():
        from jarvis.vision_product.experimental import cluster_visual_memory

        return cluster_visual_memory()

    @app.post("/api/vision/experimental/temporal-compare")
    async def vision_exp_temporal(request: Request):
        from jarvis.vision_product.experimental import temporal_compare

        body = await request.json()
        return temporal_compare(str(body.get("path") or ""), str(body.get("path2") or ""), assistant=assistant)

    @app.post("/api/vision/upload-analyze")
    async def vision_upload_analyze(
        file: UploadFile = File(...),
        action: str = Form("describe"),
        question: str = Form(""),
    ):
        from jarvis.config import DATA_DIR
        from jarvis.vision_product.engine import analyze

        upload_dir = DATA_DIR / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / (file.filename or "vision.jpg")
        dest.write_bytes(await file.read())
        return analyze(
            path=str(dest),
            action=action,
            question=question,
            source="upload",
            assistant=assistant,
            force=True,
        )
