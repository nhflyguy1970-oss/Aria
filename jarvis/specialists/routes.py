"""Specialist Team product API routes."""

from __future__ import annotations


def register_specialist_routes(app, assistant) -> None:
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @app.get("/api/specialists/gallery")
    def specialists_gallery():
        from jarvis.specialists.catalog import list_gallery
        from jarvis.specialists.favorites import frequent_teams, list_favorites, recent_teams

        return {
            "ok": True,
            "gallery": list_gallery(),
            "favorites": list_favorites(),
            "frequent": frequent_teams(),
            "recent": recent_teams(),
        }

    @app.post("/api/specialists/propose")
    async def specialists_propose(request: Request):
        body = await request.json()
        from jarvis.specialists.engine import propose_team

        return propose_team(
            str(body.get("goal") or ""),
            specialists=body.get("specialists") or body.get("team"),
            use_llm=bool(body.get("use_llm")),
        )

    @app.post("/api/specialists/run")
    async def specialists_run(request: Request):
        body = await request.json()
        if not body.get("confirm") and not body.get("dry_propose"):
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "status": "permission_required",
                    "error": "confirm=true required (or use /propose first)",
                },
            )
        from jarvis.specialists.engine import run_team
        from jarvis.specialists.favorites import record_team_usage

        result = run_team(
            assistant,
            str(body.get("goal") or ""),
            specialists=body.get("specialists") or body.get("team"),
            roles=body.get("roles"),
            confirm=bool(body.get("confirm")),
            stop_on_error=bool(body.get("stop_on_error")),
            synthesize_final=bool(body.get("synthesize_final", True)),
            budget=body.get("budget"),
            extras=body.get("extras") if isinstance(body.get("extras"), dict) else {},
            trigger=str(body.get("trigger") or "api"),
            emit_bridges=True,
            parallel_readers=bool(body.get("parallel_readers")),
            critic_loop=bool(body.get("critic_loop")),
            approve_writes=bool(body.get("approve_writes")),
            approve_experimental=bool(body.get("approve_experimental")),
        )
        if result.get("ok") and result.get("team"):
            try:
                record_team_usage(list(result["team"]))
            except Exception:
                pass
        return result

    @app.get("/api/specialists/runs")
    def specialists_runs(limit: int = 40, status: str = "", q: str = ""):
        from jarvis.specialists.history import list_runs

        return {"ok": True, "runs": list_runs(limit=limit, status=status or None, q=q)}

    @app.get("/api/specialists/runs/{run_id}")
    def specialists_run_get(run_id: str):
        from jarvis.specialists.engine import explain_run

        data = explain_run(run_id)
        if not data.get("ok"):
            return JSONResponse(status_code=404, content=data)
        return data

    @app.get("/api/specialists/jobs")
    def specialists_jobs():
        from jarvis.specialists.jobs import list_jobs

        return {"ok": True, "jobs": list_jobs()}

    @app.post("/api/specialists/jobs/{job_id}/cancel")
    def specialists_job_cancel(job_id: str):
        from jarvis.specialists.jobs import request_cancel

        return request_cancel(job_id)

    @app.post("/api/specialists/favorites")
    async def specialists_fav(request: Request):
        body = await request.json()
        from jarvis.specialists.favorites import save_favorite

        return save_favorite(str(body.get("name") or "Team"), list(body.get("team") or []))

    @app.post("/api/specialists/platform-bridge")
    async def specialists_platform_bridge(request: Request):
        body = await request.json()
        from jarvis.specialists.platform_bridge import platform_coordinate_optional

        return platform_coordinate_optional(str(body.get("goal") or ""), agent_ids=body.get("agent_ids"))

    @app.get("/api/specialists/parallel-check")
    def specialists_parallel_check(team: str = ""):
        from jarvis.specialists.parallel import can_parallelize

        ids = [t.strip() for t in team.split(",") if t.strip()]
        return can_parallelize(ids)
