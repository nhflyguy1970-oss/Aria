"""Additional FastAPI routes for journal, memory browser, gallery, export."""

import html
import re
from pathlib import Path

from fastapi import File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response

from jarvis.action_log import clear_log, list_actions
from jarvis.cache_state import (
    get_gallery_cache,
    get_video_gallery_cache,
    invalidate_gallery,
    invalidate_video_gallery,
    set_gallery_cache,
    set_video_gallery_cache,
)
from jarvis.config import DATA_DIR


class _LazyAssistantAttr:
    def __init__(self, assistant, attr: str):
        self._assistant = assistant
        self._attr = attr

    def __getattr__(self, name: str):
        return getattr(getattr(self._assistant, self._attr), name)


def register_routes(app, assistant):
    if assistant.__class__.__name__ == "_AssistantProxy":
        journal = _LazyAssistantAttr(assistant, "journal")
    else:
        journal = assistant.journal

    from jarvis.product_registration import register as register_product

    # Gallery product routes must register before /api/gallery/{name}
    from jarvis.gallery_product.api import register_routes as register_gallery_product
    from jarvis.image_generation.api import register_routes as register_image_generation
    from jarvis.video_generation.api import register_routes as register_video_generation
    from jarvis.vision_product.api import register_routes as register_vision_product
    from jarvis.voice_product.api import register_routes as register_voice_product

    register_product("gallery_product", register_gallery_product, app, assistant, required=True)
    register_product("image_generation", register_image_generation, app, assistant, required=True)
    register_product("video_generation", register_video_generation, app, assistant, required=True)
    register_product("voice_product", register_voice_product, app, assistant, required=True)
    register_product("vision_product", register_vision_product, app, assistant, required=True)

    from jarvis.capabilities_product.api import register_product_routes as register_capabilities_product

    register_product("capabilities_product", register_capabilities_product, app, assistant)

    @app.get("/api/journal")
    def journal_all():
        return journal.export_all()

    @app.get("/api/journal/key")
    def journal_key():
        return journal.get_key()

    @app.post("/api/journal/key")
    async def journal_key_update(request: Request):
        body = await request.json()
        key = journal.update_key(
            symbols=body.get("symbols"),
            description=body.get("description"),
            custom=body.get("custom"),
        )
        return {"ok": True, "key": key}

    @app.post("/api/journal/undo")
    def journal_undo():
        return journal.undo()

    @app.post("/api/journal/redo")
    def journal_redo():
        return journal.redo()

    @app.get("/api/journal/daily/timeline")
    def journal_daily_timeline(day: str = ""):
        from jarvis.modules.journal import _today

        return journal.daily_timeline(day or _today())

    @app.get("/api/journal/weekly/review")
    def journal_weekly_review(week: str = ""):
        from jarvis.modules.journal import _week_key

        return journal.weekly_review_get(week or _week_key())

    @app.post("/api/journal/weekly/review/toggle")
    async def journal_weekly_review_toggle(item_id: str = Form(...), week: str = Form("")):
        from jarvis.modules.journal import _week_key

        return {"ok": True, **journal.weekly_review_toggle(item_id, week or _week_key())}

    @app.post("/api/journal/weekly/review/notes")
    async def journal_weekly_review_notes(notes: str = Form(""), week: str = Form("")):
        from jarvis.modules.journal import _week_key

        return {"ok": True, **journal.weekly_review_set_notes(notes, week or _week_key())}

    @app.post("/api/journal/reflect/review")
    async def journal_reflect_review(
        scope: str = Form("month"), month: str = Form(""), week: str = Form("")
    ):
        text = journal.ai_reflect_review(scope, month or None, week or None)
        return {"ok": True, "reflection": text}

    @app.get("/api/journal/history")
    def journal_history():
        return {"ok": True, **journal.history_info()}

    @app.post("/api/journal/bullet/{bullet_id}/child")
    async def journal_bullet_child(
        bullet_id: str,
        content: str = Form(...),
        bullet_type: str = Form("task"),
    ):
        b = journal.bullet_add_child(bullet_id, content, bullet_type)
        if not b:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "bullet": b}

    @app.post("/api/journal/bullet/{bullet_id}/schedule")
    async def journal_bullet_schedule(bullet_id: str, month: str = Form(...)):
        b = journal.bullet_schedule(bullet_id, month)
        if not b:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "bullet": b}

    @app.post("/api/journal/bullet/{bullet_id}/thread")
    async def journal_bullet_thread(
        bullet_id: str,
        day: str = Form(""),
        duplicate: str = Form("false"),
    ):
        from jarvis.modules.journal import _today

        dup = duplicate.lower() in ("1", "true", "yes")
        b = journal.bullet_thread_to_daily(bullet_id, day or _today(), duplicate=dup)
        if not b:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "bullet": b, "duplicate": dup}

    @app.post("/api/journal/bullet/{bullet_id}/link")
    async def journal_bullet_link(bullet_id: str, to_id: str = Form(...), label: str = Form("")):
        b = journal.bullet_link(bullet_id, to_id, label)
        if not b:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "bullet": b}

    @app.delete("/api/journal/bullet/{bullet_id}/link/{to_id}")
    def journal_bullet_unlink(bullet_id: str, to_id: str):
        b = journal.bullet_unlink(bullet_id, to_id)
        return {"ok": bool(b), "bullet": b}

    @app.get("/api/journal/bullet/{bullet_id}/resolve")
    def journal_bullet_resolve(bullet_id: str):
        b = journal.bullet_resolve(bullet_id)
        if not b:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "bullet": b}

    @app.post("/api/journal/bullet/{bullet_id}/time")
    async def journal_bullet_time(
        bullet_id: str,
        time: str = Form(""),
        duration_min: str = Form(""),
    ):
        dur = int(duration_min) if duration_min.isdigit() else None
        b = journal.bullet_set_time(bullet_id, time or None, dur)
        if not b:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "bullet": b}

    @app.post("/api/journal/future/transfer")
    async def journal_future_transfer(future_month: str = Form(...), monthly_month: str = Form("")):
        from jarvis.modules.journal import _month_key

        return {
            "ok": True,
            **journal.transfer_future_to_month(future_month, monthly_month or _month_key()),
        }

    @app.get("/api/journal/wellness")
    def journal_wellness(month: str = ""):
        from jarvis.modules.journal import _month_key

        return journal.wellness_overview(month or _month_key())

    @app.post("/api/journal/wellness")
    async def journal_wellness_set(
        day: str = Form(...),
        mood: str = Form(""),
        gratitude: str = Form(""),
    ):
        items = [g.strip() for g in gratitude.split("\n") if g.strip()] if gratitude else None
        mood_val = int(mood) if mood.isdigit() else None
        page = journal.daily_set_wellness(day, mood=mood_val, gratitude=items)
        return {"ok": True, "mood": page.get("mood"), "gratitude": page.get("gratitude", [])}

    @app.post("/api/journal/gratitude")
    async def journal_gratitude_add(day: str = Form(...), text: str = Form(...)):
        page = journal.daily_add_gratitude(day, text)
        return {"ok": True, "gratitude": page.get("gratitude", [])}

    @app.get("/api/journal/monthly/review")
    def journal_monthly_review(month: str = ""):
        from jarvis.modules.journal import _month_key

        return journal.monthly_review_get(month or _month_key())

    @app.post("/api/journal/monthly/review/toggle")
    async def journal_monthly_review_toggle(item_id: str = Form(...), month: str = Form("")):
        from jarvis.modules.journal import _month_key

        return {"ok": True, **journal.monthly_review_toggle(item_id, month or _month_key())}

    @app.post("/api/journal/monthly/review/notes")
    async def journal_monthly_review_notes(notes: str = Form(""), month: str = Form("")):
        from jarvis.modules.journal import _month_key

        return {"ok": True, **journal.monthly_review_set_notes(notes, month or _month_key())}

    @app.get("/api/journal/index")
    def journal_index():
        return {"entries": journal.index_list()}

    @app.post("/api/journal/index")
    async def journal_index_add(topic: str = Form(...), pages: str = Form("")):
        page_list = [p.strip() for p in pages.split(",") if p.strip()]
        return {"ok": True, "entry": journal.index_add(topic, page_list)}

    @app.delete("/api/journal/index/{entry_id}")
    def journal_index_del(entry_id: str):
        return {"ok": journal.index_delete(entry_id)}

    @app.post("/api/journal/index/rebuild")
    def journal_index_rebuild():
        return {"ok": True, "result": journal.rebuild_auto_index()}

    @app.get("/api/journal/index/resolve")
    def journal_index_resolve(page: str = ""):
        loc = journal.index_resolve_page(page)
        if not loc:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "location": loc}

    @app.post("/api/journal/migrate-daily")
    async def journal_migrate_daily(from_day: str = Form(""), to_day: str = Form("")):
        from datetime import date, timedelta

        from jarvis.modules.journal import _today

        src = from_day or _today()
        if to_day:
            dst = to_day
        else:
            dst = (date.fromisoformat(src) + timedelta(days=1)).isoformat()
        return {"ok": True, **journal.migrate_daily_open(src, dst), "to_day": dst}

    @app.post("/api/journal/bullet/{bullet_id}/signifier")
    async def journal_bullet_signifier(bullet_id: str, name: str = Form(...)):
        b = journal.bullet_toggle_signifier(bullet_id, name)
        if not b:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "bullet": b}

    @app.post("/api/journal/bullet/{bullet_id}/cancel")
    def journal_bullet_cancel(bullet_id: str):
        b = journal.bullet_cancel(bullet_id)
        return {"ok": bool(b), "bullet": b}

    @app.get("/api/journal/future")
    def journal_future():
        return journal.future_list()

    @app.post("/api/journal/future")
    async def journal_future_add(
        month: str = Form(...), content: str = Form(...), bullet_type: str = Form("task")
    ):
        return {"ok": True, "bullet": journal.future_add(month, content, bullet_type)}

    @app.get("/api/journal/monthly/calendar")
    def journal_monthly_calendar(month: str = ""):
        from jarvis.modules.journal import _month_key

        return journal.monthly_calendar(month or _month_key())

    @app.get("/api/journal/monthly")
    def journal_monthly(month: str = ""):
        from jarvis.modules.journal import _month_key

        return journal.monthly_get(month or _month_key())

    @app.post("/api/journal/monthly")
    async def journal_monthly_add(
        content: str = Form(...), bullet_type: str = Form("task"), month: str = Form("")
    ):
        from jarvis.modules.journal import _month_key

        mk = month or _month_key()
        return {"ok": True, "bullet": journal.monthly_add(content, bullet_type, month=mk or None)}

    @app.get("/api/journal/daily")
    def journal_daily(day: str = ""):
        from jarvis.modules.journal import _today

        # Owner Journal never shows test/QA residue. Isolated DATA_DIR tests may
        # still write those bullets; Integrity purge still scrubs the store.
        return journal.daily_get(day or _today(), include_qa=False)

    @app.post("/api/journal/daily")
    async def journal_daily_add(
        content: str = Form(...),
        bullet_type: str = Form("task"),
        day: str = Form(""),
        time: str = Form(""),
    ):
        from jarvis.calendar_time import validate_time_hm

        hm = None
        if (time or "").strip():
            try:
                hm = validate_time_hm(time)
            except ValueError as exc:
                return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        try:
            bullet = journal.daily_add(content, bullet_type, day=day or None, time=hm)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {
            "ok": True,
            "bullet": bullet,
        }

    @app.get("/api/briefing")
    def morning_briefing_get(launch: bool = False, force: bool = False):
        from jarvis.morning_briefing import (
            briefing_enabled,
            briefing_visible,
            build_briefing,
            last_briefing_shown,
        )

        if not briefing_visible(force=force):
            return {
                "ok": True,
                "show": False,
                "enabled": briefing_enabled(),
                "last_shown": last_briefing_shown(),
            }
        briefing = build_briefing(
            journal=assistant.journal,
            memory_store=assistant.memory,
            include_quote=not launch,
        )
        return {"ok": True, "show": True, "enabled": briefing_enabled(), **briefing}

    @app.get("/api/documents")
    def documents_list(limit: int = 50, offset: int = 0, q: str = ""):
        from jarvis.document_services import list_library_enriched

        docs = list_library_enriched(limit=min(max(limit, 1), 200), offset=max(offset, 0), q=q)
        return {"ok": True, "documents": docs, "count": len(docs)}

    @app.get("/api/documents/home")
    def documents_home_api():
        from jarvis.document_services import documents_home

        return documents_home()

    @app.get("/api/documents/health")
    def documents_health_api():
        from jarvis.document_services import index_health

        return index_health()

    @app.get("/api/documents/preview")
    def documents_preview(path: str = ""):
        from jarvis.document_services import preview_document

        if not (path or "").strip():
            return JSONResponse(status_code=400, content={"ok": False, "message": "path required"})
        return preview_document(path)

    @app.get("/api/documents/briefing")
    def documents_briefing_api():
        from jarvis.document_services import document_briefing

        return document_briefing()

    @app.get("/api/documents/project-pack")
    def documents_project_pack(slug: str = ""):
        from jarvis.document_services import project_retrieval_pack

        return project_retrieval_pack(slug or None)

    @app.post("/api/documents/ask")
    async def documents_ask(request: Request):
        from jarvis.document_services import ask_with_sources

        body = await request.json()
        return ask_with_sources(
            (body.get("question") or "").strip(),
            mode=(body.get("mode") or "library").strip(),
            paths=body.get("paths") or None,
            folder=(body.get("folder") or "").strip(),
        )

    @app.post("/api/documents/upload")
    async def documents_upload(request: Request):
        from jarvis.document_services import save_upload

        form = await request.form()
        upload = form.get("file")
        if upload is None:
            return JSONResponse(status_code=400, content={"ok": False, "message": "file required"})
        filename = getattr(upload, "filename", None) or "upload.bin"
        content = await upload.read()
        result = save_upload(filename, content)
        status = 200 if result.get("ok") else 400
        return JSONResponse(status_code=status, content=result)

    @app.post("/api/documents/import-folder")
    async def documents_import_folder(request: Request):
        from jarvis.async_util import run_sync
        from jarvis.document_services import import_folder

        body = await request.json()
        # Never block the HTTP event loop on home-directory scans.
        return await run_sync(import_folder, (body.get("path") or "").strip())

    @app.post("/api/documents/classify")
    async def documents_classify(request: Request):
        from jarvis.document_services import classify_document, preview_document

        body = await request.json()
        path = (body.get("path") or "").strip()
        if path:
            prev = preview_document(path)
            if not prev.get("ok"):
                return prev
            doc = prev["document"]
            return {"ok": True, "suggestion": doc.get("suggestion"), "document": doc}
        return {
            "ok": True,
            "suggestion": classify_document(body.get("title") or "", body.get("text") or ""),
        }

    @app.post("/api/briefing/dismiss")
    def morning_briefing_dismiss():
        from jarvis.morning_briefing import mark_briefing_shown

        mark_briefing_shown()
        return {"ok": True}

    @app.get("/api/lan")
    def lan_info():
        from jarvis.lan import lan_status

        return lan_status()

    try:
        from jarvis.integrations_product.api import register_product_routes as register_integrations_product

        if not register_product("integrations_product", register_integrations_product, app, assistant):
            @app.get("/api/integrations/secrets")
            def integrations_secrets_get():
                from jarvis.integration_secrets import secrets_status

                return {"ok": True, **secrets_status()}

            @app.post("/api/integrations/secrets")
            async def integrations_secrets_post(request: Request):
                from jarvis.integration_secrets import save_secrets

                try:
                    body = await request.json()
                except Exception:
                    body = {}
                if not isinstance(body, dict):
                    return JSONResponse(
                        status_code=400, content={"ok": False, "message": "JSON body required"}
                    )
                return save_secrets(body)
    except Exception:
        # Outer catch only for import errors before register_product — still fail-loud via register
        register_product(
            "integrations_product",
            lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("integrations_product import failed")),
            app,
            assistant,
        )

    from jarvis.search_product.api import register_product_routes as register_search_product
    from jarvis.settings_product.api import register_product_routes as register_settings_product
    from jarvis.dashboard_product.api import register_product_routes as register_dashboard_product
    from jarvis.layouts_product.api import register_product_routes as register_layouts_product
    from jarvis.notifications_product.api import register_product_routes as register_notifications_product
    from jarvis.health_product.api import register_product_routes as register_health_product
    from jarvis.certification_product.api import register_product_routes as register_certification_product
    from jarvis.repair_product.api import register_product_routes as register_repair_product
    from jarvis.integrity_product.api import register_product_routes as register_integrity_product
    from jarvis.shell.api import register_product_routes as register_shell_product
    from jarvis.calendar_api import register_product_routes as register_calendar_product
    from jarvis.provider_health.api import register_product_routes as register_provider_health
    from jarvis.latency_observability.api import register_product_routes as register_latency

    register_product("search_product", register_search_product, app, assistant)
    register_product("settings_product", register_settings_product, app, assistant)
    register_product("dashboard_product", register_dashboard_product, app, assistant)
    register_product("layouts_product", register_layouts_product, app, assistant)
    register_product("notifications_product", register_notifications_product, app, assistant)
    register_product("health_product", register_health_product, app, assistant)
    register_product("certification_product", register_certification_product, app, assistant)
    register_product("repair_product", register_repair_product, app, assistant)
    register_product("integrity_product", register_integrity_product, app, assistant)
    register_product("shell", register_shell_product, app, assistant)
    register_product("calendar", register_calendar_product, app, assistant)
    register_product("provider_health", register_provider_health, app, assistant)
    register_product("latency_observability", register_latency, app, assistant)

    from jarvis.activity_api import register_activity_routes

    register_product("activity_inbox", register_activity_routes, app, assistant)

    @app.get("/api/collaborations")
    def collaborations_list():
        from jarvis.collaboration import store as collab_store

        return {"ok": True, "collaborations": collab_store.list_collaborations(limit=50)}

    @app.post("/api/collaborations")
    def collaborations_create(
        objective: str = Form(...), initiator: str = Form("analysis_specialist")
    ):
        from jarvis.collaboration import engine as collab_engine

        try:
            return {"ok": True, **collab_engine.create_collaboration(objective, initiator=initiator)}
        except collab_engine.DelegationError as exc:
            return {"ok": False, "message": str(exc)}

    @app.post("/api/collaborations/{collaboration_id}/delegate")
    def collaborations_delegate(
        collaboration_id: str,
        requester: str = Form(...),
        objective: str = Form(...),
        target: str = Form(""),
        capability: str = Form(""),
        action: str = Form(""),
        depends_on: str = Form(""),
    ):
        from jarvis.collaboration import engine as collab_engine
        from jarvis.collaboration import graph as collab_graph

        deps = [d for d in (depends_on or "").split(",") if d.strip()]
        try:
            task = collab_engine.delegate(
                collaboration_id,
                requester=requester,
                objective=objective,
                target=target,
                capability=capability,
                action=action,
                depends_on=[d.strip() for d in deps],
            )
        except (collab_engine.DelegationError, collab_graph.GraphError) as exc:
            return {"ok": False, "message": str(exc)}
        return {"ok": True, "task": task}

    @app.get("/api/collaborations/{collaboration_id}")
    def collaborations_status(collaboration_id: str):
        from jarvis.collaboration import engine as collab_engine

        snapshot = collab_engine.status(collaboration_id)
        if not snapshot:
            return {"ok": False, "message": f"no collaboration {collaboration_id}"}
        return {"ok": True, "collaboration": snapshot}

    @app.get("/api/collaborations/{collaboration_id}/report")
    def collaborations_report(collaboration_id: str):
        from jarvis.collaboration import engine as collab_engine

        data = collab_engine.report(collaboration_id)
        if not data:
            return {"ok": False, "message": f"no collaboration {collaboration_id}"}
        return {"ok": True, "report": data}

    @app.get("/api/agents")
    def specialized_agents_list():
        from jarvis import specialized_agents as agents

        return {"ok": True, "agents": [a.to_dict() for a in agents.list_agents()]}

    @app.get("/api/agents/capabilities")
    def specialized_agents_capabilities():
        from jarvis import specialized_agents as agents

        return {"ok": True, "capabilities": agents.capabilities()}

    @app.post("/api/agents/select")
    def specialized_agents_select(task: str = Form(""), capability: str = Form("")):
        from jarvis import specialized_agents as agents

        return {"ok": True, "selection": agents.select(task, required_capability=capability)}

    @app.post("/api/agents/invoke")
    def specialized_agents_invoke(
        task: str = Form(...),
        agent_id: str = Form(""),
        action: str = Form(""),
        capability: str = Form(""),
    ):
        from jarvis import specialized_agents as agents

        if agent_id:
            return agents.invoke(agent_id, task, assistant=assistant, action=action)
        return agents.select_and_invoke(
            task, assistant=assistant, required_capability=capability, action=action
        )

    @app.get("/api/agents/{agent_id}")
    def specialized_agent_get(agent_id: str):
        from jarvis import specialized_agents as agents

        agent = agents.get(agent_id)
        if not agent:
            return {"ok": False, "message": f"no agent {agent_id}"}
        return {"ok": True, "agent": agent.to_dict(include_instructions=True)}

    @app.get("/api/deep-research")
    def deep_research_list():
        from jarvis.research import store as research_store

        return {"ok": True, "research": research_store.list_jobs(limit=50)}

    @app.post("/api/deep-research")
    def deep_research_create(objective: str = Form(...)):
        from jarvis.research import engine as research_engine

        text = (objective or "").strip()
        if not text:
            return {"ok": False, "message": "objective required"}
        return {"ok": True, **research_engine.create_research(text)}

    @app.get("/api/deep-research/{research_id}")
    def deep_research_status(research_id: str):
        from jarvis.research import engine as research_engine

        snapshot = research_engine.status(research_id)
        if not snapshot:
            return {"ok": False, "message": f"no research {research_id}"}
        return {"ok": True, "research": snapshot}

    @app.get("/api/deep-research/{research_id}/report")
    def deep_research_report(research_id: str):
        from jarvis.research import engine as research_engine

        data = research_engine.report(research_id)
        if not data:
            return {"ok": False, "message": f"no research {research_id}"}
        return {"ok": True, "report": data}

    @app.get("/api/knowledge")
    def knowledge_list():
        from jarvis.knowledge import list_topics

        return {"ok": True, "topics": list_topics()}

    @app.get("/api/knowledge/research")
    def knowledge_research_list_api():
        from jarvis.knowledge_research_daily import (
            _categories,
            _load_state,
            list_research_briefs,
            research_enabled,
        )

        state = _load_state()
        cats = _categories(memory=assistant.memory)
        return {
            "ok": True,
            "enabled": research_enabled(),
            "last_run_day": state.get("last_run_day", ""),
            "categories": [
                {
                    "id": c["id"],
                    "slug": c["slug"],
                    "title": c["title"],
                    "kind": c.get("kind", "stack"),
                    "source": c.get("source", "builtin"),
                }
                for c in cats
            ],
            "profile_topic_count": sum(1 for c in cats if c.get("kind") == "profile"),
            "briefs": list_research_briefs(),
        }

    @app.get("/api/knowledge/research/daily")
    def knowledge_research_daily_get():
        from jarvis.knowledge_research_daily import list_research_briefs

        briefs = list_research_briefs()
        if not briefs:
            return JSONResponse(
                status_code=404,
                content={"ok": False, "message": "Brief not found", "briefs": []},
            )
        return {"ok": True, "briefs": briefs, "count": len(briefs)}

    @app.get("/api/knowledge/research/{slug}")
    def knowledge_research_get_api(slug: str):
        from jarvis.knowledge_research_daily import RESEARCH_DIR

        safe = re.sub(r"[^\w-]", "", (slug or "").strip())
        path = RESEARCH_DIR / f"{safe}.md"
        if not path.is_file():
            return JSONResponse(
                status_code=404, content={"ok": False, "message": "Brief not found"}
            )
        return {"ok": True, "slug": safe, "markdown": path.read_text(encoding="utf-8")[:120_000]}

    @app.post("/api/knowledge/research/daily")
    async def knowledge_research_daily(request: Request):
        from jarvis.background_jobs import submit_action
        from jarvis.handlers import ensure_handlers_loaded
        from jarvis.handlers.registry import get_spec
        from jarvis.knowledge_research_daily import research_category, run_nightly_research

        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        category = (body.get("category") or "").strip()
        force = body.get("force") is True
        async_mode = body.get("async") is not False

        def _sync_result() -> dict:
            if category:
                result = research_category(category, memory=assistant.memory, force=force)
                if result.get("ok") and result.get("remembered"):
                    assistant.refresh_system_prompt()
                return {"ok": result.get("ok", False), **result}
            results = run_nightly_research(memory=assistant.memory, force=force)
            if any(r.get("remembered") for r in results if isinstance(r, dict)):
                assistant.refresh_system_prompt()
            updated = [
                r for r in results if isinstance(r, dict) and r.get("ok") and not r.get("skipped")
            ]
            if updated:
                titles = ", ".join(r.get("title") or r.get("slug") or "topic" for r in updated[:5])
                message = f"Research complete — {len(updated)} topic(s): {titles}."
            elif results and results[0].get("skipped"):
                message = results[0].get("message", "Already completed today.")
            else:
                message = results[0].get("message") if results else "No research categories ran."
            ok = bool(updated) or (results and results[0].get("ok"))
            return {"ok": ok, "message": message, "results": results}

        if async_mode:
            ensure_handlers_loaded()
            spec = get_spec("knowledge_research_run")
            if not spec or not spec.handler:
                return _sync_result()
            params: dict = {"force": "true" if force else "false"}
            if category:
                params["category"] = category
            job_id = submit_action(
                assistant,
                "knowledge_research_run",
                params,
                f"knowledge research {category or 'all'}",
            )
            return {
                "ok": True,
                "pending": True,
                "job_id": job_id,
                "message": "Knowledge research queued — poll /api/coding/job/{job_id}",
            }

        return _sync_result()

    @app.get("/api/homeassistant/status")
    def homeassistant_status():
        from jarvis.env_loader import load_jarvis_env
        from jarvis.home_assistant import status_payload

        load_jarvis_env()
        return {"ok": True, **status_payload()}

    @app.post("/api/homeassistant/config")
    async def homeassistant_config(request: Request):
        from jarvis.home_assistant import save_config

        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        enabled = body.get("enabled")
        if enabled is not None and not isinstance(enabled, bool):
            enabled = str(enabled).lower() in ("1", "true", "yes", "on")

        result = save_config(
            url=body.get("url"),
            token=body.get("token"),
            leave_scene=body.get("leave_scene"),
            enabled=enabled,
            ensure_automation_secret=body.get("ensure_automation_secret", True),
        )
        status = (
            200 if result.get("connection", {}).get("ok") or not result.get("token_set") else 200
        )
        return JSONResponse(status_code=status, content={"ok": True, **result})

    @app.post("/api/homeassistant/test")
    async def homeassistant_test(request: Request):
        from jarvis.home_assistant import test_connection

        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        result = test_connection(url=body.get("url"), token=body.get("token"))
        status = 200 if result.get("ok") else 400
        return JSONResponse(status_code=status, content=result)

    @app.get("/api/environment")
    def environment_snapshot():
        from jarvis.environment import snapshot as env_snapshot

        return {"ok": True, **env_snapshot()}

    @app.get("/api/documents/search")
    def documents_search(q: str = "", limit: int = 8, project: int = 0):
        from jarvis.document_services import search_library

        query = (q or "").strip()
        if not query:
            return JSONResponse(status_code=400, content={"ok": False, "message": "q required"})
        return search_library(query, limit=min(limit, 20), project_scope=bool(project))

    @app.post("/api/documents/reindex")
    def documents_reindex():
        from jarvis.document_services import rebuild_search_index

        return rebuild_search_index(force=True)

    @app.post("/api/documents/learn")
    async def documents_learn(request: Request):
        """Stage Memory candidates from a document — never silent ACM writes."""
        from jarvis.document_services import stage_learn_candidates

        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}
        result = stage_learn_candidates(
            (body.get("path") or "").strip(),
            url=(body.get("url") or "").strip(),
            text=(body.get("text") or "").strip(),
            title=(body.get("title") or "").strip(),
        )
        status = 200 if result.get("ok") else 400
        return JSONResponse(status_code=status, content=result)

    @app.post("/api/automation/inbound")
    async def automation_inbound(request: Request):
        from jarvis.home_assistant import (
            activate_scene,
            automation_secret,
            verify_automation_secret,
        )

        secret_hdr = request.headers.get("X-Jarvis-Automation-Secret")
        secret_q = request.query_params.get("secret")
        configured = automation_secret()
        if not configured:
            return JSONResponse(
                status_code=503,
                content={
                    "ok": False,
                    "message": "Set JARVIS_AUTOMATION_SECRET in data/jarvis.env to enable inbound webhooks.",
                },
            )
        if secret_q and not secret_hdr:
            return JSONResponse(
                status_code=401,
                content={
                    "ok": False,
                    "message": "Pass secret via X-Jarvis-Automation-Secret header only (query param rejected).",
                },
            )
        if not verify_automation_secret(secret_hdr, secret_q):
            return JSONResponse(
                status_code=401,
                content={"ok": False, "message": "Invalid automation secret."},
            )

        try:
            body = await request.json()
        except Exception:
            body = {}
        if not isinstance(body, dict):
            body = {}

        def _pub(name: str, status: str, why: str = "", ok: bool = True):
            try:
                from jarvis.automation.activity_bridge import publish_run_event
                from jarvis.automation.execution import FAILED, SUCCEEDED

                return publish_run_event(
                    kind="webhook",
                    name=name,
                    status=SUCCEEDED if ok else FAILED,
                    source="home",
                    why=why or status,
                    executed=True,
                    detail={"action": action},
                )
            except Exception:
                return {}

        action = (body.get("action") or "chat").strip().lower()
        message = (body.get("message") or body.get("text") or "").strip()

        if action == "chat":
            import os

            allow_chat = os.getenv("JARVIS_AUTOMATION_ALLOW_CHAT", "0").strip().lower() in (
                "1",
                "true",
                "yes",
                "on",
            )
            if not allow_chat:
                return JSONResponse(
                    status_code=403,
                    content={
                        "ok": False,
                        "message": "Automation chat disabled. Set JARVIS_AUTOMATION_ALLOW_CHAT=1 to enable, "
                        "or use action journal_log|ha_scene|briefing|run_script|wake|resources.",
                    },
                )
            if not message:
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "message": "message or text required for chat action."},
                )
            result = assistant.process(message)
            return result
        if action == "journal_log":
            text = message or (body.get("entry") or "").strip()
            if not text:
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "message": "text or entry required for journal_log."},
                )
            from jarvis.handlers import ensure_handlers_loaded
            from jarvis.handlers.registry import call_action

            ensure_handlers_loaded()
            result = call_action(assistant, "journal_log", {"text": text}, text)
            return result

        if action == "ha_scene":
            scene = (body.get("scene") or message or "").strip()
            if not scene:
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "message": "scene required for ha_scene."},
                )
            ok, msg = activate_scene(scene)
            status = 200 if ok else 400
            pub = _pub(f"HA scene {scene}", "ok" if ok else "failed", msg, ok)
            return JSONResponse(
                status_code=status,
                content={"ok": ok, "message": msg, "activity": pub.get("activity"), "run": pub.get("run")},
            )

        if action == "briefing":
            from jarvis.handlers import ensure_handlers_loaded
            from jarvis.handlers.registry import call_action

            ensure_handlers_loaded()
            result = call_action(assistant, "morning_briefing", {}, message or "morning briefing")
            pub = _pub("Morning briefing", "ok" if result.get("ok", True) else "failed", "briefing", bool(result.get("ok", True)))
            if isinstance(result, dict):
                result = {**result, "activity": pub.get("activity"), "run": pub.get("run")}
            return result

        if action == "run_script":
            from jarvis.remote_control import run_whitelisted_script

            script = (body.get("script") or body.get("name") or message or "").strip()
            if not script:
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "message": "script name required (data/scripts/ only)."},
                )
            ok, msg = run_whitelisted_script(script)
            status = 200 if ok else 400
            return JSONResponse(status_code=status, content={"ok": ok, "message": msg})

        if action == "wake":
            from jarvis.remote_control import wake_on_lan

            mac = (body.get("mac") or message or "").strip() or None
            ok, msg = wake_on_lan(mac)
            status = 200 if ok else 400
            return JSONResponse(status_code=status, content={"ok": ok, "message": msg})

        if action == "resources":
            from jarvis.resource_router import snapshot as resource_snapshot

            return JSONResponse(status_code=200, content={"ok": True, **resource_snapshot()})

        if action == "environment":
            from jarvis.environment import snapshot as env_snapshot

            return JSONResponse(status_code=200, content={"ok": True, **env_snapshot()})

        return JSONResponse(
            status_code=400,
            content={"ok": False, "message": f"Unknown action: {action}"},
        )

    @app.get("/api/upgrade/status")
    def upgrade_status():
        from jarvis.upgrade_wizard import wizard_status

        return {"ok": True, **wizard_status()}

    @app.post("/api/upgrade/clear")
    def upgrade_clear():
        from jarvis.upgrade_wizard import clear_session, wizard_status

        clear_session()
        return {"ok": True, **wizard_status()}

    @app.post("/api/upgrade/propose")
    async def upgrade_propose(task: str = Form(...), max_steps: int = Form(4)):
        result = assistant._upgrade_wizard(
            {"task": task.strip(), "max_steps": max_steps},
            f"upgrade jarvis: {task.strip()}",
        )
        status = 400 if not result.get("ok") else 200
        return JSONResponse(status_code=status, content=result)

    @app.post("/api/upgrade/verify")
    async def upgrade_verify(proposal_id: str = Form("")):
        result = assistant._upgrade_verify(
            {"proposal_id": proposal_id.strip()},
            "verify upgrade",
        )
        status = 400 if not result.get("ok") else 200
        return JSONResponse(status_code=status, content=result)

    @app.post("/api/upgrade/apply")
    async def upgrade_apply(proposal_id: str = Form(""), force: str = Form("false")):
        result = assistant._upgrade_apply(
            {"proposal_id": proposal_id.strip(), "force": force},
            "apply upgrade",
        )
        status = 400 if not result.get("ok") else 200
        return JSONResponse(status_code=status, content=result)

    @app.post("/api/upgrade/rollback")
    async def upgrade_rollback(snapshot_id: str = Form("")):
        result = assistant._upgrade_rollback(
            {"snapshot_id": snapshot_id.strip()},
            "rollback upgrade",
        )
        status = 400 if not result.get("ok") else 200
        return JSONResponse(status_code=status, content=result)

    @app.post("/api/journal/rapid")
    async def journal_rapid(
        text: str = Form(...),
        day: str = Form(""),
        bullet_type: str = Form("task"),
        section: str = Form("daily"),
        week: str = Form(""),
        month: str = Form(""),
    ):
        try:
            bullets = journal.parse_rapid_log(
                text,
                day=day or None,
                default_type=bullet_type or "task",
                section=section or "daily",
                week=week or None,
                month=month or None,
            )
            return {"ok": True, "bullets": bullets, "section": section or "daily"}
        except ValueError as e:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(e)})

    @app.post("/api/journal/bullet/{bullet_id}/promote")
    def journal_bullet_promote(bullet_id: str):
        try:
            result = journal.promote_to_planner(bullet_id)
            return result
        except ValueError as e:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(e)})

    @app.delete("/api/journal/bullet/{bullet_id}/promote")
    def journal_bullet_unlink_planner(bullet_id: str):
        try:
            return journal.unlink_planner(bullet_id)
        except ValueError as e:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(e)})

    @app.post("/api/journal/assist/reflect")
    async def journal_assist_reflect(scope: str = Form("today")):
        from jarvis.journal_services import reflect_assistant

        return reflect_assistant(journal, scope)

    @app.get("/api/journal/assist/promote")
    def journal_assist_promote():
        from jarvis.journal_services import promotion_assistant

        return promotion_assistant(journal)

    @app.get("/api/journal/assist/migrate")
    def journal_assist_migrate(scope: str = "daily"):
        from jarvis.journal_services import migration_assistant

        return migration_assistant(journal, scope)

    @app.get("/api/journal/assist/memory")
    def journal_assist_memory(q: str = ""):
        from jarvis.journal_services import memory_surface

        return memory_surface(journal, q)

    @app.post("/api/journal/assist/writing")
    async def journal_assist_writing(text: str = Form(...), mode: str = Form("organize")):
        from jarvis.journal_services import writing_assistant

        return writing_assistant(text, mode)

    @app.post("/api/journal/assist/voice")
    async def journal_assist_voice(transcript: str = Form(...)):
        from jarvis.journal_services import parse_voice_rapid_log

        return parse_voice_rapid_log(transcript)

    @app.post("/api/journal/assist/vision")
    async def journal_assist_vision(
        ocr_text: str = Form(""),
        path: str = Form(""),
        source: str = Form("scan"),
        section: str = Form("daily"),
    ):
        from jarvis.journal_services import vision_import_preview

        return vision_import_preview(ocr_text=ocr_text, path=path, source=source, section=section)

    @app.get("/api/journal/wizard/month-end")
    def journal_month_end_wizard(month: str = ""):
        from jarvis.journal_services import month_end_wizard
        from jarvis.modules.journal import _month_key

        return month_end_wizard(journal, month or _month_key())

    @app.post("/api/journal/backup")
    def journal_backup():
        from jarvis.journal_services import create_backup

        return create_backup(journal)

    @app.get("/api/journal/collections/presets")
    def journal_collection_presets():
        from jarvis.journal_presets import list_presets

        return {"ok": True, "presets": list_presets(journal.collection_list())}

    @app.post("/api/journal/collections/preset")
    async def journal_collection_from_preset(preset_id: str = Form(...)):
        from jarvis.journal_presets import preset_by_id

        preset = preset_by_id(preset_id)
        if not preset:
            return JSONResponse(status_code=404, content={"ok": False, "error": "unknown preset"})
        col = journal.collection_create(preset["name"], preset["description"])
        return {"ok": True, "collection": col, "created": col.get("bullets") == []}

    @app.get("/api/journal/collections")
    def journal_collections():
        from jarvis.journal_presets import list_presets

        return {
            "names": journal.collection_list(),
            "data": journal._data.get("collections", {}),
            "presets": list_presets(journal.collection_list()),
        }

    @app.post("/api/journal/collections")
    async def journal_collection_create(name: str = Form(...), description: str = Form("")):
        return {"ok": True, "collection": journal.collection_create(name, description)}

    @app.post("/api/journal/collections/{name}/add")
    async def journal_collection_add(
        name: str, content: str = Form(...), bullet_type: str = Form("task")
    ):
        return {"ok": True, "bullet": journal.collection_add(name, content, bullet_type)}

    @app.patch("/api/journal/bullet/{bullet_id}")
    async def journal_bullet_update(bullet_id: str, request: Request):
        # Owner UI posts multipart/form-data; also accept JSON so API clients
        # do not get a silent no-op success when Content-Type is application/json.
        content = ""
        status = ""
        bullet_type = ""
        ctype = (request.headers.get("content-type") or "").lower()
        if "application/json" in ctype:
            body = await request.json()
            if not isinstance(body, dict):
                body = {}
            content = str(body.get("content") or body.get("text") or "")
            status = str(body.get("status") or "")
            bullet_type = str(body.get("bullet_type") or body.get("type") or "")
        else:
            form = await request.form()
            content = str(form.get("content") or "")
            status = str(form.get("status") or "")
            bullet_type = str(form.get("bullet_type") or "")
        kw = {}
        if content:
            kw["content"] = content
        if status:
            kw["status"] = status
        if bullet_type:
            kw["bullet_type"] = bullet_type
        if not kw:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": "No updatable fields provided"},
            )
        b = journal.bullet_update(bullet_id, **kw)
        if not b:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "bullet": b}

    @app.post("/api/journal/bullet/{bullet_id}/complete")
    def journal_bullet_complete(bullet_id: str):
        b = journal.bullet_complete(bullet_id)
        return {"ok": bool(b), "bullet": b}

    @app.post("/api/journal/bullet/{bullet_id}/migrate")
    async def journal_bullet_migrate(bullet_id: str, target: str = Form(...)):
        b = journal.bullet_migrate(bullet_id, target)
        return {"ok": bool(b), "bullet": b}

    @app.delete("/api/journal/bullet/{bullet_id}")
    def journal_bullet_delete(bullet_id: str):
        return {"ok": journal.bullet_delete(bullet_id)}

    @app.post("/api/journal/migrate-month")
    async def journal_migrate_month(
        from_month: str = Form(...),
        to_month: str = Form(...),
        dest: str = Form("monthly"),
    ):
        return {"ok": True, **journal.migrate_month(from_month, to_month, dest=dest or "monthly")}

    @app.post("/api/journal/reflect")
    async def journal_reflect(scope: str = Form("week")):
        text = journal.ai_reflect(scope)
        return {"ok": True, "reflection": text}

    @app.get("/api/journal/search")
    def journal_search(q: str):
        return {"results": journal.search(q)}

    @app.get("/api/journal/stats")
    def journal_stats():
        return {"ok": True, "stats": journal.stats()}

    @app.get("/api/journal/export")
    def journal_export():
        return journal.export_all()

    @app.post("/api/journal/export/encrypted")
    async def journal_export_encrypted(password: str = Form(...)):
        from jarvis.journal_crypto import encrypt_export

        try:
            payload = encrypt_export(journal.export_all(), password)
            return {"ok": True, "export": payload}
        except ValueError as e:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(e)})
        except RuntimeError as e:
            return JSONResponse(status_code=501, content={"ok": False, "message": str(e)})

    @app.post("/api/journal/import/encrypted")
    async def journal_import_encrypted(request: Request):
        from jarvis.journal_crypto import decrypt_import

        body = await request.json()
        password = str(body.get("password", ""))
        merge = body.get("merge", True) is not False
        if not merge and str(body.get("confirm_wipe", "")).lower() not in ("1", "true", "yes"):
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "message": "Non-merge import wipes journal data. Set confirm_wipe=true to proceed.",
                },
            )
        # Prefer body["export"] (UI contract). Fall back to body for raw envelope POSTs.
        # decrypt_import normalizes accidental {ok, export: envelope} wrappers.
        envelope = body["export"] if isinstance(body.get("export"), (dict, str, bytes)) else body
        try:
            payload = decrypt_import(envelope, password)
        except ValueError as e:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(e)})
        except RuntimeError as e:
            return JSONResponse(status_code=501, content={"ok": False, "message": str(e)})
        if not merge:
            journal.import_all(payload)
            return {"ok": True, "merged": False}
        current = journal.export_all()
        for key in (
            "index",
            "future_log",
            "monthly_log",
            "daily_log",
            "weekly_log",
            "collections",
            "habits",
            "page_counter",
        ):
            if key in payload:
                current[key] = payload[key]
        journal.import_all(current)
        return {"ok": True, "merged": True}

    @app.post("/api/journal/import")
    async def journal_import(request: Request):
        body = await request.json()
        merge = body.get("merge", True) is not False
        if not merge and str(body.get("confirm_wipe", "")).lower() not in ("1", "true", "yes"):
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "message": "Non-merge import wipes journal data. Set confirm_wipe=true to proceed.",
                },
            )
        payload = {k: v for k, v in body.items() if k not in ("merge", "password", "confirm_wipe")}
        if not merge:
            journal.import_all(payload)
            return {"ok": True, "merged": False}
        current = journal.export_all()
        for key in (
            "index",
            "future_log",
            "monthly_log",
            "daily_log",
            "weekly_log",
            "collections",
            "habits",
            "page_counter",
        ):
            if key in payload:
                current[key] = payload[key]
        journal.import_all(current)
        return {"ok": True, "merged": True}

    @app.get("/api/journal/weekly")
    def journal_weekly(week: str = ""):
        from jarvis.modules.journal import _week_key

        return journal.weekly_get(week or _week_key())

    @app.post("/api/journal/weekly")
    async def journal_weekly_add(
        content: str = Form(...),
        bullet_type: str = Form("task"),
        week: str = Form(""),
    ):

        return {"ok": True, "bullet": journal.weekly_add(content, bullet_type, week=week or None)}

    @app.get("/api/journal/habits")
    def journal_habits(month: str = ""):
        from jarvis.modules.journal import _month_key

        return journal.habit_tracker(month or _month_key())

    @app.post("/api/journal/habits")
    async def journal_habit_create(name: str = Form(...)):
        return {"ok": True, "habit": journal.habit_create(name)}

    @app.post("/api/journal/habits/{habit_id}/toggle")
    async def journal_habit_toggle(habit_id: str, day: str = Form("")):
        from jarvis.modules.journal import _today

        h = journal.habit_toggle(habit_id, day or _today())
        if not h:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "habit": h}

    @app.post("/api/journal/daily/prompts")
    async def journal_daily_prompts(
        day: str = Form(...),
        morning: str = Form(""),
        evening: str = Form(""),
    ):
        page = journal.daily_set_prompts(day, morning=morning, evening=evening)
        return {"ok": True, "prompts": page.get("prompts", {})}

    @app.post("/api/journal/daily/photo")
    async def journal_daily_photo(
        day: str = Form(...),
        caption: str = Form(""),
        file: UploadFile = File(...),
    ):
        content = await file.read()
        if not content:
            return JSONResponse(status_code=400, content={"ok": False, "error": "empty file"})
        entry = journal.daily_add_photo(day, file.filename or "photo.jpg", content, caption)
        return {"ok": True, "photo": entry}

    @app.delete("/api/journal/daily/{day}/photo/{photo_id}")
    def journal_daily_photo_delete(day: str, photo_id: str):
        return {"ok": journal.daily_delete_photo(day, photo_id)}

    @app.get("/api/journal/photos/{filename}")
    def journal_photo_file(filename: str):
        fp = journal.photo_path(filename)
        if not fp:
            return JSONResponse(status_code=404, content={"ok": False})
        return FileResponse(fp)

    @app.post("/api/journal/monthly/calendar-note")
    async def journal_calendar_note(
        day: int = Form(...),
        note: str = Form(""),
        month: str = Form(""),
    ):
        from jarvis.modules.journal import _month_key

        page = journal.monthly_calendar_note(day, note, month or _month_key())
        return {"ok": True, "calendar_notes": page.get("calendar_notes", {})}

    @app.post("/api/journal/bullet/{bullet_id}/remember")
    def journal_bullet_remember(bullet_id: str):
        text = journal.bullet_remember_text(bullet_id)
        if not text:
            return JSONResponse(status_code=404, content={"ok": False, "error": "bullet not found"})
        from jarvis.memory_services import propose_candidate

        ns = assistant.session.memory_namespace or "default"
        result = propose_candidate(
            text,
            source="journal",
            entry_type="note",
            namespace=ns,
            tags=["journal", f"bullet:{bullet_id}"],
            evidence=f"Journal bullet {bullet_id}",
            confidence=0.7,
        )
        return {
            "ok": True,
            "candidate": True,
            "requires_confirmation": True,
            "text": text,
            "namespace": ns,
            **result,
            "message": "Staged as a Memory Candidate — open Memory Home to Adopt.",
        }

    @app.get("/api/journal/print")
    def journal_print_html(month: str = ""):
        from jarvis.journal_export import month_print_html
        from jarvis.modules.journal import _month_key

        html = month_print_html(journal, month or _month_key())
        return HTMLResponse(html)

    @app.get("/api/journal/projects")
    def journal_projects_list():
        from jarvis.project_journal import list_projects

        return {"ok": True, "projects": list_projects()}

    @app.get("/api/journal/projects/{slug}")
    def journal_projects_page(slug: str, day: str = ""):
        from jarvis.modules.journal import _today
        from jarvis.project_journal import ProjectJournal

        store = ProjectJournal(slug)
        store.ensure()
        d = (day or "").strip() or _today()
        page = store.daily_get(d)
        return {
            "ok": True,
            "project": store.data.get("title") or store.slug,
            "slug": store.slug,
            "day": d,
            "page": page,
        }

    @app.post("/api/journal/projects/{slug}/log")
    async def journal_projects_log(slug: str, request: Request):
        from jarvis.modules.journal import _today
        from jarvis.project_journal import ProjectJournal

        body = await request.json()
        text = str(body.get("text") or "").strip()
        if not text:
            return JSONResponse(status_code=400, content={"ok": False, "error": "text required"})
        bullet_type = str(body.get("bullet_type") or "note")
        day = str(body.get("day") or "").strip() or _today()
        store = ProjectJournal(slug)
        store.ensure()
        bullet = store.daily_add(text, bullet_type=bullet_type, day=day)
        return {"ok": True, "bullet": bullet, "slug": store.slug, "day": day}

    @app.post("/api/journal/projects/{slug}/learn")
    async def journal_projects_learn(slug: str, request: Request):
        from jarvis.journal_learning import learn_from_project_journal
        from jarvis.modules.journal import _today

        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        day = str((body or {}).get("day") or "").strip() or _today()
        result = learn_from_project_journal(
            assistant.memory, slug, day=day, namespace=slug
        )
        return {"ok": True, "day": day, "slug": slug, **(result if isinstance(result, dict) else {})}

    @app.get("/api/journal/export/pdf")
    def journal_export_pdf(month: str = ""):
        from jarvis.journal_export import export_month_pdf
        from jarvis.modules.journal import _month_key

        mk = month or _month_key()
        dest = DATA_DIR / "exports" / f"journal-{mk}.pdf"
        try:
            export_month_pdf(journal, dest, mk)
        except RuntimeError as e:
            return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})
        return FileResponse(dest, filename=dest.name, media_type="application/pdf")

    @app.get("/api/actions")
    def actions_list(module: str = "", limit: int = 50):
        return {"actions": list_actions(limit=min(limit, 100), module=module)}

    @app.post("/api/actions/clear")
    def actions_clear():
        clear_log()
        return {"ok": True}

    @app.get("/api/chat/export")
    def chat_export(branch_id: str = "", memory: int = 0):
        bid = branch_id.strip() or assistant.branches.active_id
        from jarvis.assistant import display_chat_user_content
        from jarvis.config import build_system_prompt, load_personality_preset
        from jarvis.movie_tiers import export_chat_with_memory

        conv = assistant.branches.get_conversation(
            bid, build_system_prompt(load_personality_preset(), assistant.memory)
        )
        name = assistant.branches.branch_name(bid)
        safe = re.sub(r"[^\w\-]+", "-", name).strip("-") or bid
        msgs = [m for m in conv.messages if m.get("role") != "system"]
        memory_hits = None
        if memory:
            memory_hits = (
                assistant.memory.search("", limit=8) if hasattr(assistant.memory, "search") else []
            )
        if memory:
            body = export_chat_with_memory(msgs, branch_name=name, memory_hits=memory_hits)
        else:
            lines = [f"# Jarvis Chat — {name}\n", f"_Branch `{bid}`_\n"]
            for m in msgs:
                role = m.get("role", "?")
                content = m.get("content", "")
                if role == "user":
                    content = display_chat_user_content(content)
                lines.append(f"## {role.capitalize()}\n\n{content}\n")
            body = "\n".join(lines)
        return PlainTextResponse(
            body,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="jarvis-chat-{safe}.md"'},
        )

    @app.post("/api/branches/fork")
    async def branches_fork(name: str = Form("Fork"), display_index: int = Form(0)):
        bid = assistant.fork_branch(name, int(display_index))
        return {"ok": True, "branch_id": bid, "active": bid}

    @app.get("/api/branches")
    def branches_list():
        return {
            "active": assistant.branches.active_id,
            "branches": assistant.branches.list_branches(),
        }

    @app.post("/api/branches")
    async def branches_create(name: str = Form("Branch"), from_index: str = Form("")):
        idx = int(from_index) if from_index.strip().isdigit() else None
        bid = assistant.create_branch(name, from_index=idx)
        return {"ok": True, "branch_id": bid, "active": bid}

    @app.post("/api/branches/switch")
    async def branches_switch(branch_id: str = Form(...)):
        ok = assistant.switch_branch(branch_id)
        if not ok:
            return JSONResponse(
                status_code=404, content={"ok": False, "message": "Branch not found"}
            )
        return {"ok": True, "active": branch_id}

    @app.post("/api/branches/delete")
    async def branches_delete(branch_ids: str = Form(...)):
        ids = [p.strip() for p in branch_ids.split(",") if p.strip()]
        result = assistant.delete_branches(ids)
        if not result["deleted"]:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": "No branches deleted (main is protected)."},
            )
        return {"ok": True, **result}

    @app.post("/api/branches/clear")
    async def branches_clear_form(branch_id: str = Form("main")):
        """Clear chat history for a branch without switching the active branch."""
        result = assistant.clear_branch_messages(branch_id.strip() or "main")
        if not result.get("ok"):
            return JSONResponse(status_code=400, content=result)
        return result

    @app.post("/api/branches/{branch_id}/clear")
    async def branches_clear(branch_id: str):
        result = assistant.clear_branch_messages(branch_id.strip())
        if not result.get("ok"):
            return JSONResponse(status_code=400, content=result)
        return result

    @app.get("/api/branches/{branch_id}/messages")
    def branch_messages(branch_id: str):
        from jarvis.assistant import display_chat_user_content
        from jarvis.config import build_system_prompt, load_personality_preset

        conv = assistant.branches.get_conversation(
            branch_id, build_system_prompt(load_personality_preset(), assistant.memory)
        )
        out = []
        for m in conv.messages:
            if m.get("role") not in ("user", "assistant"):
                continue
            content = m.get("content", "")
            if m.get("role") == "user":
                content = display_chat_user_content(content)
            out.append({"role": m["role"], "content": content})
        return {"messages": out}

    _IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

    @app.get("/api/gallery")
    def gallery_list(
        offset: int = 0,
        limit: int = 48,
        q: str = "",
        sort: str = "newest",
        include_artifacts: bool = False,
        favorites: bool = False,
        project: str = "",
    ):
        """Gallery library — paginated stills (artifacts excluded by default)."""
        from jarvis.gallery_product.library import list_images

        # Short cache only for default unfiltered first page
        if not q and not favorites and not project and offset == 0 and not include_artifacts:
            cached = get_gallery_cache()
            if cached is not None:
                return {"images": cached[:limit], "total": len(cached), "offset": 0, "limit": limit, "ok": True}
        result = list_images(
            offset=offset,
            limit=limit,
            query=q,
            sort=sort,
            include_artifacts=include_artifacts,
            project=project,
            favorites_only=favorites,
        )
        if not q and not favorites and not project and offset == 0 and not include_artifacts:
            set_gallery_cache(result.get("images") or [])
        return result

    @app.get("/api/gallery/{name}")
    def gallery_file(name: str, max: int = 0, reveal: bool = False):
        from jarvis.gallery_product.visibility import is_restricted_for_viewer

        generated = (DATA_DIR / "generated").resolve()
        path = (generated / Path(name).name).resolve()
        if (
            generated not in path.parents
            or not path.exists()
            or path.suffix.lower() not in _IMAGE_EXTS
        ):
            return JSONResponse(status_code=404, content={"detail": "not found"})
        # Profile-appropriate presentation: censored viewers get placeholder, not the asset
        if is_restricted_for_viewer(name) and not reveal:
            from jarvis.config import is_uncensored

            if not is_uncensored():
                svg = (
                    "<svg xmlns='http://www.w3.org/2000/svg' width='384' height='384'>"
                    "<rect width='100%' height='100%' fill='#1a1a1a'/>"
                    "<text x='50%' y='50%' fill='#aaa' font-size='16' text-anchor='middle' "
                    "dominant-baseline='middle' font-family='sans-serif'>Restricted</text></svg>"
                )
                from fastapi.responses import Response as FastResponse

                return FastResponse(content=svg.encode("utf-8"), media_type="image/svg+xml")
        if max and max > 0:
            try:
                import io

                from fastapi.responses import Response
                from PIL import Image

                cap = min(int(max), 1536)
                with Image.open(path) as im:
                    rgb = im.convert("RGB")
                    rgb.thumbnail((cap, cap), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    rgb.save(buf, format="PNG", optimize=True)
                return Response(content=buf.getvalue(), media_type="image/png")
            except Exception:
                pass
        return FileResponse(path)

    @app.delete("/api/gallery/{name}")
    def gallery_delete(name: str, permanent: bool = False):
        generated = (DATA_DIR / "generated").resolve()
        path = (generated / Path(name).name).resolve()
        if generated not in path.parents or not path.is_file():
            return JSONResponse(status_code=404, content={"ok": False, "message": "Not found"})
        if path.suffix.lower() not in _IMAGE_EXTS:
            return JSONResponse(status_code=400, content={"ok": False, "message": "Not an image"})
        if permanent:
            path.unlink(missing_ok=False)
            invalidate_gallery()
            try:
                from jarvis.gallery_product.consistency import on_gallery_asset_removed

                on_gallery_asset_removed(path.name, path=str(path))
            except Exception:
                pass
            return {"ok": True, "deleted": path.name, "permanent": True}
        from jarvis.gallery_product.soft_delete import soft_delete

        return soft_delete(path)

    _VIDEO_EXTS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"}
    _VIDEO_MEDIA = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
        ".avi": "video/x-msvideo",
        ".m4v": "video/mp4",
    }

    @app.get("/api/video-gallery")
    @app.get("/api/video/gallery")
    def video_gallery_list():
        cached = get_video_gallery_cache()
        if cached is not None:
            videos = cached
        else:
            from jarvis.video_ops import list_videos

            videos = list_videos(50)
            set_video_gallery_cache(videos)
        try:
            from jarvis.video_generation.metadata import apply_visibility

            videos = [apply_visibility(dict(v) if isinstance(v, dict) else {"name": v}) for v in videos]
        except Exception:
            pass
        return {"videos": videos}

    @app.get("/api/video-gallery/{name}")
    def video_gallery_file(name: str):
        from jarvis.video_ops import VIDEO_OUTPUT_DIR, VIDEO_UPLOAD_DIR, ensure_webm

        safe = Path(name).name
        try:
            from jarvis.video_generation.metadata import is_restricted_for_viewer

            if is_restricted_for_viewer(safe):
                # Serve placeholder — do not expose restricted media
                from jarvis.config import DATA_DIR

                placeholder = DATA_DIR / "gallery_product" / "restricted_placeholder.png"
                if placeholder.is_file():
                    return FileResponse(placeholder, media_type="image/png")
                return JSONResponse(
                    status_code=403,
                    content={"ok": False, "restricted": True, "message": "Restricted video"},
                )
        except Exception:
            # Fail closed: never serve the asset if restriction check cannot run
            return JSONResponse(
                status_code=403,
                content={"ok": False, "restricted": True, "message": "Restricted video (check failed)"},
            )
        for root in (VIDEO_OUTPUT_DIR, VIDEO_UPLOAD_DIR):
            path = (root / safe).resolve()
            if (
                root.resolve() in path.parents
                and path.is_file()
                and path.suffix.lower() in _VIDEO_EXTS
            ):
                media = _VIDEO_MEDIA.get(path.suffix.lower(), "video/mp4")
                return FileResponse(path, media_type=media)
            if safe.lower().endswith(".webm"):
                mp4_path = (root / f"{safe[:-5]}.mp4").resolve()
                if root.resolve() in mp4_path.parents and mp4_path.is_file():
                    webm = ensure_webm(mp4_path)
                    if not str(webm).startswith("ERROR:"):
                        return FileResponse(Path(webm), media_type="video/webm")
        return JSONResponse(status_code=404, content={"detail": "not found"})

    @app.delete("/api/video-gallery/{name}")
    def video_gallery_delete(name: str):
        from jarvis.video_ops import VIDEO_OUTPUT_DIR, VIDEO_UPLOAD_DIR

        safe = Path(name).name
        if not safe or safe in (".", ".."):
            return JSONResponse(status_code=400, content={"ok": False, "message": "Invalid name"})
        for root in (VIDEO_OUTPUT_DIR, VIDEO_UPLOAD_DIR):
            path = (root / safe).resolve()
            try:
                if root.resolve() not in path.parents:
                    continue
            except (OSError, ValueError):
                continue
            if path.is_file() and path.suffix.lower() in _VIDEO_EXTS:
                try:
                    path.unlink()
                except OSError as exc:
                    return JSONResponse(status_code=500, content={"ok": False, "message": str(exc)})
                invalidate_video_gallery()
                return {"ok": True, "deleted": path.name}
        return JSONResponse(status_code=404, content={"ok": False, "message": "Not found"})

    _MEME_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

    @app.get("/api/meme-gallery")
    def meme_gallery_list():
        from jarvis.cache_state import get_meme_gallery_cache, set_meme_gallery_cache
        from jarvis.meme_ops import list_memes

        cached = get_meme_gallery_cache()
        if cached is not None:
            return {"memes": cached}
        memes = list_memes(50)
        set_meme_gallery_cache(memes)
        return {"memes": memes}

    @app.get("/api/meme-gallery/{name}")
    def meme_gallery_file(name: str):
        meme_dir = (DATA_DIR / "generated" / "memes").resolve()
        path = (meme_dir / Path(name).name).resolve()
        if meme_dir not in path.parents or not path.is_file():
            return JSONResponse(status_code=404, content={"detail": "not found"})
        if path.suffix.lower() not in _MEME_EXTS:
            return JSONResponse(status_code=404, content={"detail": "not found"})
        return FileResponse(path)

    @app.delete("/api/meme-gallery/{name}")
    def meme_gallery_delete(name: str):
        from jarvis.cache_state import invalidate_meme_gallery

        meme_dir = (DATA_DIR / "generated" / "memes").resolve()
        path = (meme_dir / Path(name).name).resolve()
        if meme_dir not in path.parents or not path.is_file():
            return JSONResponse(status_code=404, content={"ok": False, "message": "Not found"})
        if path.suffix.lower() not in _MEME_EXTS:
            return JSONResponse(status_code=400, content={"ok": False, "message": "Not an image"})
        path.unlink(missing_ok=False)
        invalidate_meme_gallery()
        return {"ok": True, "deleted": path.name}

    @app.get("/api/uploads/{name}")
    def upload_file(name: str):
        upload_dir = (DATA_DIR / "uploads").resolve()
        path = (upload_dir / Path(name).name).resolve()
        if upload_dir not in path.parents or not path.exists():
            return JSONResponse(status_code=404, content={"detail": "not found"})
        if path.suffix.lower() not in _IMAGE_EXTS:
            return JSONResponse(status_code=404, content={"detail": "not found"})
        return FileResponse(path)

    @app.get("/api/audio/file")
    def audio_file(path: str):
        from jarvis.modules.audio import AUDIO_LIBRARY_DIRS
        from jarvis.music_gen import MUSIC_DIR
        from jarvis.song_studio import SONGS_DIR

        allowed_roots = [
            *(d.resolve() for d in AUDIO_LIBRARY_DIRS.values()),
            MUSIC_DIR.resolve(),
            SONGS_DIR.resolve(),
        ]
        try:
            p = Path(path).expanduser().resolve()
        except OSError:
            return JSONResponse(status_code=400, content={"detail": "invalid path"})
        data_root = DATA_DIR.resolve()
        if data_root not in p.parents and p != data_root:
            return JSONResponse(status_code=404, content={"detail": "not found"})
        if not p.is_file():
            return JSONResponse(status_code=404, content={"detail": "not found"})
        if not any((p == root or root in p.parents) for root in allowed_roots):
            return JSONResponse(status_code=404, content={"detail": "not found"})
        media = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".ogg": "audio/ogg",
            ".flac": "audio/flac",
            ".webm": "audio/webm",
            ".m4a": "audio/mp4",
        }.get(p.suffix.lower(), "application/octet-stream")
        return FileResponse(p, media_type=media)

    @app.get("/api/personality")
    def get_personality():
        from jarvis.config import load_personality_preset

        return {"ok": True, "personality": load_personality_preset()}

    @app.post("/api/personality")
    async def set_personality(preset: str = Form("default")):
        from jarvis.config import PERSONALITIES, save_personality_preset

        preset = preset if preset in PERSONALITIES else "default"
        save_personality_preset(preset)
        assistant.refresh_system_prompt()
        assistant.branches.persist(session=assistant.session)
        return {"ok": True, "personality": preset}

    @app.get("/api/git/status")
    def git_status():
        from jarvis import git_util

        return {"status": git_util.status()}

    @app.get("/api/git/diff")
    def git_diff(file: str = ""):
        from jarvis import git_util

        return {"diff": git_util.diff(file=file or None)}

    @app.post("/api/undo-apply")
    def undo_apply():
        from jarvis.assistant import perform_undo_apply

        result = perform_undo_apply(assistant)
        status = 400 if not result.get("ok") else 200
        return JSONResponse(status_code=status, content=result)

    @app.post("/api/rag/reindex")
    def rag_reindex():
        from jarvis import rag

        chunks = rag.build_index()
        return {"ok": True, "chunks": len(chunks)}

    # --- Coding Tier 3 / Cursor bridge ---

    @app.get("/api/coding/tasks")
    def coding_tasks_list():
        tasks = assistant.task_manager.list_tasks()
        return {"tasks": [t.to_dict() for t in tasks]}

    @app.get("/api/coding/tasks/{task_id}")
    def coding_task_get(task_id: str):
        t = assistant.task_manager.get(task_id)
        if not t:
            return JSONResponse(status_code=404, content={"ok": False, "message": "Task not found"})
        return t.to_dict()

    @app.post("/api/coding/tasks/{task_id}/pause")
    def coding_task_pause(task_id: str):
        t = assistant.task_manager.pause(task_id)
        if not t:
            return JSONResponse(status_code=404, content={"ok": False})
        return {"ok": True, "task": t.to_dict()}

    @app.post("/api/coding/tasks/{task_id}/resume")
    def coding_task_resume(task_id: str):
        t = assistant.task_manager.get(task_id)
        if not t:
            return JSONResponse(status_code=404, content={"ok": False, "message": "Task not found"})
        assistant.task_manager.resume(task_id)
        checkpoint = t.checkpoint
        result = assistant._coding_agent(
            {
                "task": checkpoint.get("task") or t.title,
                "path": t.path,
                "mode": t.mode,
                "task_id": task_id,
            },
            checkpoint.get("task") or t.title,
        )
        return {"ok": result.get("ok", False), "task": t.to_dict(), "result": result}

    @app.get("/api/coding/syntax")
    def coding_syntax(path: str, deep: str = "true"):
        from jarvis.cursor_bridge import check_syntax

        return check_syntax(path, assistant.coding._base())

    @app.get("/api/coding/context")
    def coding_context(path: str, task: str = ""):
        from jarvis.cursor_bridge import get_file_context

        return get_file_context(path, assistant.coding._base(), task=task)

    @app.get("/api/coding/search")
    def coding_semantic_search(q: str = "", limit: int = 8):
        from jarvis.cursor_bridge import search_codebase

        return {"results": search_codebase(q, limit=limit)}

    @app.get("/api/coding/runner")
    def coding_runner_info():
        from jarvis.project_runner import runner_info

        return runner_info(assistant.coding._base())

    @app.post("/api/editor/context")
    async def editor_context_post(request: Request):
        from jarvis.editor_context import save_context

        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(status_code=400, content={"ok": False, "message": "Invalid JSON"})
        if not isinstance(payload, dict):
            return JSONResponse(
                status_code=400, content={"ok": False, "message": "Expected object"}
            )
        ctx = save_context(payload)
        if ctx.relative_file:
            assistant.session.note_file(ctx.relative_file)
        return {"ok": True, "file": ctx.relative_file, "has_selection": ctx.has_selection()}

    @app.get("/api/editor/context")
    def editor_context_get():
        from jarvis.editor_context import get_context, load_context

        ctx = load_context()
        fresh = get_context()
        sel_lines = ctx.selection_line_count() if ctx.has_selection() else 0
        return {
            "ok": True,
            "fresh": fresh is not None,
            "context": {
                "relative_file": ctx.relative_file,
                "language": ctx.language,
                "has_selection": ctx.has_selection(),
                "selection_lines": sel_lines,
                "cursor_line": ctx.cursor_line,
                "open_files": ctx.open_files,
                "updated_at": ctx.updated_at,
            },
        }

    @app.get("/api/coding/tools")
    def coding_tools():
        from jarvis.lsp import tools_status
        from jarvis.syntax_check import available_tools

        return {**available_tools(), **tools_status()}

    @app.get("/api/lsp/status")
    def lsp_status_route():
        from jarvis.lsp_bridge import lsp_status

        return {"ok": True, **lsp_status()}

    @app.get("/api/lsp/diagnostics")
    def lsp_diagnostics_route(path: str, deep: str = "false"):
        from jarvis.lsp_bridge import lsp_diagnostics

        d = deep.lower() in ("1", "true", "yes")
        return lsp_diagnostics(path, assistant.coding._base(), deep=d)

    @app.get("/api/lsp/definition")
    def lsp_definition_route(path: str, line: int = 1, column: int = 1):
        from jarvis.lsp_bridge import lsp_definition

        return lsp_definition(path, assistant.coding._base(), line, column)

    @app.get("/api/lsp/references")
    def lsp_references_route(path: str, line: int = 1, column: int = 1):
        from jarvis.lsp_bridge import lsp_references

        return lsp_references(path, assistant.coding._base(), line, column)

    @app.get("/api/lsp/hover")
    def lsp_hover_route(path: str, line: int = 1, column: int = 1):
        from jarvis.lsp_bridge import lsp_hover

        return lsp_hover(path, assistant.coding._base(), line, column)

    @app.get("/api/lsp/completion")
    def lsp_completion_route(path: str, line: int = 1, column: int = 1):
        from jarvis.lsp_bridge import lsp_completion

        return lsp_completion(path, assistant.coding._base(), line, column)

    @app.get("/api/lsp/symbols")
    def lsp_symbols_route(path: str):
        from jarvis.lsp_bridge import lsp_symbols

        return lsp_symbols(path, assistant.coding._base())

    @app.post("/api/lsp/format")
    async def lsp_format_route(path: str = Form(...), write: str = Form("1")):
        from jarvis.lsp_bridge import lsp_format

        do_write = write.lower() not in ("0", "false", "no")
        return lsp_format(path, assistant.coding._base(), write=do_write)

    @app.post("/api/code/reindex")
    def code_reindex():
        from jarvis.code_index import build_index, invalidate_cache

        invalidate_cache()
        chunks = build_index(assistant.coding._base())
        return {"ok": True, "chunks": len(chunks)}

    @app.get("/api/profiles")
    def profiles_list():
        from jarvis.profiles import list_profiles

        return {"profiles": list_profiles()}

    @app.post("/api/profiles/switch")
    async def profiles_switch(request: Request):
        from jarvis.profiles import apply_profile

        body = await request.json()
        pid = (body.get("profile") or body.get("id") or "").strip()
        try:
            result = apply_profile(pid)
            assistant.refresh_system_prompt()
            return result
        except ValueError as e:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(e)})

    @app.get("/api/prompts")
    def prompts_list(favorites: bool = False, limit: int = 50):
        from jarvis.prompt_history import list_entries

        return {"prompts": list_entries(favorites_only=favorites, limit=limit)}

    @app.post("/api/prompts/{entry_id}/favorite")
    def prompts_favorite(entry_id: str):
        from jarvis.prompt_history import toggle_favorite

        entry = toggle_favorite(entry_id)
        if not entry:
            return JSONResponse(status_code=404, content={"ok": False, "message": "Not found"})
        return {"ok": True, "entry": entry}

    @app.delete("/api/prompts/{entry_id}")
    def prompts_delete(entry_id: str):
        from jarvis.prompt_history import delete_entry

        removed = delete_entry(entry_id)
        if removed is None:
            return JSONResponse(status_code=404, content={"ok": False, "message": "Not found"})
        return {"ok": True, "deleted": entry_id, "entry": removed}

    @app.post("/api/prompts/restore")
    async def prompts_restore(request: Request):
        from jarvis.prompt_history import restore_entry

        body = await request.json()
        entry = body.get("entry") if isinstance(body, dict) else None
        restored = restore_entry(entry or {})
        if restored is None:
            return JSONResponse(status_code=400, content={"ok": False, "message": "Nothing to restore"})
        return {"ok": True, "entry": restored}

    @app.get("/api/git/log")
    def git_log(limit: int = 10):
        from jarvis import git_util

        return {"log": git_util.log_oneline(limit=limit)}

    @app.post("/api/admin/backup")
    async def admin_backup(request: Request):
        import subprocess

        try:
            body = await request.json()
        except Exception:
            body = {}
        want_async = bool(body.get("async")) if isinstance(body, dict) else False

        script = Path(__file__).resolve().parent.parent.parent / "scripts" / "backup-data.sh"
        if not script.exists():
            return JSONResponse(
                status_code=500, content={"ok": False, "message": "backup script missing"}
            )

        def _run_backup() -> dict:
            proc = subprocess.run([str(script)], capture_output=True, text=True, timeout=120)
            if proc.returncode != 0:
                return {"ok": False, "message": proc.stderr or proc.stdout}
            return {"ok": True, "message": (proc.stdout or "").strip()}

        if want_async:
            from jarvis.coding_jobs import submit

            job_id = submit("admin backup", _run_backup)
            return {"ok": True, "pending": True, "job_id": job_id}

        result = _run_backup()
        if not result.get("ok"):
            return JSONResponse(status_code=500, content=result)
        return result

    @app.get("/api/chat/export/pdf")
    def chat_export_pdf(branch_id: str = ""):
        bid = branch_id.strip() or assistant.branches.active_id
        from jarvis.assistant import display_chat_user_content
        from jarvis.config import build_system_prompt, load_personality_preset

        conv = assistant.branches.get_conversation(
            bid, build_system_prompt(load_personality_preset(), assistant.memory)
        )
        name = assistant.branches.branch_name(bid)
        safe = re.sub(r"[^\w\-]+", "-", name).strip("-") or bid
        parts = [
            f"<h1>Jarvis Chat — {html.escape(name)}</h1>",
            f"<p><em>Branch {html.escape(bid)}</em></p>",
        ]
        for m in conv.messages:
            role = m.get("role", "?")
            if role == "system":
                continue
            content = m.get("content", "")
            if role == "user":
                content = display_chat_user_content(content)
            parts.append(f"<h2>{html.escape(role.capitalize())}</h2>")
            parts.append(f"<pre>{html.escape(content)}</pre>")
        html_doc = f"<!DOCTYPE html><html><body>{''.join(parts)}</body></html>"
        try:
            from weasyprint import HTML
        except ImportError:
            return JSONResponse(
                status_code=501,
                content={"ok": False, "message": "Install weasyprint for PDF export"},
            )
        pdf_bytes = HTML(string=html_doc).write_pdf()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="jarvis-chat-{safe}.pdf"'},
        )

    @app.get("/api/movie/trust-health")
    def movie_trust_health():
        from jarvis.movie_tiers import trust_health

        return {"ok": True, **trust_health()}

    @app.get("/api/movie/profile-banner")
    def movie_profile_banner():
        from jarvis.movie_tiers import profile_banner

        return {"ok": True, **profile_banner()}

    @app.get("/api/movie/task-nudge")
    def movie_task_nudge():
        from jarvis.movie_tiers import task_nudge_check

        return {"ok": True, **task_nudge_check()}

    @app.post("/api/movie/task-nudge/dismiss")
    def movie_task_nudge_dismiss():
        from jarvis.movie_tiers import mark_task_nudge_shown

        mark_task_nudge_shown()
        return {"ok": True}

    @app.get("/api/resources/last-good")
    def resources_last_good():
        from jarvis.movie_tiers import last_good_media_settings

        return {"ok": True, **last_good_media_settings()}

    @app.post("/api/services/restart")
    async def services_restart(request: Request):
        from jarvis.movie_tiers import service_restart

        try:
            body = await request.json()
        except Exception:
            body = {}
        name = (body.get("service") or body.get("name") or "").strip()
        result = service_restart(name)
        status = 200 if result.get("ok") else 400
        return JSONResponse(status_code=status, content=result)

    @app.post("/api/jarvis/restart-server")
    def jarvis_restart_server(request: Request):
        from jarvis.server_restart import request_restart

        client = request.client.host if request.client else "?"
        ua = (request.headers.get("user-agent") or "")[:120]
        result = request_restart(source="api", detail=f"client={client} ua={ua}")
        status = 200 if result.get("ok") else 503
        return JSONResponse(status_code=status, content=result)

    @app.get("/api/homeassistant/entities")
    def ha_entities(domain: str = "", limit: int = 80):
        from jarvis.home_assistant import ha_credential_locked, ha_enabled, list_states

        if not ha_enabled():
            if ha_credential_locked():
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "locked": True,
                        "message": "Home Assistant is locked. Unlock Aria to load entities.",
                    },
                )
            return JSONResponse(
                status_code=400, content={"ok": False, "message": "Home Assistant disabled"}
            )
        try:
            states = list_states(refresh=True)
        except Exception as exc:
            return JSONResponse(
                status_code=503,
                content={
                    "ok": False,
                    "message": str(exc) or "Home Assistant unreachable",
                    "entities": [],
                },
            )
        dom = (domain or "").strip().lower()
        if dom:
            states = [s for s in states if (s.get("entity_id") or "").startswith(f"{dom}.")]
        return {"ok": True, "entities": states[: min(limit, 200)]}

    @app.post("/api/homeassistant/toggle")
    async def ha_toggle_entity(request: Request):
        from jarvis.home_assistant import call_service, ha_enabled
        from jarvis.tool_permissions import create_pending, permission_for

        if not ha_enabled():
            return JSONResponse(status_code=400, content={"ok": False, "message": "HA disabled"})
        try:
            body = await request.json()
        except Exception:
            body = {}
        eid = (body.get("entity_id") or "").strip()
        action = (body.get("action") or "toggle").strip().lower()
        if not eid:
            return JSONResponse(
                status_code=400, content={"ok": False, "message": "entity_id required"}
            )
        perm = permission_for("ha_control")
        if perm == "never":
            return JSONResponse(
                status_code=403,
                content={
                    "ok": False,
                    "message": "Home Assistant control is blocked by tool permissions.",
                },
            )
        confirmed = str(body.get("confirmed", "")).lower() in ("1", "true", "yes")
        if perm == "ask" and not confirmed:
            confirm_id = create_pending(
                "ha_control",
                "ha_control",
                {"target": eid, "action": action, "entity_id": eid},
                f"toggle {eid}",
            )
            return {
                "ok": False,
                "confirm_required": True,
                "confirm_id": confirm_id,
                "message": "Confirm Home Assistant control?",
            }
        domain = eid.split(".")[0]
        svc = "turn_on" if action == "on" else "turn_off" if action == "off" else "toggle"
        call_service(domain, svc, {"entity_id": eid})
        return {"ok": True, "entity_id": eid, "action": svc}

    @app.post("/api/homeassistant/scene")
    async def ha_activate_scene(request: Request):
        from jarvis.home_assistant import activate_scene, ha_enabled
        from jarvis.tool_permissions import create_pending, permission_for

        if not ha_enabled():
            return JSONResponse(status_code=400, content={"ok": False, "message": "HA disabled"})
        try:
            body = await request.json()
        except Exception:
            body = {}
        scene = (body.get("entity_id") or body.get("scene") or "").strip()
        if not scene:
            return JSONResponse(
                status_code=400, content={"ok": False, "message": "entity_id required"}
            )
        perm = permission_for("ha_control")
        if perm == "never":
            return JSONResponse(
                status_code=403,
                content={
                    "ok": False,
                    "message": "Home Assistant control is blocked by tool permissions.",
                },
            )
        confirmed = str(body.get("confirmed", "")).lower() in ("1", "true", "yes")
        if perm == "ask" and not confirmed:
            confirm_id = create_pending(
                "ha_control",
                "ha_scene",
                {"scene": scene, "entity_id": scene},
                f"activate scene {scene}",
            )
            return {
                "ok": False,
                "confirm_required": True,
                "confirm_id": confirm_id,
                "message": "Confirm Home Assistant scene?",
            }
        ok, _msg = activate_scene(scene)
        return {"ok": ok, "scene": scene}

    @app.post("/api/video/storyboard")
    async def video_storyboard(request: Request):
        """Storyboard via shared Video Generation media queue (not coding_jobs)."""
        from jarvis.video_generation.engine import submit_storyboard

        ctype = (request.headers.get("content-type") or "").lower()
        if "application/json" in ctype:
            body = await request.json()
            paths = body.get("paths") or body.get("path") or ""
            if isinstance(paths, list):
                path_str = ",".join(str(p) for p in paths)
                path_list = [str(p) for p in paths]
            else:
                path_str = str(paths)
                path_list = [p.strip() for p in path_str.split(",") if p.strip()]
            sec = body.get("sec_per_slide", 3.5)
            width = body.get("width")
            height = body.get("height")
        else:
            form = await request.form()
            path_str = str(form.get("paths") or "")
            path_list = [p.strip() for p in path_str.split(",") if p.strip()]
            try:
                sec = float(form.get("sec_per_slide") or 3.5)
            except (TypeError, ValueError):
                sec = 3.5
            width = form.get("width")
            height = form.get("height")

        result = submit_storyboard(
            assistant,
            {
                "paths": path_list,
                "sec_per_slide": sec,
                "width": width,
                "height": height,
            },
            source="studio",
        )
        return result

    @app.get("/api/registry/actions")
    def actions_registry():
        from jarvis.handlers import ensure_handlers_loaded
        from jarvis.handlers.registry import all_actions

        ensure_handlers_loaded()
        return {"ok": True, "actions": all_actions()}

    @app.get("/api/registry/router/rules")
    def router_rules():
        from jarvis.router_table import list_rules

        return {"ok": True, "rules": list_rules()}

    @app.get("/api/audit")
    def audit_get(refresh: bool = False):
        from jarvis.system_audit import get_audit_status

        # GET never starts a run. Entering the Audit Room must be read-only.
        # POST /api/audit/run is the only start. `refresh` is ignored on GET.
        _ = refresh
        return get_audit_status()

    @app.post("/api/audit/run")
    def audit_run():
        from jarvis.system_audit import clear_audit_cache, run_audit

        clear_audit_cache()
        return run_audit(use_cache=False, background=True)

    @app.post("/api/audit/install")
    async def audit_install(request: Request):
        from jarvis.system_audit import clear_audit_cache
        from jarvis.system_audit_engine import run_install_script

        try:
            body = await request.json()
        except Exception:
            body = {}
        key = (body.get("install_key") or body.get("key") or "").strip()
        if not key:
            return JSONResponse({"ok": False, "error": "install_key required"})
        try:
            result = run_install_script(key)
            if result.get("ok"):
                clear_audit_cache()
                result["message"] = (
                    result.get("message") or "Install finished"
                ) + " — run audit to refresh"
            return JSONResponse(result)
        except Exception as exc:
            return JSONResponse({"ok": False, "error": str(exc), "message": str(exc)})

    @app.get("/api/audit/status")
    def audit_status_alias():
        from jarvis.system_audit import get_audit_status

        return get_audit_status()

    @app.get("/api/audit/history")
    def audit_history_alias():
        from jarvis.system_audit import get_cached_audit

        cached = get_cached_audit()
        if not cached:
            return {"ok": False, "history": [], "message": "No audit cached"}
        return {"ok": True, "history": [cached], "latest": cached}

    @app.get("/api/audit/latest")
    def audit_latest_alias():
        from jarvis.system_audit import get_audit_status, get_cached_audit

        cached = get_cached_audit()
        if cached:
            return {"ok": True, **cached}
        return get_audit_status()

    @app.get("/api/background-jobs")
    def background_jobs_alias():
        from jarvis.jobs_center import snapshot

        return {"ok": True, **snapshot()}

    @app.get("/api/skills")
    def skills_list(q: str = ""):
        from jarvis.skill_database import list_skills

        skills = list_skills(query=q)
        return {
            "ok": True,
            "skills": [
                {
                    "slug": s.get("slug"),
                    "name": s.get("name"),
                    "description": s.get("description"),
                    "tags": s.get("tags") or [],
                    "steps": len(s.get("steps") or []),
                }
                for s in skills
            ],
        }

    @app.post("/api/skills/{slug}/run")
    async def skills_run(slug: str, request: Request):
        from jarvis.automation.activity_bridge import publish_run_event
        from jarvis.automation.execution import normalize_result
        from jarvis.skill_database import run_skill

        try:
            body = await request.json()
        except Exception:
            body = {}
        # Explicit dry_run; tests often pass dry_run True. Default True for legacy safety
        # unless confirm=true requests real run.
        if body.get("confirm") and "dry_run" not in body:
            dry_run = False
        else:
            dry_run = True if body.get("dry_run") is None else bool(body.get("dry_run"))
        result = run_skill(slug, dry_run=dry_run)
        norm = normalize_result(
            {"ok": result.get("ok", False), "result": result, "message": result.get("message")},
            dry_run=dry_run,
        )
        pub = publish_run_event(
            kind="skill",
            name=slug,
            status=norm["status"],
            target_id=slug,
            why=norm["why"],
            dry_run=dry_run,
            executed=norm["executed"],
            detail=result,
        )
        status = 200 if result.get("ok") or dry_run else 404
        return JSONResponse(
            status_code=status,
            content={**result, "execution": norm, "activity": pub.get("activity"), "run": pub.get("run")},
        )

    @app.get("/api/workflows")
    def workflows_list(q: str = ""):
        from jarvis.workflow_learning import list_workflows

        workflows = list_workflows(query=q)
        return {
            "ok": True,
            "workflows": [
                {
                    "slug": w.get("slug"),
                    "name": w.get("name"),
                    "description": w.get("description"),
                    "count": w.get("count", 1),
                    "steps": len(w.get("steps") or []),
                }
                for w in workflows
            ],
        }

    @app.post("/api/workflows/{slug}/run")
    async def workflows_run(slug: str, request: Request):
        from jarvis.automation.activity_bridge import publish_run_event
        from jarvis.automation.execution import normalize_result
        from jarvis.workflow_learning import run_workflow

        try:
            body = await request.json()
        except Exception:
            body = {}
        if body.get("confirm") and "dry_run" not in body:
            dry_run = False
        else:
            dry_run = True if body.get("dry_run") is None else bool(body.get("dry_run"))
        if not dry_run and not body.get("confirm"):
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "status": "permission_required",
                    "error": "confirm=true required for real execution",
                },
            )
        result = run_workflow(slug, assistant=None if dry_run else assistant, dry_run=dry_run)
        norm = normalize_result(
            {"ok": result.get("ok", False), "result": result, "message": result.get("message")},
            dry_run=dry_run,
        )
        pub = publish_run_event(
            kind="learned_workflow",
            name=slug,
            status=norm["status"],
            target_id=slug,
            why=norm["why"],
            dry_run=dry_run,
            executed=norm["executed"],
            detail=result,
        )
        status = 200 if result.get("ok") or dry_run else 404
        return JSONResponse(
            status_code=status,
            content={**result, "execution": norm, "activity": pub.get("activity"), "run": pub.get("run")},
        )

    @app.post("/api/workflows/scan")
    async def workflows_scan(request: Request):
        from jarvis.automation.suggestions import propose_from_scan
        from jarvis.workflow_learning import scan_action_log

        try:
            body = await request.json()
        except Exception:
            body = {}
        min_rep = body.get("min_repeats")
        found = scan_action_log(min_repeats_count=min_rep)
        suggestions = propose_from_scan(found)
        return {
            "ok": True,
            "count": len(found),
            "workflows": found,
            "suggestions": suggestions,
            "auto_enabled": False,
            "message": "Suggestions created — review in Automation Home before enabling.",
        }

    # —— Connections (Knowledge Graph product surface) ——
    @app.get("/api/connections/home")
    def connections_home_api():
        from jarvis.connections_services import connections_home

        return connections_home()

    @app.get("/api/connections/health")
    def connections_health_api():
        from jarvis.connections_services import health

        return health()

    @app.get("/api/connections/search")
    def connections_search_api(
        q: str = "",
        limit: int = 20,
        namespace: str = "",
        kind: str = "",
        mode: str = "all",
    ):
        from jarvis.connections_services import search_connections

        return search_connections(q, limit=limit, namespace=namespace, kind=kind, mode=mode)

    @app.get("/api/connections/entity")
    def connections_entity_api(name: str = "", namespace: str = ""):
        from jarvis.connections_services import entity_page

        return entity_page(name, namespace=namespace)

    @app.post("/api/connections/entity")
    async def connections_create_entity(request: Request):
        body = await request.json()
        from jarvis.connections_services import create_entity

        return create_entity(
            str(body.get("name") or ""),
            kind=str(body.get("kind") or "entity"),
            namespace=str(body.get("namespace") or "default"),
            description=str(body.get("description") or ""),
            source=str(body.get("source") or "manual"),
            confidence=float(body.get("confidence") or 1.0),
            project=str(body.get("project") or ""),
            document=str(body.get("document") or ""),
        )

    @app.post("/api/connections/relationship")
    async def connections_create_rel(request: Request):
        body = await request.json()
        from jarvis.connections_services import create_relationship

        return create_relationship(
            str(body.get("subject") or ""),
            str(body.get("predicate") or ""),
            str(body.get("object") or ""),
            namespace=str(body.get("namespace") or "default"),
            source=str(body.get("source") or "manual"),
            confidence=float(body.get("confidence") or 1.0),
            memory_id=str(body.get("memory_id") or ""),
            document=str(body.get("document") or ""),
            project=str(body.get("project") or ""),
            journal=str(body.get("journal") or ""),
            description=str(body.get("description") or ""),
        )

    @app.post("/api/connections/propose")
    async def connections_propose(request: Request):
        body = await request.json()
        from jarvis.connections_services import propose_ingest_from_text

        return propose_ingest_from_text(
            str(body.get("text") or ""),
            namespace=str(body.get("namespace") or "default"),
            source=str(body.get("source") or "ai_suggestion"),
            document=str(body.get("document") or ""),
            project=str(body.get("project") or ""),
        )

    @app.post("/api/connections/approve")
    async def connections_approve(request: Request):
        body = await request.json()
        from jarvis.connections_services import approve_pending_ingest

        return approve_pending_ingest(
            str(body.get("pending_id") or ""),
            selected_entities=body.get("entities"),
            selected_rels=body.get("relationships"),
        )

    @app.post("/api/connections/dismiss")
    async def connections_dismiss(request: Request):
        body = await request.json()
        from jarvis.connections_services import dismiss_pending_ingest

        return dismiss_pending_ingest(str(body.get("pending_id") or ""))

    @app.delete("/api/connections/entity")
    def connections_delete_entity(name: str = "", namespace: str = "default"):
        from jarvis.connections_services import delete_entity

        return delete_entity(name, namespace=namespace)

    @app.delete("/api/connections/relationship")
    def connections_delete_rel(id: str = ""):
        from jarvis.connections_services import delete_relationship

        return delete_relationship(id)

    @app.post("/api/connections/prune")
    async def connections_prune(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.connections_services import prune_orphans

        return prune_orphans(namespace=str(body.get("namespace") or ""))

    @app.post("/api/connections/cleanup-queries")
    def connections_cleanup_queries():
        from jarvis.connections_services import cleanup_queries_namespace

        return cleanup_queries_namespace()

    @app.post("/api/connections/undo")
    async def connections_undo(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.connections_services import undo_last

        return undo_last(str(body.get("undo_id") or ""))

    @app.post("/api/connections/merge")
    async def connections_merge(request: Request):
        body = await request.json()
        from jarvis.connections_services import merge_entities

        return merge_entities(
            str(body.get("keep") or ""),
            str(body.get("drop") or ""),
            namespace=str(body.get("namespace") or "default"),
        )

    @app.get("/api/connections/assistant")
    def connections_assistant_api():
        from jarvis.connections_services import relationship_assistant

        return relationship_assistant()

    @app.get("/api/connections/explain")
    def connections_explain_api(subject: str = "", object: str = "", namespace: str = ""):
        from jarvis.connections_services import explain_relationship

        return explain_relationship(subject, object, namespace=namespace)

    @app.get("/api/connections/project")
    def connections_project_api(slug: str = ""):
        from jarvis.connections_services import project_subgraph

        return project_subgraph(slug)

    @app.post("/api/connections/from-document")
    async def connections_from_document(request: Request):
        """Documents → extract → review queue (never auto-write)."""
        body = await request.json()
        from jarvis.connections_services import propose_ingest_from_text
        from jarvis.document_pipeline import parse_document

        path = str(body.get("path") or "").strip()
        text = str(body.get("text") or "")
        if path and not text:
            try:
                doc = parse_document(path)
                text = "\n\n".join(getattr(doc, "pages", None) or [])
            except Exception as exc:
                return {"ok": False, "error": str(exc)}
        return propose_ingest_from_text(
            text,
            namespace=str(body.get("namespace") or "default"),
            source="document",
            document=path or str(body.get("document") or ""),
            project=str(body.get("project") or ""),
        )

    try:
        from jarvis.intelligence.routes import register_intelligence_routes

        register_product("intelligence", register_intelligence_routes, app, assistant)
        from jarvis.automation.product_routes import register_automation_product_routes

        register_product("automation", register_automation_product_routes, app, assistant)
        from jarvis.specialists.routes import register_specialist_routes

        register_product("specialists", register_specialist_routes, app, assistant)
    except Exception as exc:
        # Import-time failure before individual register_product calls
        register_product(
            "intelligence_automation_specialists",
            lambda *_a, **_k: (_ for _ in ()).throw(exc),
            app,
            assistant,
        )
