"""Video Generation HTTP API — generate, storyboard, presets, enhance, recovery."""

from __future__ import annotations

from fastapi import Request


def register_routes(app, assistant) -> None:
    @app.get("/api/video-generation/status")
    def vg_status():
        from jarvis.video_generation.fallback import recovery_options
        from jarvis.video_generation.mission_bridge import engine_health

        health = engine_health()
        return {
            "ok": True,
            **health,
            "recovery": recovery_options("" if health.get("running") else "ComfyUI is not running"),
        }

    @app.post("/api/video-generation/generate")
    async def vg_generate(request: Request):
        from jarvis.video_generation.engine import submit_video

        body = await request.json()
        source = str(body.get("source") or "api")
        return submit_video(assistant, body, message=str(body.get("prompt") or ""), source=source)

    @app.post("/api/video-generation/storyboard")
    async def vg_storyboard(request: Request):
        from jarvis.video_generation.engine import submit_storyboard

        body = await request.json()
        return submit_storyboard(assistant, body, source=str(body.get("source") or "studio"))

    @app.post("/api/video-generation/enhance-preview")
    async def vg_enhance_preview(request: Request):
        from jarvis.video_generation.enhance import preview_enhance

        body = await request.json()
        enhance = body.get("enhance")
        if enhance is None:
            enhance = True
        return preview_enhance(
            str(body.get("prompt") or ""),
            enhance=bool(enhance),
            negative=str(body.get("negative") or ""),
        )

    @app.get("/api/video-generation/presets")
    def vg_presets(project: str = ""):
        from jarvis.video_generation.presets import list_presets

        return list_presets(project=project)

    @app.post("/api/video-generation/presets")
    async def vg_presets_save(request: Request):
        from jarvis.video_generation.presets import save_preset

        body = await request.json()
        return save_preset(
            str(body.get("title") or "Preset"),
            body.get("fields") or body,
            preset_id=str(body.get("id") or ""),
            project=str(body.get("project") or ""),
        )

    @app.delete("/api/video-generation/presets/{preset_id}")
    def vg_presets_delete(preset_id: str, project: str = ""):
        from jarvis.video_generation.presets import delete_preset

        return delete_preset(preset_id, project=project)

    @app.get("/api/video-generation/presets/export")
    def vg_presets_export():
        from jarvis.video_generation.presets import export_presets

        return export_presets()

    @app.post("/api/video-generation/presets/import")
    async def vg_presets_import(request: Request):
        from jarvis.video_generation.presets import save_preset

        body = await request.json()
        custom = body.get("custom") or {}
        imported = []
        for pid, meta in custom.items():
            out = save_preset(meta.get("title") or pid, meta, preset_id=pid)
            imported.append(out.get("id"))
        return {"ok": True, "imported": imported}

    @app.get("/api/video-generation/last-settings")
    def vg_last_settings():
        from jarvis.video_generation.engine import last_settings_snapshot

        return last_settings_snapshot(assistant)

    @app.post("/api/video-generation/recovery")
    async def vg_recovery(request: Request):
        from jarvis.video_generation.fallback import recovery_options

        body = await request.json()
        return recovery_options(str(body.get("error") or ""), gpu_failure=bool(body.get("gpu_failure")))

    @app.post("/api/video-generation/coach")
    async def vg_coach(request: Request):
        from jarvis.video_generation.experimental import prompt_coach

        body = await request.json()
        return prompt_coach(str(body.get("prompt") or ""))

    @app.post("/api/video-generation/recommend")
    async def vg_recommend(request: Request):
        from jarvis.video_generation.experimental import recommend_motion

        body = await request.json()
        return recommend_motion(str(body.get("prompt") or ""))

    @app.post("/api/video-generation/shot-plan")
    async def vg_shot_plan(request: Request):
        from jarvis.video_generation.experimental import shot_planner

        body = await request.json()
        return shot_planner(str(body.get("prompt") or ""), max_shots=int(body.get("max_shots") or 4))

    @app.get("/api/video-generation/seed-explorer")
    def vg_seed_explorer(base: int | None = None, count: int = 4):
        from jarvis.video_generation.experimental import seed_explorer

        return seed_explorer(base_seed=base, count=count)

    @app.get("/api/video-generation/camera")
    def vg_camera():
        from jarvis.video_generation.experimental import camera_explorer

        return camera_explorer()

    @app.get("/api/video-generation/meta/{name}")
    def vg_meta(name: str):
        from jarvis.video_generation.metadata import apply_visibility, get_meta, is_restricted_for_viewer

        if is_restricted_for_viewer(name):
            return {"ok": True, "restricted": True, "meta": {"uncensored": True}}
        return {"ok": True, "meta": apply_visibility({"name": name, **get_meta(name)})}
