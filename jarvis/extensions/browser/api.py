"""Browser agent API."""

from __future__ import annotations

from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse


def register_routes(app, assistant) -> None:
    @app.get("/api/browser/status")
    def browser_status():
        try:
            from jarvis.browser_agent import status

            return {"ok": True, **status()}
        except Exception as exc:
            return {"ok": False, "status": "error", "message": str(exc)}

    @app.post("/api/browser/navigate")
    async def browser_navigate(request: Request):
        from jarvis.browser_agent import navigate

        body = await request.json()
        url = str(body.get("url") or "").strip()
        if not url:
            return JSONResponse(status_code=400, content={"ok": False, "message": "url required"})
        result = navigate(url, allow_risky=bool(body.get("allow_risky")))
        return {"ok": True, **result} if result.get("ok") else result

    @app.post("/api/browser/run")
    @app.post("/api/browser/run-task")
    async def browser_run(request: Request):
        body = await request.json()
        url = str(body.get("url") or "").strip()
        task = str(body.get("task") or body.get("goal") or "").strip()
        if not task:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": "task or goal required"},
            )
        try:
            from jarvis.p2_flags import browser_agent_enabled

            if not browser_agent_enabled():
                return {"ok": False, "message": "Browser agent disabled (set JARVIS_BROWSER_AGENT=1)"}
            from jarvis.browser_agent import navigate, run_agent_task

            if url:
                nav = navigate(url, allow_risky=bool(body.get("allow_risky")))
                if not nav.get("ok"):
                    return nav
            result = run_agent_task(
                task,
                mode=body.get("mode") or "auto",
                max_steps=int(body.get("max_steps") or 10),
                assistant=assistant,
            )
            return {"ok": True, "message": result.get("message") or result.get("summary") or "Done", **result}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    @app.post("/api/browser/pause")
    def browser_pause():
        try:
            from jarvis.browser_agent import pause

            return {"ok": True, **pause()}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    @app.post("/api/browser/resume")
    def browser_resume():
        try:
            from jarvis.browser_agent import resume

            return {"ok": True, **resume()}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    @app.post("/api/browser/takeover")
    def browser_takeover():
        try:
            from jarvis.browser_agent import takeover

            return {"ok": True, **takeover()}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    @app.post("/api/browser/stop")
    def browser_stop():
        try:
            from jarvis.browser_agent import stop

            return {"ok": True, **stop()}
        except Exception as exc:
            return {"ok": False, "message": str(exc)}

    @app.post("/api/browser/install-playwright")
    def browser_install_playwright():
        """Bootstrap Playwright + Chromium for the Browser panel Install button."""
        try:
            from jarvis.browser_playwright import ensure_playwright

            stack = ensure_playwright(install=True)
            ok = bool(stack.get("playwright") and stack.get("chromium"))
            return {
                "ok": ok,
                **stack,
                "hint": None
                if ok
                else "Install failed — try: pip install playwright && playwright install chromium",
            }
        except Exception as exc:
            return {
                "ok": False,
                "playwright": False,
                "chromium": False,
                "hint": str(exc),
            }

    @app.get("/api/browser/screenshot/latest")
    def browser_screenshot_latest():
        from jarvis.browser_agent import status

        st = status()
        path = st.get("last_screenshot") or ""
        if not path:
            return {"ok": False, "message": "No screenshot yet"}
        p = Path(path)
        if not p.is_file():
            return {"ok": False, "message": "Screenshot file missing"}
        return {"ok": True, "path": path, "url": "/api/browser/screenshot/image"}

    @app.get("/api/browser/screenshot/image")
    def browser_screenshot_image():
        from jarvis.browser_agent import status

        st = status()
        path = st.get("last_screenshot") or ""
        p = Path(path)
        if not p.is_file():
            return JSONResponse(status_code=404, content={"ok": False, "message": "No screenshot"})
        return FileResponse(path)

    @app.post("/api/browser/screenshot")
    def browser_screenshot_capture():
        from jarvis.browser_agent import status

        st = status()
        if st.get("last_screenshot"):
            return {"ok": True, "path": st["last_screenshot"]}
        return {"ok": False, "message": "No screenshot available (Playwright capture not active)"}
