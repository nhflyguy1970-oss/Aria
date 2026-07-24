"""Memory, cheatsheet, and profile REST API routes."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def _memory_settings_payload(assistant) -> dict:
    from jarvis.brain_memory import brain_mode_status
    from jarvis.config import (
        load_auto_checkpoint,
        load_auto_document_learn,
        load_auto_journal_learn,
        load_auto_memory_mode,
        load_auto_namespace,
        load_brain_mode,
        load_memory_in_system_prompt,
        load_memory_namespace,
    )

    status = {
        "ok": True,
        "namespace": load_memory_namespace(),
        "session_namespace": assistant.session.memory_namespace,
        "auto_memory_mode": load_auto_memory_mode(),
        "auto_checkpoint": load_auto_checkpoint(),
        "auto_namespace": load_auto_namespace(),
        "memory_in_system_prompt": load_memory_in_system_prompt(),
        "brain_mode": load_brain_mode(),
        "auto_journal_learn": load_auto_journal_learn(),
        "auto_document_learn": load_auto_document_learn(),
        "brain_learning": brain_mode_status(),
    }
    try:
        from jarvis.action_confidence import snapshot as confidence_snapshot
        from jarvis.reflection_loop import reflection_status

        status["reflection"] = reflection_status()
        status["action_confidence"] = confidence_snapshot()
    except Exception:
        pass
    return status


def register_routes(app, assistant) -> None:
    @app.get("/api/memory/all")
    def memory_all(q: str = "", type: str = "", namespace: str = ""):
        entries = assistant.memory.list_entries(
            type or None,
            namespace=namespace or None,
            query=q or None,
        )
        return {
            "entries": entries,
            "stats": assistant.memory.stats(),
            "namespace": assistant.session.memory_namespace,
        }

    @app.get("/api/memory/stats")
    def memory_stats():
        from jarvis.config import (
            load_auto_checkpoint,
            load_auto_memory,
            load_auto_memory_mode,
            load_auto_namespace,
            load_memory_in_system_prompt,
            load_memory_namespace,
        )

        payload = {
            "stats": assistant.memory.stats(),
            "namespace": load_memory_namespace(),
            "session_namespace": assistant.session.memory_namespace,
            "auto_memory": load_auto_memory(),
            "auto_memory_mode": load_auto_memory_mode(),
            "auto_checkpoint": load_auto_checkpoint(),
            "auto_namespace": load_auto_namespace(),
            "memory_in_system_prompt": load_memory_in_system_prompt(),
            "source_of_truth": "acm",
        }
        try:
            from aria_core.acm_bridge import acm_dashboard, acm_is_authoritative

            if acm_is_authoritative():
                payload["acm"] = acm_dashboard(limit=50)
                payload["source_of_truth"] = "acm"
        except Exception:
            pass
        return payload

    @app.get("/api/memory/settings")
    def memory_settings_get():
        return _memory_settings_payload(assistant)

    @app.post("/api/memory/settings")
    async def memory_settings_set(request: Request):
        from jarvis.config import (
            save_auto_checkpoint,
            save_auto_document_learn,
            save_auto_journal_learn,
            save_auto_memory_mode,
            save_auto_namespace,
            save_brain_mode,
            save_memory_in_system_prompt,
            save_memory_namespace,
        )

        body = await request.json()
        if "auto_memory_mode" in body:
            save_auto_memory_mode(str(body["auto_memory_mode"]))
        if "auto_checkpoint" in body:
            save_auto_checkpoint(bool(body["auto_checkpoint"]))
        if "auto_namespace" in body:
            save_auto_namespace(bool(body["auto_namespace"]))
            if body["auto_namespace"]:
                assistant.sync_project_namespace()
        if "memory_in_system_prompt" in body:
            save_memory_in_system_prompt(bool(body["memory_in_system_prompt"]))
        if "brain_mode" in body:
            save_brain_mode(bool(body["brain_mode"]))
        if "auto_journal_learn" in body:
            save_auto_journal_learn(bool(body["auto_journal_learn"]))
        if "auto_document_learn" in body:
            save_auto_document_learn(bool(body["auto_document_learn"]))
        if "namespace" in body:
            ns = (body.get("namespace") or "default").strip() or "default"
            save_memory_namespace(ns)
            assistant.session.note_memory_namespace(ns)
        assistant.refresh_system_prompt()
        return memory_settings_get()

    @app.get("/api/memory/environment/preferences")
    def memory_environment_preferences_get():
        from jarvis.memory_knowledge import environment_preferences_payload

        return environment_preferences_payload()

    @app.put("/api/memory/environment/preferences")
    async def memory_environment_preferences_put(request: Request):
        from jarvis.memory_knowledge import save_environment_preferences_to_memory

        body = await request.json()
        prefs: dict[str, str] = {}
        if isinstance(body.get("preferences"), list):
            for item in body["preferences"]:
                if isinstance(item, dict) and item.get("key"):
                    prefs[str(item["key"])] = str(item.get("content") or "")
        elif isinstance(body.get("preferences"), dict):
            prefs = {str(k): str(v) for k, v in body["preferences"].items()}
        else:
            for spec in ("pref-linux-commands", "pref-ollama-local", "pref-privacy-local"):
                if spec in body:
                    prefs[spec] = str(body[spec])
        if not prefs:
            return JSONResponse(
                status_code=400, content={"ok": False, "error": "preferences required"}
            )
        assistant.refresh_system_prompt()
        return save_environment_preferences_to_memory(assistant.memory, prefs)

    @app.post("/api/memory/environment/sync")
    def memory_environment_sync(machine_only: bool = False):
        from jarvis.memory_knowledge import sync_environment_memory

        result = sync_environment_memory(assistant.memory, force=True, machine_only=machine_only)
        assistant.refresh_system_prompt()
        return result

    @app.get("/api/memory/conflicts")
    def memory_conflicts():
        from jarvis.memory_context import find_conflicts

        return {"ok": True, "conflicts": find_conflicts(assistant.memory)}

    @app.post("/api/memory/conflicts/resolve")
    async def memory_conflicts_resolve(request: Request):
        body = await request.json()
        drop_id = (body.get("drop_id") or "").strip()
        if not drop_id:
            return JSONResponse(status_code=400, content={"ok": False, "error": "drop_id required"})
        ok = assistant.memory.delete_id(drop_id)
        if not ok:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        assistant.refresh_system_prompt()
        return {"ok": True}

    @app.post("/api/memory/auto-checkpoint")
    async def memory_auto_checkpoint():
        assistant.branches.persist(session=assistant.session)
        return assistant.auto_checkpoint(reason="gui-exit")

    @app.post("/api/memory")
    async def memory_add(request: Request):
        body = await request.json()
        content = (body.get("content") or "").strip()
        if not content:
            return JSONResponse(status_code=400, content={"ok": False, "error": "content required"})
        try:
            entry = assistant.memory.add(
                body.get("type") or "fact",
                content,
                tags=body.get("tags") or [],
                namespace=body.get("namespace") or assistant.session.memory_namespace,
            )
        except ValueError as e:
            return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})
        assistant.refresh_system_prompt()
        return {"ok": True, "entry": assistant.memory.to_public(entry)}

    @app.put("/api/memory/{entry_id}")
    async def memory_update(entry_id: str, request: Request):
        body = await request.json()
        ok = assistant.memory.update(
            entry_id,
            content=body.get("content"),
            entry_type=body.get("type"),
            tags=body.get("tags"),
            namespace=body.get("namespace"),
        )
        if not ok:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        assistant.refresh_system_prompt()
        return {"ok": True, "entry": assistant.memory.get(entry_id)}

    @app.delete("/api/memory/{entry_id}")
    def memory_delete_id(entry_id: str):
        if entry_id.isdigit():
            ok = assistant.memory.delete(int(entry_id))
        else:
            ok = assistant.memory.delete_id(entry_id)
        if ok:
            assistant.refresh_system_prompt()
        return {"ok": ok}

    @app.get("/api/memory/export")
    def memory_export():
        return assistant.memory.export_data()

    @app.post("/api/memory/import")
    async def memory_import(request: Request):
        body = await request.json()
        merge = body.get("merge", True) is not False
        try:
            added = assistant.memory.import_data(body, merge=merge)
        except ValueError as e:
            return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})
        return {"ok": True, "added": added}

    @app.post("/api/memory/prune")
    def memory_prune():
        removed = assistant.memory.prune()
        assistant.refresh_system_prompt()
        return {"ok": True, "removed": removed}

    @app.get("/api/memory/trust/status")
    def memory_trust_status():
        from jarvis.trust_memory import trust_status

        status = trust_status(assistant.memory)
        status["last_scrub_on_startup"] = getattr(assistant, "_trust_last_scrub", 0)
        return {"ok": True, **status}

    @app.post("/api/memory/trust/scrub")
    def memory_trust_scrub():
        from jarvis.trust_memory import scrub_store

        result = scrub_store(assistant.memory)
        assistant.refresh_system_prompt()
        return {"ok": True, **result}

    @app.get("/api/cheatsheets")
    def cheatsheets_list():
        from jarvis.cheatsheets import list_cheatsheets, seed_cheatsheets

        if not list_cheatsheets(assistant.memory):
            seed_cheatsheets(assistant.memory)
        return {"ok": True, "cheatsheets": list_cheatsheets(assistant.memory)}

    @app.get("/api/cheatsheets/{key}")
    def cheatsheets_get(key: str):
        from jarvis.cheatsheets import find_by_key, seed_cheatsheets

        if not find_by_key(assistant.memory, key):
            seed_cheatsheets(assistant.memory, keys=[key.split("/")[0]])
        entry = find_by_key(assistant.memory, key)
        if not entry:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        return {"ok": True, "cheatsheet": assistant.memory.to_public(entry)}

    @app.put("/api/cheatsheets/{key}")
    async def cheatsheets_update(key: str, request: Request):
        from jarvis.cheatsheets import upsert_cheatsheet

        body = await request.json()
        content = (body.get("content") or "").strip()
        if not content:
            return JSONResponse(status_code=400, content={"ok": False, "error": "content required"})
        try:
            entry = upsert_cheatsheet(assistant.memory, key, content)
        except ValueError as e:
            return JSONResponse(status_code=400, content={"ok": False, "error": str(e)})
        return {"ok": True, "cheatsheet": assistant.memory.to_public(entry)}

    @app.post("/api/cheatsheets/{key}/reset")
    def cheatsheets_reset(key: str):
        from jarvis.cheatsheets import reset_cheatsheet

        entry = reset_cheatsheet(assistant.memory, key)
        if not entry:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        return {"ok": True, "cheatsheet": assistant.memory.to_public(entry)}

    @app.get("/api/profile/questionnaire")
    def profile_questionnaire_status(edit: bool = False):
        from jarvis.profile_questionnaire import get_questions, get_status

        status = get_status()
        has_profile = bool(assistant.memory.list_entries(namespace="profile"))
        show_questions = edit or not status.get("completed") or not has_profile
        return {
            "ok": True,
            **status,
            "questions": get_questions() if show_questions else [],
        }

    @app.post("/api/profile/questionnaire/reset")
    def profile_questionnaire_reset():
        from jarvis.profile_questionnaire import get_questions, reset_profile

        reset_profile(assistant.memory)
        assistant.refresh_system_prompt()
        return {"ok": True, "questions": get_questions()}

    @app.post("/api/profile/questionnaire")
    async def profile_questionnaire_submit(request: Request):
        from jarvis.profile_questionnaire import get_status, save_answers, skip

        body = await request.json()
        if body.get("skip"):
            skip(assistant.memory)
            return {"ok": True, "skipped": True}
        answers = body.get("answers") if isinstance(body.get("answers"), dict) else body
        if not isinstance(answers, dict):
            return JSONResponse(status_code=400, content={"ok": False, "error": "answers required"})
        name = (answers.get("name") or "").strip()
        if not name:
            return JSONResponse(status_code=400, content={"ok": False, "error": "name is required"})
        retake = bool(body.get("retake")) or bool(get_status().get("completed"))
        stored = save_answers(assistant.memory, answers, replace=retake)
        assistant.refresh_system_prompt()
        return {"ok": True, "stored": len(stored), "memories": stored, "retake": retake}

    @app.post("/api/memory/namespace")
    async def memory_namespace_set(request: Request):
        from jarvis.config import save_memory_namespace

        body = await request.json()
        ns = (body.get("namespace") or "default").strip() or "default"
        save_memory_namespace(ns)
        assistant.session.note_memory_namespace(ns)
        return {"ok": True, "namespace": ns}
