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

    @app.get("/api/browser/home")
    def browser_home():
        from jarvis.browser_product.home import browser_home_snapshot

        return browser_home_snapshot(assistant)

    @app.post("/api/browser/navigate")
    async def browser_navigate(request: Request):
        from jarvis import browser_agent as ba
        from jarvis.async_util import run_sync
        from jarvis.browser_product.history import record_visit

        body = await request.json()
        url = str(body.get("url") or "").strip()
        if not url:
            return JSONResponse(status_code=400, content={"ok": False, "message": "url required"})
        # Playwright sync API cannot run on the FastAPI event-loop thread.
        result = await run_sync(
            ba.navigate,
            url,
            allow_risky=bool(body.get("allow_risky")),
            allow_system_fallback=bool(body.get("allow_system_fallback")),
        )
        if result.get("ok"):
            try:
                record_visit(result.get("url") or url, title=result.get("title") or "")
            except Exception:
                pass
        return result

    @app.post("/api/browser/run")
    @app.post("/api/browser/run-task")
    async def browser_run(request: Request):
        body = await request.json()
        url = str(body.get("url") or "").strip()
        task = str(body.get("task") or body.get("goal") or "").strip()
        if not task:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": "task or goal required — nothing was run"},
            )
        try:
            from jarvis.async_util import run_sync
            from jarvis.p2_flags import browser_agent_enabled

            if not browser_agent_enabled():
                return {
                    "ok": False,
                    "message": "Browser agent disabled (set JARVIS_BROWSER_AGENT=1)",
                    "recovery": "Enable the flag and retry",
                }
            from jarvis.browser_agent import _modes_available, navigate, run_agent_task

            mode = body.get("mode") or "auto"
            modes = _modes_available()
            if mode == "vlm" and not modes.get("vlm"):
                return {
                    "ok": False,
                    "message": "VLM mode unavailable",
                    "recovery": modes.get("unavailable_reason"),
                    "modes_available": modes,
                }
            if mode in ("dom", "auto") and not modes.get("dom"):
                return {
                    "ok": False,
                    "message": "DOM/auto mode unavailable",
                    "recovery": modes.get("unavailable_reason"),
                    "modes_available": modes,
                }

            async_job = bool(body.get("async") or body.get("queue"))
            if async_job:
                from jarvis.browser_product.job_bridge import submit_browser_task

                return submit_browser_task(
                    task,
                    url=url,
                    mode=mode,
                    max_steps=int(body.get("max_steps") or 10),
                    allow_risky=bool(body.get("allow_risky")),
                    assistant=assistant,
                )

            def _run_sync_browser():
                if url:
                    nav = navigate(url, allow_risky=bool(body.get("allow_risky")))
                    if not nav.get("ok"):
                        return nav
                return run_agent_task(
                    task,
                    mode=mode,
                    max_steps=int(body.get("max_steps") or 10),
                    assistant=assistant,
                )

            # Do not wrap failures as ok:True
            return await run_sync(_run_sync_browser)
        except Exception as exc:
            return {"ok": False, "message": str(exc), "recovery": "Retry after checking Playwright"}

    @app.post("/api/browser/pause")
    def browser_pause():
        from jarvis.browser_agent import pause

        return {"ok": True, **pause()}

    @app.post("/api/browser/resume")
    def browser_resume():
        from jarvis.browser_agent import resume

        return {"ok": True, **resume()}

    @app.post("/api/browser/takeover")
    def browser_takeover():
        from jarvis.browser_agent import takeover

        return {"ok": True, **takeover()}

    @app.post("/api/browser/stop")
    def browser_stop():
        from jarvis.browser_agent import stop

        return {"ok": True, **stop()}

    @app.post("/api/browser/install-playwright")
    def browser_install_playwright():
        from jarvis.browser_playwright import ensure_playwright

        stack = ensure_playwright(install=True)
        ok = bool(stack.get("playwright") and stack.get("chromium"))
        return {
            "ok": ok,
            **stack,
            "message": "Playwright ready" if ok else "Install did not complete",
            "hint": None
            if ok
            else "Try: pip install playwright && playwright install chromium",
            "recovery": None if ok else "Install Chromium dependencies, then Refresh",
        }

    @app.get("/api/browser/screenshot/latest")
    def browser_screenshot_latest():
        from jarvis.browser_agent import status

        st = status()
        path = st.get("last_screenshot") or ""
        if not path or not Path(path).is_file():
            return {"ok": False, "message": "No screenshot yet — navigate or capture first"}
        return {
            "ok": True,
            "path": path,
            "url": "/api/browser/screenshot/image",
            "stale": bool(st.get("screenshot_stale")),
        }

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
        from jarvis.browser_agent import screenshot

        return screenshot(label="manual", reason="operator")

    @app.get("/api/browser/history")
    def browser_history(q: str = "", limit: int = 50):
        from jarvis.browser_product.history import list_history

        return list_history(query=q, limit=limit)

    @app.get("/api/browser/bookmarks")
    def browser_bookmarks():
        from jarvis.browser_product.history import list_bookmarks

        return list_bookmarks()

    @app.post("/api/browser/bookmarks")
    async def browser_bookmarks_add(request: Request):
        from jarvis.browser_product.history import add_bookmark

        body = await request.json()
        return add_bookmark(str(body.get("url") or ""), title=str(body.get("title") or ""))

    @app.post("/api/browser/bookmarks/remove")
    async def browser_bookmarks_remove(request: Request):
        from jarvis.browser_product.history import remove_bookmark

        body = await request.json()
        return remove_bookmark(str(body.get("url") or ""))

    @app.get("/api/browser/downloads")
    def browser_downloads():
        from jarvis.browser_product.downloads import list_downloads

        return list_downloads()

    @app.get("/api/browser/notes")
    def browser_notes():
        from jarvis.browser_product.history import list_notes

        return list_notes()

    @app.post("/api/browser/notes")
    async def browser_notes_add(request: Request):
        from jarvis.browser_product.history import add_note

        body = await request.json()
        return add_note(str(body.get("text") or ""), url=str(body.get("url") or ""))

    @app.post("/api/browser/save-documents")
    async def browser_save_docs(request: Request):
        from jarvis.extensions.browser.handlers import browser_save_documents

        body = await request.json()
        return browser_save_documents(assistant, body, "")

    @app.post("/api/browser/check-download")
    async def browser_check_download(request: Request):
        from jarvis.browser_product.downloads import check_download_safe

        body = await request.json()
        return check_download_safe(
            str(body.get("url") or ""),
            filename=str(body.get("filename") or ""),
            allow_risky=bool(body.get("allow_risky")),
        )

    @app.post("/api/browser/research/plan")
    async def browser_research_plan(request: Request):
        from jarvis.browser_product.multi_tab import plan_research

        body = await request.json()
        return plan_research(str(body.get("goal") or ""), body.get("urls") or [])

    @app.post("/api/browser/research/tab")
    async def browser_research_tab(request: Request):
        from jarvis.browser_product.multi_tab import run_tab

        body = await request.json()
        return run_tab(str(body.get("tab_id") or ""), allow_risky=bool(body.get("allow_risky")))

    @app.get("/api/browser/research/merge")
    def browser_research_merge():
        from jarvis.browser_product.multi_tab import merge_findings

        return merge_findings()

    @app.post("/api/browser/vision-coding")
    async def browser_vision_coding_api(request: Request):
        from jarvis.browser_product.vision_to_coding import vision_to_coding

        body = await request.json()
        return vision_to_coding(
            assistant,
            hint=str(body.get("hint") or ""),
            image_path=str(body.get("path") or ""),
            use_live_screenshot=not bool(body.get("path")),
        )

    @app.post("/api/browser/voice")
    async def browser_voice_api(request: Request):
        from jarvis.browser_product.voice_bridge import handle_voice_command

        body = await request.json()
        return handle_voice_command(str(body.get("text") or ""), assistant=assistant)

    @app.get("/api/browser/steps")
    def browser_steps():
        from jarvis.browser_product.session import steps

        return {"ok": True, "steps": steps(limit=50)}
