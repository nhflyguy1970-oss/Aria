"""Certification product HTTP API."""

from __future__ import annotations

import base64
import threading
from typing import Any

from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    @app.get("/api/certification/product")
    def certification_product_status():
        from jarvis.certification_product.engine import product_status

        return product_status()

    @app.get("/api/certification/home")
    def certification_home():
        from jarvis.certification_product.engine import home_payload

        return home_payload()

    @app.get("/api/certification/runs")
    def certification_runs(limit: int = 40):
        from jarvis.certification_product import store

        return {"ok": True, "runs": store.list_runs(limit=limit)}

    @app.get("/api/certification/runs/latest")
    def certification_latest():
        from jarvis.certification_product import store

        run = store.latest_run()
        return {"ok": True, "run": run}

    @app.get("/api/certification/runs/{run_id}")
    def certification_run(run_id: str):
        from jarvis.certification_product.engine import run_detail

        return run_detail(run_id)

    @app.get("/api/certification/runs/{run_id}/assertions")
    def certification_assertions(run_id: str, q: str = ""):
        from jarvis.certification_product import store

        rows = store.list_assertions(run_id)
        if q:
            ql = q.lower()
            rows = [r for r in rows if ql in json_blob(r).lower()]
        return {"ok": True, "assertions": rows}

    @app.get("/api/certification/runs/{run_id}/evidence")
    def certification_evidence(run_id: str):
        from jarvis.certification_product import store

        return {"ok": True, "files": store.list_evidence_files(run_id)}

    @app.get("/api/certification/runs/{run_id}/file")
    def certification_file(run_id: str, path: str):
        from jarvis.certification_product import store

        root = store.run_dir(run_id).resolve()
        target = (root / path).resolve()
        if root not in target.parents and target != root:
            return JSONResponse(status_code=400, content={"ok": False, "message": "Invalid path"})
        if not target.is_file():
            return JSONResponse(status_code=404, content={"ok": False, "message": "Not found"})
        return FileResponse(target)

    @app.post("/api/certification/run")
    async def certification_run_start(request: Request):
        """Start an evidence certification run (background)."""
        from jarvis.certification_product.runner import run_certification

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        label = str(body.get("label") or "Dashboard certification")
        skip_image = bool(body.get("skip_image"))
        suites = body.get("suites")
        if isinstance(suites, str):
            suites = [s.strip() for s in suites.split(",") if s.strip()]

        holder: dict[str, Any] = {"run_id": None}

        def _job() -> None:
            try:
                result = run_certification(label=label, skip_image=skip_image, suites=suites)
                holder["run_id"] = result.get("id")
            except Exception as exc:
                holder["error"] = str(exc)

        threading.Thread(target=_job, name="aria-cert-run", daemon=True).start()
        # Brief wait so caller often gets the real id
        import time as _t

        for _ in range(20):
            if holder.get("run_id") or holder.get("error"):
                break
            _t.sleep(0.05)
        from jarvis.certification_product import store

        latest = store.latest_run()
        return {
            "ok": True,
            "pending": True,
            "run_id": holder.get("run_id") or (latest or {}).get("id"),
            "message": "Certification running — poll /api/certification/runs/{id}",
            "error": holder.get("error"),
        }

    @app.post("/api/certification/run/sync")
    async def certification_run_sync(request: Request):
        """Synchronous run — returns full manifest (may take minutes if image suite included).

        Runs off the event loop so nested HTTP evidence calls against this same
        server can be served (avoiding self-deadlock).
        """
        import asyncio

        from jarvis.certification_product.runner import run_certification

        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        label = str(body.get("label") or "Sync certification")
        skip_image = bool(body.get("skip_image", True))
        suites = body.get("suites")
        result = await asyncio.to_thread(
            run_certification,
            label=label,
            skip_image=skip_image,
            suites=suites,
        )
        return {"ok": True, "run": result}

    @app.post("/api/certification/fixtures/seed_chat")
    async def certification_seed_chat(request: Request):
        """Seed durable chat messages on the live BranchManager (no LLM)."""
        body: dict[str, Any] = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        branch_id = str(body.get("branch_id") or "main").strip() or "main"
        messages = body.get("messages") or []
        if not isinstance(messages, list) or not messages:
            return JSONResponse(status_code=400, content={"ok": False, "message": "messages required"})
        from jarvis.config import build_system_prompt, load_personality_preset

        prompt = build_system_prompt(load_personality_preset(), assistant.memory)
        conv = assistant.branches.get_conversation(branch_id, prompt)
        seeded = [{"role": "system", "content": prompt}]
        for m in messages:
            role = str((m or {}).get("role") or "")
            content = str((m or {}).get("content") or "")
            if role in ("user", "assistant") and content:
                seeded.append({"role": role, "content": content})
        if len(seeded) < 2:
            return JSONResponse(status_code=400, content={"ok": False, "message": "no user/assistant messages"})
        conv.messages = seeded
        assistant.branches.persist(branch_id)
        return {
            "ok": True,
            "branch_id": branch_id,
            "count": sum(1 for m in seeded if m.get("role") in ("user", "assistant")),
        }

    @app.post("/api/certification/runs/{run_id}/screenshot")
    async def certification_upload_screenshot(run_id: str, request: Request):
        from jarvis.certification_product import store

        body = await request.json()
        name = str(body.get("name") or f"shot_{int(__import__('time').time())}.png")
        b64 = str(body.get("data") or "")
        if "," in b64:
            b64 = b64.split(",", 1)[1]
        if not b64:
            return JSONResponse(status_code=400, content={"ok": False, "message": "data required"})
        raw = base64.b64decode(b64)
        rel = f"files/ui_captures_uncredited/{name}"
        store.write_bytes(run_id, rel, raw)
        return {"ok": True, "path": rel, "bytes": len(raw), "credited": False}

    @app.post("/api/certification/runs/{run_id}/console")
    async def certification_upload_console(run_id: str, request: Request):
        from jarvis.certification_product import store

        body = await request.json()
        text = str(body.get("text") or body.get("log") or "")
        store.write_text(run_id, "logs/browser_console.txt", text)
        return {"ok": True}

    @app.post("/api/certification/package/{run_id}")
    def certification_package(run_id: str):
        from jarvis.certification_product import store

        path = store.package_zip(run_id)
        if not path:
            return JSONResponse(status_code=404, content={"ok": False, "message": "Run not found"})
        return {"ok": True, "path": str(path), "name": path.name}


def json_blob(obj: Any) -> str:
    import json

    return json.dumps(obj, default=str)
