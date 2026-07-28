"""Image Generation HTTP API — presets, enhance preview, params, recovery, status."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def register_routes(app, assistant) -> None:
    @app.get("/api/image-generation/status")
    def ig_status():
        from jarvis.comfyui_settings import get_settings_dict
        from jarvis.image_generation.fallback import recovery_options
        from jarvis.image_generation.mission_bridge import engine_health

        health = engine_health()
        settings = get_settings_dict()
        return {
            "ok": True,
            **health,
            "settings": settings,
            "recovery": recovery_options("" if health.get("running") else "ComfyUI is not running"),
        }

    @app.post("/api/image-generation/generate")
    async def ig_generate(request: Request):
        from jarvis.image_generation.engine import submit_generation

        body = await request.json()
        source = str(body.get("source") or "api")
        return submit_generation(assistant, body, message=str(body.get("prompt") or ""), source=source)

    @app.post("/api/image-generation/enhance-preview")
    async def ig_enhance_preview(request: Request):
        from jarvis.image_generation.enhance import preview_enhance

        body = await request.json()
        enhance = body.get("enhance")
        if enhance is None:
            enhance = True
        return preview_enhance(
            str(body.get("prompt") or ""),
            enhance=bool(enhance),
            negative=str(body.get("negative") or ""),
        )

    @app.get("/api/image-generation/params")
    def ig_params():
        from jarvis.image_generation.params import ASPECT_PRESETS, MAX_VARIATIONS

        return {
            "ok": True,
            "aspect_presets": {k: {"width": v[0], "height": v[1]} for k, v in ASPECT_PRESETS.items()},
            "max_variations": MAX_VARIATIONS,
            "samplers": [
                "euler",
                "euler_ancestral",
                "heun",
                "dpm_2",
                "dpm_2_ancestral",
                "dpmpp_2m",
                "dpmpp_2m_sde",
                "dpmpp_sde",
                "ddim",
            ],
            "schedulers": ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform"],
        }

    @app.get("/api/image-generation/presets")
    def ig_presets(project: str = ""):
        from jarvis.image_generation.presets import list_presets

        return list_presets(project=project)

    @app.post("/api/image-generation/presets")
    async def ig_presets_save(request: Request):
        from jarvis.image_generation.presets import save_preset

        body = await request.json()
        return save_preset(
            str(body.get("title") or "Preset"),
            body.get("fields") or body,
            preset_id=str(body.get("id") or ""),
            project=str(body.get("project") or ""),
        )

    @app.delete("/api/image-generation/presets/{preset_id}")
    def ig_presets_delete(preset_id: str, project: str = ""):
        from jarvis.image_generation.presets import delete_preset

        return delete_preset(preset_id, project=project)

    @app.get("/api/image-generation/presets/export")
    def ig_presets_export():
        from jarvis.image_generation.presets import export_presets

        return export_presets()

    @app.post("/api/image-generation/presets/import")
    async def ig_presets_import(request: Request):
        from jarvis.image_generation.presets import save_preset

        body = await request.json()
        custom = body.get("custom") or {}
        imported = []
        for pid, meta in custom.items():
            out = save_preset(meta.get("title") or pid, meta, preset_id=pid)
            imported.append(out.get("id"))
        return {"ok": True, "imported": imported}

    @app.get("/api/image-generation/last-settings")
    def ig_last_settings():
        from jarvis.image_generation.engine import last_settings_snapshot

        return last_settings_snapshot(assistant)

    @app.post("/api/image-generation/recovery")
    async def ig_recovery(request: Request):
        from jarvis.image_generation.fallback import recovery_options

        body = await request.json()
        return recovery_options(str(body.get("error") or ""), gpu_failure=bool(body.get("gpu_failure")))

    @app.post("/api/image-generation/coach")
    async def ig_coach(request: Request):
        from jarvis.image_generation.experimental import prompt_coach

        body = await request.json()
        return prompt_coach(str(body.get("prompt") or ""))

    @app.post("/api/image-generation/recommend")
    async def ig_recommend(request: Request):
        from jarvis.image_generation.experimental import recommend_style_workflow

        body = await request.json()
        return recommend_style_workflow(str(body.get("prompt") or ""))

    @app.get("/api/image-generation/seed-explorer")
    def ig_seed_explorer(base: int | None = None, count: int = 4):
        from jarvis.image_generation.experimental import seed_explorer

        return seed_explorer(base_seed=base, count=count)

    @app.post("/api/image-generation/evolve")
    async def ig_evolve(request: Request):
        from jarvis.image_generation.experimental import evolve_prompt

        body = await request.json()
        return evolve_prompt(str(body.get("prompt") or ""), direction=str(body.get("direction") or "detail"))
