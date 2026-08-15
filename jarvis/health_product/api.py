"""Health product HTTP API — local PHR only."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from fastapi import File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER
from jarvis.health_product.trust import HealthWriteBlocked


def _owner_or_response(request):
    from jarvis.health_product import gate

    err = gate.require_owner(request)
    if err:
        status = int(err.pop("status_code", 423))
        return JSONResponse(status_code=status, content=err)
    return None


def _gate_or_response(request, op: str, body: dict | None = None):
    from jarvis.health_product import gate

    err = gate.require(request, op, body=body)
    if err:
        status = int(err.pop("status_code", 403))
        return JSONResponse(status_code=status, content=err)
    return None


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    if not getattr(app.state, "health_write_guard", False):

        @app.exception_handler(HealthWriteBlocked)
        async def _health_write_blocked(_request, exc: HealthWriteBlocked):
            return JSONResponse(status_code=403, content={"ok": False, "message": str(exc), "disclaimer": DISCLAIMER})

        app.state.health_write_guard = True

    @app.get("/api/health/product")
    def health_product_status(request: Request):
        blocked = _owner_or_response(request)
        if blocked:
            return blocked
        from jarvis.health_product.engine import product_status

        return product_status()

    @app.get("/api/health/home")
    def health_home(request: Request):
        blocked = _owner_or_response(request)
        if blocked:
            return blocked
        from jarvis.health_product.engine import home_payload

        return home_payload()

    @app.get("/api/health/profile")
    def health_profile_get():
        return {"ok": True, "profile": store.get_profile(), "disclaimer": DISCLAIMER}

    @app.post("/api/health/profile")
    async def health_profile_set(request: Request):
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse(status_code=400, content={"ok": False, "message": "JSON object required"})
        return {"ok": True, "profile": store.set_profile(body), "disclaimer": DISCLAIMER}

    @app.get("/api/health/checkin")
    def health_checkin_get(day: str = ""):
        return {"ok": True, "checkin": store.get_checkin(day or None), "disclaimer": DISCLAIMER}

    @app.get("/api/health/checkins")
    def health_checkins(limit: int = 90, since: str = ""):
        return {"ok": True, "checkins": store.list_checkins(limit=limit, since=since or None)}

    @app.post("/api/health/checkin")
    async def health_checkin_set(request: Request):
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse(status_code=400, content={"ok": False, "message": "JSON object required"})
        rec = store.upsert_checkin(body, day=body.get("day"))
        mapping = {
            "weight": ("weight", "lb"),
            "heart_rate": ("heart_rate", "bpm"),
            "blood_sugar": ("blood_sugar", "mg/dL"),
            "temperature": ("temperature", "F"),
            "spo2": ("spo2", "%"),
            "sleep_hours": ("sleep_hours", "hr"),
            "pain": ("pain", ""),
            "mood": ("mood", ""),
            "energy": ("energy", ""),
            "stress": ("stress", ""),
        }
        for key, (kind, units) in mapping.items():
            if key in body and body.get(key) not in (None, ""):
                try:
                    store.add_vital(kind, float(body[key]), units=units, day=rec.get("day"))
                except Exception:
                    pass
        if "bp_systolic" in body and body.get("bp_systolic") not in (None, ""):
            try:
                store.add_vital(
                    "blood_pressure",
                    float(body["bp_systolic"]),
                    value2=float(body["bp_diastolic"]) if body.get("bp_diastolic") not in (None, "") else None,
                    units="mmHg",
                    day=rec.get("day"),
                )
            except Exception:
                pass
        return {"ok": True, "checkin": rec, "disclaimer": DISCLAIMER}

    @app.get("/api/health/medications")
    def health_meds(status: str = ""):
        where, args = ("status=?", (status,)) if status else ("", ())
        return {"ok": True, "medications": store.list_table("medications", where, args, limit=200)}

    @app.post("/api/health/medications")
    async def health_meds_upsert(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("name"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        return {"ok": True, "medication": store.upsert_medication(body)}

    @app.delete("/api/health/medications/{item_id}")
    def health_meds_delete(item_id: str, request: Request):
        blocked = _gate_or_response(request, "edit_medications")
        if blocked:
            return blocked
        return {"ok": store.delete_by_id("medications", item_id)}

    @app.get("/api/health/supplements")
    def health_supps(status: str = ""):
        where, args = ("status=?", (status,)) if status else ("", ())
        return {"ok": True, "supplements": store.list_table("supplements", where, args, limit=200)}

    @app.post("/api/health/supplements")
    async def health_supps_upsert(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("name"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        return {"ok": True, "supplement": store.upsert_supplement(body)}

    @app.delete("/api/health/supplements/{item_id}")
    def health_supps_delete(item_id: str):
        return {"ok": store.delete_by_id("supplements", item_id)}

    @app.get("/api/health/conditions")
    def health_conditions():
        return {"ok": True, "conditions": store.list_table("conditions", limit=200)}

    @app.post("/api/health/conditions")
    async def health_conditions_upsert(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("name"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        return {"ok": True, "condition": store.upsert_condition(body)}

    @app.get("/api/health/allergies")
    def health_allergies():
        return {"ok": True, "allergies": store.list_table("allergies", limit=200)}

    @app.post("/api/health/allergies")
    async def health_allergies_upsert(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("name"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        return {"ok": True, "allergy": store.upsert_allergy(body)}

    @app.get("/api/health/vitals")
    def health_vitals(kind: str = "", since: str = "", limit: int = 365):
        return {"ok": True, "vitals": store.list_vitals(kind=kind or None, since=since or None, limit=limit)}

    @app.post("/api/health/vitals")
    async def health_vitals_add(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("kind"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "kind required"})
        rec = store.add_vital(
            str(body["kind"]),
            body.get("value"),
            value2=body.get("value2"),
            units=str(body.get("units") or ""),
            notes=str(body.get("notes") or ""),
            day=body.get("day"),
        )
        return {"ok": True, "vital": rec}

    @app.get("/api/health/labs")
    def health_labs(name: str = "", since: str = "", limit: int = 200):
        return {"ok": True, "labs": store.list_labs(name=name or None, since=since or None, limit=limit)}

    @app.post("/api/health/labs")
    async def health_labs_add(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("name"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        return {"ok": True, "lab": store.add_lab(body)}

    @app.get("/api/health/symptoms")
    def health_symptoms(limit: int = 100):
        return {"ok": True, "symptoms": store.list_table("symptoms", order="recorded_at DESC", limit=limit)}

    @app.post("/api/health/symptoms")
    async def health_symptoms_add(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("name"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        return {"ok": True, "symptom": store.add_symptom(body)}

    @app.get("/api/health/vaccinations")
    def health_vax():
        return {"ok": True, "vaccinations": store.list_table("vaccinations", order="day DESC", limit=200)}

    @app.post("/api/health/vaccinations")
    async def health_vax_upsert(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("name"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        return {"ok": True, "vaccination": store.upsert_vaccination(body)}

    @app.get("/api/health/notes")
    def health_notes(limit: int = 100):
        return {"ok": True, "notes": store.list_table("medical_notes", order="created_at DESC", limit=limit)}

    @app.post("/api/health/notes")
    async def health_notes_add(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not str(body.get("body") or "").strip():
            return JSONResponse(status_code=400, content={"ok": False, "message": "body required"})
        return {"ok": True, "note": store.add_note(str(body.get("title") or ""), str(body["body"]), body.get("day"))}

    @app.get("/api/health/reminders")
    def health_reminders():
        return {"ok": True, "reminders": store.list_table("reminders", limit=100)}

    @app.post("/api/health/reminders")
    async def health_reminders_upsert(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("title") or not body.get("kind"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "kind and title required"})
        rec = store.upsert_reminder(body)
        synced = None
        try:
            from jarvis.health_product.reminders import maybe_sync_appointment_to_calendar

            synced = maybe_sync_appointment_to_calendar(rec)
        except Exception:
            synced = None
        return {"ok": True, "reminder": rec, "calendar": synced}

    @app.get("/api/health/documents")
    def health_documents(limit: int = 100):
        rows = store.list_table("documents", order="created_at DESC", limit=limit)
        for r in rows:
            text = r.get("extracted_text") or ""
            r["extracted_preview"] = text[:240]
            r.pop("extracted_text", None)
        return {"ok": True, "documents": rows}

    @app.post("/api/health/documents")
    async def health_documents_upload(
        file: UploadFile = File(...),
        title: str = Form(""),
        kind: str = Form("document"),
        notes: str = Form(""),
        day: str = Form(""),
    ):
        store.ensure_dirs()
        raw_name = Path(file.filename or "health-doc").name
        import uuid

        dest = store.DOCS_DIR / f"doc_{uuid.uuid4().hex[:12]}_{raw_name}"
        with dest.open("wb") as fh:
            shutil.copyfileobj(file.file, fh)
        extracted = ""
        try:
            from jarvis.vision_product.ocr import run_ocr

            ocr = run_ocr(str(dest))
            if ocr.get("ok"):
                extracted = str(ocr.get("text") or "")
        except Exception:
            extracted = ""
        rec = store.add_document(
            {
                "title": title or raw_name,
                "kind": kind,
                "path": str(dest),
                "day": day or None,
                "extracted_text": extracted,
                "notes": notes,
            }
        )
        return {"ok": True, "document": rec, "ocr": bool(extracted), "disclaimer": DISCLAIMER}

    @app.get("/api/health/search")
    def health_search(q: str = "", limit: int = 40):
        from jarvis.health_product.engine import search_summary

        return search_summary(q)

    @app.post("/api/health/nl")
    async def health_nl(request: Request):
        body = await request.json()
        text = str((body or {}).get("text") or (body or {}).get("message") or "")
        from jarvis.health_product.engine import ingest_message

        return ingest_message(text)

    @app.get("/api/health/graph")
    def health_graph(kind: str = "weight", days: int = 90):
        from jarvis.health_product.engine import graph_summary

        return graph_summary(kind, days=days)

    @app.get("/api/health/observations")
    def health_observations():
        from jarvis.health_product.engine import observations_message

        return observations_message()

    @app.get("/api/health/doctor-visit")
    def health_doctor():
        from jarvis.health_product.engine import doctor_visit_summary

        return doctor_visit_summary()

    @app.get("/api/health/emergency")
    def health_emergency():
        from jarvis.health_product.engine import emergency_summary

        return emergency_summary()

    @app.get("/api/health/report")
    def health_report(kind: str = "daily", day: str = "", start: str = "", end: str = "", name: str = "", window: str = ""):
        from jarvis.health_product.reports import report_html

        html = report_html(kind, day=day or None, start=start or None, end=end or None, name=name or None, window=window or "month")
        return HTMLResponse(html)

    @app.get("/api/health/timeline")
    def health_timeline(category: str = "", limit: int = 200):
        from jarvis.health_product.timeline import build_timeline

        return build_timeline(category=category, limit=limit)

    @app.get("/api/health/coach")
    def health_coach():
        from jarvis.health_product.coach import wellness_coach

        return wellness_coach()

    @app.get("/api/health/questions")
    def health_questions(status: str = ""):
        where, args = ("status=?", (status,)) if status else ("", ())
        return {"ok": True, "questions": store.list_table("doctor_questions", where, args, order="created_at DESC", limit=100)}

    @app.post("/api/health/questions")
    async def health_questions_add(request: Request):
        body = await request.json()
        text = str((body or {}).get("text") or (body or {}).get("question") or "").strip()
        if not text:
            return JSONResponse(status_code=400, content={"ok": False, "message": "text required"})
        return {"ok": True, "question": store.add_doctor_question(text, str((body or {}).get("notes") or ""))}

    @app.post("/api/health/questions/{item_id}/status")
    async def health_questions_status(item_id: str, request: Request):
        body = await request.json()
        status = str((body or {}).get("status") or "answered")
        rec = store.set_doctor_question_status(item_id, status, str((body or {}).get("notes") or ""))
        if not rec:
            return JSONResponse(status_code=404, content={"ok": False, "message": "question not found"})
        return {"ok": True, "question": rec}

    @app.get("/api/health/pending")
    def health_pending():
        return {"ok": True, "pending": store.latest_pending(), "disclaimer": DISCLAIMER}

    @app.post("/api/health/confirm")
    async def health_confirm(request: Request):
        body = await request.json()
        confirm = bool((body or {}).get("confirm", True))
        from jarvis.health_product.engine import confirm_latest

        return confirm_latest(confirm)

    @app.get("/api/health/consultations")
    def health_consultations():
        rows = store.list_table("consultations", order="created_at DESC", limit=50)
        for r in rows:
            r.pop("shared_json", None)
        return {"ok": True, "consultations": rows, "disclaimer": DISCLAIMER}

    @app.post("/api/health/consult/preview")
    async def health_consult_preview(request: Request):
        body = await request.json()
        from jarvis.health_product.consult import preview_consultation

        return preview_consultation(
            str((body or {}).get("question") or (body or {}).get("text") or ""),
            level=str((body or {}).get("level") or "sanitized"),
            include_docs=bool((body or {}).get("include_docs")),
        )

    @app.post("/api/health/consult/{consultation_id}/send")
    def health_consult_send(consultation_id: str, request: Request):
        blocked = _gate_or_response(request, "cloud_consult")
        if blocked:
            return blocked
        from jarvis.health_product.consult import run_consultation

        return run_consultation(consultation_id)

    @app.post("/api/health/consult/{consultation_id}/cancel")
    def health_consult_cancel(consultation_id: str):
        from jarvis.health_product.consult import cancel_consultation

        return cancel_consultation(consultation_id)

    @app.get("/api/health/export")
    def health_export(request: Request):
        blocked = _gate_or_response(request, "export_record")
        if blocked:
            return blocked
        from fastapi.responses import JSONResponse as _JSON

        bundle = store.export_bundle()
        return _JSON(
            content=bundle,
            headers={"Content-Disposition": 'attachment; filename="aria-health-export.json"'},
        )

    @app.get("/api/health/visits")
    def health_visits():
        return {"ok": True, "visits": store.list_table("visits", order="day DESC", limit=100)}

    @app.post("/api/health/visits")
    async def health_visits_add(request: Request):
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse(status_code=400, content={"ok": False, "message": "JSON object required"})
        return {"ok": True, "visit": store.add_visit(body)}

    @app.post("/api/health/reminders/fire")
    def health_reminders_fire():
        from jarvis.health_product.reminders import fire_due_reminders

        return fire_due_reminders()

    @app.get("/api/health/overview")
    def health_overview(request: Request):
        blocked = _owner_or_response(request)
        if blocked:
            return blocked
        from jarvis.health_product.dashboard import dashboard_payload

        return dashboard_payload()

    @app.get("/api/health/scorecard")
    def health_scorecard(days: int = 28):
        from jarvis.health_product.scorecard import build_scorecard

        return build_scorecard(days=days)

    @app.get("/api/health/milestones")
    def health_milestones():
        from jarvis.health_product.milestones import discover_milestones

        return discover_milestones(persist=True)

    @app.get("/api/health/adherence")
    def health_adherence(days: int = 7):
        from jarvis.health_product.dashboard import medication_adherence

        return {"ok": True, **medication_adherence(days=days), "disclaimer": DISCLAIMER}

    @app.post("/api/health/doses")
    async def health_doses_log(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("name"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        return {
            "ok": True,
            "dose": store.log_dose(
                str(body["name"]),
                status=str(body.get("status") or "taken"),
                kind=str(body.get("kind") or "medication"),
                notes=str(body.get("notes") or ""),
                day=body.get("day"),
            ),
            "disclaimer": DISCLAIMER,
        }

    @app.get("/api/health/recovery")
    def health_recovery(limit: int = 100):
        return {"ok": True, "events": store.list_table("recovery_events", limit=limit)}

    @app.post("/api/health/recovery")
    async def health_recovery_add(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not (body.get("title") or body.get("kind")):
            return JSONResponse(status_code=400, content={"ok": False, "message": "title or kind required"})
        return {"ok": True, "event": store.add_recovery(body), "disclaimer": DISCLAIMER}

    @app.get("/api/health/trends")
    def health_trends():
        from jarvis.health_product.trends import build_trends

        return build_trends()

    @app.get("/api/health/safety")
    def health_safety():
        from jarvis.health_product.safety import scan_interactions

        return scan_interactions()

    @app.get("/api/health/activities")
    def health_activities(limit: int = 100):
        return {"ok": True, "activities": store.list_table("activities", limit=limit), "kinds": __import__("jarvis.health_product.workouts", fromlist=["ACTIVITY_KINDS"]).ACTIVITY_KINDS}

    @app.post("/api/health/activities")
    async def health_activities_add(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("kind"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "kind required"})
        if body.get("calories") in (None, "") and body.get("duration_min"):
            from jarvis.health_product.workouts import estimate_calories

            body["calories"] = estimate_calories(body.get("kind"), body.get("duration_min"), body.get("intensity") or "")
        return {"ok": True, "activity": store.add_activity(body)}

    @app.get("/api/health/workouts")
    def health_workouts(limit: int = 80):
        from jarvis.health_product.workouts import progression, WORKOUT_TEMPLATES

        rows = store.list_table("workouts", limit=limit)
        for row in rows:
            row["sets"] = store.list_workout_sets(row["id"])
            row["volume"] = sum(
                float(s.get("sets") or 1) * float(s.get("reps") or 0) * float(s.get("weight") or 0)
                for s in row["sets"]
                if s.get("reps") is not None
            )
        return {"ok": True, "workouts": rows, "templates": WORKOUT_TEMPLATES, "progression": progression()}

    @app.post("/api/health/workouts")
    async def health_workouts_add(request: Request):
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse(status_code=400, content={"ok": False, "message": "JSON object required"})
        return {"ok": True, "workout": store.add_workout(body, body.get("sets"))}

    @app.get("/api/health/goals")
    def health_goals():
        from jarvis.health_product.dashboard import _goal_progress

        rows = [_goal_progress(g) for g in store.list_table("goals", limit=80)]
        return {"ok": True, "goals": rows}

    @app.post("/api/health/goals")
    async def health_goals_upsert(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("title"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "title required"})
        return {"ok": True, "goal": store.upsert_goal(body)}

    @app.get("/api/health/journal")
    def health_journal_list(limit: int = 80):
        return {"ok": True, "entries": store.list_table("health_journal", limit=limit)}

    @app.post("/api/health/journal")
    async def health_journal_add(request: Request):
        body = await request.json()
        text = str((body or {}).get("body") or (body or {}).get("text") or "").strip()
        if not text:
            return JSONResponse(status_code=400, content={"ok": False, "message": "body required"})
        return {"ok": True, "entry": store.add_health_journal(text, day=(body or {}).get("day"), mood=str((body or {}).get("mood") or ""))}

    @app.get("/api/health/knowledge")
    def health_knowledge(limit: int = 80):
        return {"ok": True, "items": store.list_table("knowledge", limit=limit)}

    @app.post("/api/health/knowledge")
    async def health_knowledge_add(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("title"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "title required"})
        return {"ok": True, "item": store.add_knowledge(body)}

    @app.get("/api/health/providers")
    def health_providers():
        return {"ok": True, "providers": store.list_table("providers", limit=100)}

    @app.post("/api/health/providers")
    async def health_providers_upsert(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("name") or not body.get("specialty"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name and specialty required"})
        return {"ok": True, "provider": store.upsert_provider(body)}

    @app.get("/api/health/procedures")
    def health_procedures():
        return {"ok": True, "procedures": store.list_table("procedures", limit=200)}

    @app.post("/api/health/procedures")
    async def health_procedures_add(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("name"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name required"})
        return {"ok": True, "procedure": store.add_procedure(body)}

    @app.post("/api/health/second-opinion/preview")
    async def health_second_preview(request: Request):
        body = await request.json()
        from jarvis.health_product.second_opinion import preview_second_opinion

        return preview_second_opinion(str((body or {}).get("question") or ""), level=str((body or {}).get("level") or "sanitized"))

    @app.get("/api/health/mission")
    def health_mission():
        from jarvis.health_product.mission_bridge import health_mission_panel

        return {"ok": True, **health_mission_panel()}

    @app.get("/api/health/dashboard")
    def health_dashboard():
        from jarvis.health_product.dashboard_bridge import dashboard_health_summary

        return {"ok": True, **dashboard_health_summary()}

    @app.get("/api/health/family-history")
    def health_family_history_get():
        from jarvis.health_product.family_history import family_summary

        return family_summary()

    @app.post("/api/health/family-history")
    async def health_family_history_post(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not body.get("condition"):
            return JSONResponse(status_code=400, content={"ok": False, "message": "condition required"})
        blocked = _gate_or_response(request, "edit_family_history", body if isinstance(body, dict) else None)
        if blocked:
            return blocked
        from jarvis.health_product.family_history import save_entry

        return {"ok": True, "entry": save_entry(body, confirmed=bool(body.get("confirmed"))), "disclaimer": DISCLAIMER}

    @app.delete("/api/health/family-history/{item_id}")
    def health_family_history_delete(item_id: str, request: Request):
        blocked = _gate_or_response(request, "edit_family_history")
        if blocked:
            return blocked
        return {"ok": store.delete_by_id("family_history", item_id), "disclaimer": DISCLAIMER}

    @app.get("/api/health/preventive")
    def health_preventive_get():
        from jarvis.health_product.preventive import list_due

        return list_due(include_catalog=True)

    @app.get("/api/health/preventive/catalog")
    def health_preventive_catalog():
        from jarvis.health_product.preventive import catalog

        return {"ok": True, "catalog": catalog(), "disclaimer": DISCLAIMER}

    @app.get("/api/health/preventive/due")
    def health_preventive_due():
        from jarvis.health_product.preventive import list_due

        return list_due()

    @app.post("/api/health/preventive")
    async def health_preventive_post(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not (body.get("name") or body.get("slug")):
            return JSONResponse(status_code=400, content={"ok": False, "message": "name or slug required"})
        from jarvis.health_product.preventive import save

        return {"ok": True, "item": save(body), "disclaimer": DISCLAIMER}

    @app.post("/api/health/preventive/{item_id}/complete")
    async def health_preventive_complete(item_id: str, request: Request):
        body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        if not isinstance(body, dict):
            body = {}
        from jarvis.health_product.preventive import complete

        try:
            return {"ok": True, "item": complete(item_id, day=body.get("day"), result=str(body.get("result") or ""), physician=str(body.get("physician") or "")), "disclaimer": DISCLAIMER}
        except ValueError as exc:
            return JSONResponse(status_code=404, content={"ok": False, "message": str(exc), "disclaimer": DISCLAIMER})

    @app.delete("/api/health/preventive/{item_id}")
    def health_preventive_delete(item_id: str):
        return {"ok": store.delete_by_id("preventive_care", item_id), "disclaimer": DISCLAIMER}

    @app.get("/api/health/nutrition")
    def health_nutrition_get(limit: int = 100):
        return {"ok": True, "entries": store.list_table("nutrition_log", order="created_at DESC", limit=limit), "disclaimer": DISCLAIMER}

    @app.post("/api/health/nutrition")
    async def health_nutrition_post(request: Request):
        body = await request.json()
        if not isinstance(body, dict):
            return JSONResponse(status_code=400, content={"ok": False, "message": "JSON object required"})
        from jarvis.health_product.nutrition import log_entries

        entries = body if isinstance(body.get("entries"), list) else [body]
        return {"ok": True, "entries": log_entries(entries, provenance="manual"), "disclaimer": DISCLAIMER}

    @app.get("/api/health/nutrition/habits")
    def health_nutrition_habits(days: int = 14):
        from jarvis.health_product.nutrition import habits

        return habits(days=days)

    @app.get("/api/health/correlations")
    def health_correlations(days: int = 45):
        from jarvis.health_product.patterns import build_insights, symptom_correlations

        symptom_correlations(days=days)
        return build_insights(days=days)

    @app.post("/api/health/observations/{obs_id}/dismiss")
    def health_observation_dismiss(obs_id: str):
        row = store.get_by_id("health_observations", obs_id)
        if not row:
            return JSONResponse(status_code=404, content={"ok": False, "message": "observation not found"})
        with store._lock:
            conn = store.connect()
            try:
                conn.execute("UPDATE health_observations SET dismissed=1 WHERE id=?", (obs_id,))
                conn.commit()
            finally:
                conn.close()
        return {"ok": True, "observation": store.get_by_id("health_observations", obs_id), "disclaimer": DISCLAIMER}

    @app.get("/api/health/visit-prep")
    def health_visit_prep():
        from jarvis.health_product.visit_prep import build_visit_prep

        return build_visit_prep()

    @app.get("/api/health/backups")
    def health_backups():
        from jarvis.health_product.backup import history

        return history()

    @app.post("/api/health/backups")
    async def health_backups_create(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not str(body.get("password") or "").strip():
            return JSONResponse(status_code=400, content={"ok": False, "message": "password required"})
        blocked = _gate_or_response(request, "backup_create", body)
        if blocked:
            return blocked
        from jarvis.health_product.backup import create

        return create(password=str(body["password"]), kind=str(body.get("kind") or "manual"), notes=str(body.get("notes") or ""))

    @app.post("/api/health/backups/{backup_id}/verify")
    def health_backups_verify(backup_id: str):
        from jarvis.health_product.backup import verify

        return verify(backup_id)

    @app.post("/api/health/backups/restore-preview")
    async def health_backups_restore_preview(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not str(body.get("password") or "").strip():
            return JSONResponse(status_code=400, content={"ok": False, "message": "password required"})
        blocked = _gate_or_response(request, "backup_restore", body)
        if blocked:
            return blocked
        from jarvis.health_product.backup import restore_preview

        out = restore_preview(
            backup_id=str(body.get("backup_id") or ""),
            path=str(body.get("path") or ""),
            password=str(body["password"]),
        )
        if out.get("ok") is False:
            return JSONResponse(status_code=400, content=out)
        return out

    @app.post("/api/health/backups/restore")
    async def health_backups_restore(request: Request):
        body = await request.json()
        if not isinstance(body, dict) or not str(body.get("password") or "").strip():
            return JSONResponse(status_code=400, content={"ok": False, "message": "password required"})
        blocked = _gate_or_response(request, "backup_restore", body)
        if blocked:
            return blocked
        from jarvis.health_product.backup import restore

        out = restore(
            password=str(body["password"]),
            backup_id=str(body.get("backup_id") or ""),
            path=str(body.get("path") or ""),
            mode=str(body.get("mode") or "merge"),
            confirm=bool(body.get("confirm")),
        )
        if out.get("ok") is False:
            code = 409 if out.get("confirm_required") else 400
            return JSONResponse(status_code=int(out.get("status_code") or code), content=out)
        return out

    @app.get("/api/health/backups/integrity")
    def health_backups_integrity():
        from jarvis.health_product.backup import integrity_report

        return integrity_report()

    @app.get("/api/health/auth/status")
    def health_auth_status(request: Request):
        from jarvis.health_product import gate

        return gate.status(request)

    @app.post("/api/health/auth/step-up")
    async def health_auth_step_up(request: Request):
        body = await request.json()
        if not isinstance(body, dict):
            body = {}
        from jarvis.health_product import gate

        return gate.step_up(request, pin=str(body.get("pin") or body.get("password") or ""), op=str(body.get("op") or "*"))

    @app.get("/api/health/records/{table}/{item_id}/provenance")
    def health_record_provenance(table: str, item_id: str):
        from jarvis.health_product.provenance import describe

        row = store.get_by_id(table, item_id)
        if not row:
            return JSONResponse(status_code=404, content={"ok": False, "message": "record not found"})
        return {"ok": True, "provenance": describe(row), "disclaimer": DISCLAIMER}

    @app.post("/api/health/records/{table}/{item_id}/confirm")
    def health_record_confirm(table: str, item_id: str, request: Request):
        op_map = {
            "family_history": "edit_family_history",
            "medications": "edit_medications",
            "conditions": "edit_conditions",
            "allergies": "edit_allergies",
        }
        op = op_map.get(table)
        if op:
            blocked = _gate_or_response(request, op)
            if blocked:
                return blocked
        from jarvis.health_product.provenance import mark_confirmed

        row = mark_confirmed(table, item_id)
        if not row:
            return JSONResponse(status_code=404, content={"ok": False, "message": "record not found"})
        return {"ok": True, "record": row, "disclaimer": DISCLAIMER}
