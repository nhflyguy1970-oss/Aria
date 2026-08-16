"""Health product — local PHR store, NL ingest, reports, search facet."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def health_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    from jarvis.health_product import store

    monkeypatch.setattr(store, "HEALTH_DIR", tmp_path / "health_product")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "health_product" / "health.db")
    monkeypatch.setattr(store, "DOCS_DIR", tmp_path / "health_product" / "documents")
    store.ensure_dirs()
    return tmp_path


def test_terminology_and_disclaimer():
    from jarvis.health_product.terminology import BOUNDARIES, DISCLAIMER, MENTAL_MODEL, TERMINOLOGY

    assert TERMINOLOGY["product"] == "Health"
    assert "Personal Health Record" in TERMINOLOGY["record"]
    assert "does not diagnose" in DISCLAIMER.lower() or "not a physician" in DISCLAIMER.lower()
    assert "medications" in BOUNDARIES["owns"]
    assert "emr" in BOUNDARIES["does_not_own"]
    assert "journal" in MENTAL_MODEL


def test_checkin_meds_vitals_roundtrip(health_data):
    from jarvis.health_product import store

    chk = store.upsert_checkin({"overall": 7, "weight": 232, "bp_systolic": 126, "bp_diastolic": 78, "blood_sugar": 121})
    assert chk["weight"] == 232
    again = store.get_checkin()
    assert again["blood_sugar"] == 121
    store.upsert_medication({"name": "Metformin", "strength": "500 mg", "status": "current"})
    store.upsert_supplement({"name": "Vitamin D", "dose": "2000 IU", "status": "current"})
    store.add_vital("blood_pressure", 126, value2=78, units="mmHg")
    store.add_lab({"name": "A1C", "value": 6.4, "units": "%"})
    meds = store.list_table("medications", "status=?", ("current",))
    assert any(m["name"] == "Metformin" for m in meds)
    hits = store.search_all("metformin")
    assert hits


def test_nl_log_and_never_invent(health_data):
    from jarvis.health_product.engine import ingest_message, medications_summary
    from jarvis.health_product.parser import parse_health_utterance

    parsed = parse_health_utterance("My sugar was 121 this morning.")
    assert parsed["checkin"]["blood_sugar"] == 121
    out = ingest_message("My pressure was 126 over 78.")
    assert out["ok"] is True
    assert any("blood_pressure" in a for a in out["applied"])
    ingest_message("I started taking Vitamin D.")
    ingest_message("I stopped taking Magnesium.")
    pending = ingest_message("My doctor increased my Metformin.")
    assert pending.get("confirm_required") is True
    assert "Metformin" in (pending.get("message") or "")
    confirmed = ingest_message("yes")
    assert confirmed.get("ok") is True
    meds = medications_summary()
    assert "disclaimer" in meds["message"].lower() or "physician" in meds["disclaimer"].lower()
    empty = ingest_message("What medications am I taking?")
    assert empty["intent"] == "medications"
    assert "Metformin" in empty["message"]


def test_doctor_and_emergency_include_disclaimer(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.engine import doctor_visit_summary, emergency_summary
    from jarvis.health_product.reports import report_html

    store.set_profile({"name": "Jeff", "blood_type": "O+", "dob": "1970-01-01"})
    store.upsert_medication({"name": "Metformin", "status": "current", "dose": "500 mg"})
    store.upsert_allergy({"name": "Penicillin", "kind": "drug", "reaction": "rash"})
    doc = doctor_visit_summary()
    ice = emergency_summary()
    assert doc["ok"] and ice["ok"]
    assert "Metformin" in doc["message"]
    assert "Penicillin" in ice["message"]
    assert "not a physician" in doc["disclaimer"].lower() or "informational" in doc["disclaimer"].lower()
    html = report_html("emergency")
    assert "Emergency" in html
    assert "Jeff" in html


def test_health_required_product_and_search_facet():
    from jarvis.product_registration import REQUIRED_PRODUCTS
    from jarvis.search_product.retrievers import RETRIEVERS
    from jarvis.search_product.terminology import FACETS

    assert "health_product" in REQUIRED_PRODUCTS
    assert "health" in FACETS
    assert "health" in RETRIEVERS


def test_health_handlers_registered():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import action_names

    ensure_handlers_loaded()
    names = action_names()
    for action in (
        "health_home",
        "health_log",
        "health_today",
        "health_medications",
        "health_doctor_visit",
        "health_emergency",
        "health_timeline",
        "health_coach",
        "health_consult",
        "health_question",
        "health_confirm",
        "health_export",
        "health_reminders",
        "health_dashboard",
        "health_trends",
        "health_safety",
        "health_activity",
        "health_workouts",
        "health_second_opinion",
    ):
        assert action in names


def test_router_health_natural_intents():
    from jarvis.router import _natural_intent_route

    r = _natural_intent_route("My sugar was 121 this morning.")
    assert r and r["action"] == "health_log"
    r = _natural_intent_route("Prepare for my doctor appointment.")
    assert r and r["action"] == "health_doctor_visit"
    r = _natural_intent_route("What medications am I taking?")
    assert r and r["action"] == "health_medications"
    r = _natural_intent_route("Graph my weight.")
    assert r and r["action"] == "health_graph"
    r = _natural_intent_route("Show my health timeline.")
    assert r and r["action"] == "health_timeline"
    r = _natural_intent_route("Wellness coach.")
    assert r and r["action"] == "health_coach"
    r = _natural_intent_route("Remind me to ask my doctor about my A1C.")
    assert r and r["action"] == "health_question"
    r = _natural_intent_route("Review my last six months of blood pressure.")
    assert r and r["action"] == "health_consult"
    r = _natural_intent_route("How have I been doing?")
    assert r and r["action"] == "health_dashboard"
    r = _natural_intent_route("Have I exercised enough?")
    assert r and r["action"] == "health_activity"
    r = _natural_intent_route("Did I lose weight?")
    assert r and r["action"] == "health_graph"
    r = _natural_intent_route("Get a second opinion.")
    assert r and r["action"] == "health_second_opinion"
    r = _natural_intent_route("What should I ask my doctor?")
    assert r and r["action"] == "health_doctor_visit"


def test_medication_confirmation_and_reject(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.engine import ingest_message

    out = ingest_message("I started Metformin.")
    assert out.get("confirm_required") is True
    assert not store.list_table("medications")
    ingest_message("no")
    assert not store.list_table("medications")
    ingest_message("I started Metformin.")
    ingest_message("yes")
    meds = store.list_table("medications", "status=?", ("current",))
    assert any(m["name"] == "Metformin" for m in meds)


def test_timeline_questions_coach_consult_preview(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.coach import wellness_coach
    from jarvis.health_product.consult import latest_preview, preview_consultation
    from jarvis.health_product.engine import doctor_visit_summary, ingest_message
    from jarvis.health_product.timeline import build_timeline

    ingest_message("My sugar was 118.")
    ingest_message("I slept six hours.")
    q = ingest_message("Remind me to ask my doctor about knee pain.")
    assert q["intent"] == "doctor_question"
    timeline = build_timeline()
    assert timeline["ok"]
    assert timeline["items"]
    visit = doctor_visit_summary()
    assert "knee pain" in visit["message"].lower()
    coach = wellness_coach()
    assert coach["ok"]
    assert "not a diagnosis" in coach["boundary"].lower() or "not a diagnosis" in coach["message"].lower() or "educational" in coach["message"].lower()
    preview = preview_consultation("Review my blood sugar trend.", level="sanitized")
    assert preview["confirm_required"] is True
    assert preview["leaves_device"] is True or preview["shared"]["privacy_level"] in ("sanitized", "local_only", "full")
    assert "name" not in (preview["shared"].get("profile") or {})
    assert latest_preview()
    assert store.list_table("consultations")


def test_pytest_cannot_write_live_health_record(monkeypatch):
    from jarvis.config import _DATA_DEFAULT
    from jarvis.health_product import store
    from jarvis.health_product.trust import HealthWriteBlocked, is_live_record

    live = Path(_DATA_DEFAULT) / "health_product" / "health.db"
    assert is_live_record(live)
    monkeypatch.setattr(store, "DB_PATH", live)
    assert is_live_record()
    with pytest.raises(HealthWriteBlocked):
        store.upsert_medication({"name": "SHOULD_NOT_LAND_IN_LIVE_PHR", "status": "current"})


def test_export_bundle_includes_core_tables(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.engine import export_summary

    store.upsert_checkin({"overall": 8, "weight": 230})
    bundle = export_summary()["bundle"]
    assert "medications" in bundle
    assert "checkins" in bundle
    assert bundle["checkins"]
    assert "activities" in bundle
    assert "workouts" in bundle
    assert "goals" in bundle


def test_activity_workout_goals_journal_safety(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.dashboard import dashboard_payload
    from jarvis.health_product.engine import ingest_message
    from jarvis.health_product.safety import scan_interactions
    from jarvis.health_product.timeline import build_timeline
    from jarvis.health_product.trends import build_trends
    from jarvis.health_product.workouts import progression

    walk = ingest_message("I walked 30 minutes.")
    assert walk["ok"]
    assert any("activity" in a for a in walk["applied"])
    wo = ingest_message("I did an upper body workout.")
    assert wo["ok"]
    store.add_workout(
        {"title": "Push", "template": "push", "body_part": "upper"},
        [{"exercise": "band row", "sets": 3, "reps": 12, "weight": 0, "band_color": "red", "resistance": "medium"}],
    )
    store.upsert_goal({"title": "Walk 8000 steps", "kind": "steps", "target_value": 8000, "status": "active"})
    store.add_health_journal("I felt dizzy.")
    store.add_knowledge({"title": "AHA walking note", "source": "aha", "body": "Walk most days."})
    store.upsert_provider({"name": "Dr Example", "specialty": "primary", "phone": "555-0100"})
    store.add_procedure({"name": "Stress test", "kind": "Stress test", "result": "pending"})
    ingest_message("yes")  # no-op if nothing pending
    store.upsert_medication({"name": "Metformin", "status": "current"})
    store.upsert_supplement({"name": "Fish Oil", "status": "current"})
    dash = dashboard_payload()
    assert dash["ok"] and dash["intent"] == "dashboard"
    assert dash["goals"]
    trends = build_trends()
    assert trends["ok"]
    timeline = build_timeline()
    sources = {i["source"] for i in timeline["items"]}
    assert "activities" in sources
    assert "health_journal" in sources
    assert "workouts" in sources
    prog = progression()
    assert prog["frequency_28"] >= 1
    safety = scan_interactions()
    assert safety["ok"]
    assert safety["offline"] is True
    assert "pharmacist" in safety["boundary"].lower()
    hits = store.search_all("dizzy")
    assert any(h["source"] == "health_journal" for h in hits)
    hits = store.search_all("AHA walking")
    assert any(h["source"] == "knowledge" for h in hits)


def test_phase3_milestones_scorecard_adherence_recovery(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.dashboard import medication_adherence
    from jarvis.health_product.engine import ingest_message
    from jarvis.health_product.milestones import discover_milestones
    from jarvis.health_product.scorecard import build_scorecard
    from jarvis.health_product.timeline import build_timeline

    # Seed weight loss large enough for a milestone
    store.add_vital("weight", 240, units="lb")
    store.add_vital("weight", 228, units="lb")
    for _ in range(25):
        store.add_workout({"title": "Band", "template": "full_body"})
    store.add_activity({"kind": "walking", "duration_min": 30, "distance": 1000, "distance_units": "mi", "title": "Long walk series"})
    store.add_lab({"name": "A1C", "value": 7.1, "units": "%"})
    store.add_lab({"name": "A1C", "value": 6.5, "units": "%"})
    store.upsert_medication({"name": "Metformin", "status": "current", "start_date": "2020-01-01"})
    store.log_dose("Metformin", status="taken")
    store.log_dose("Metformin", status="missed")
    store.add_recovery({"kind": "injury", "title": "Knee strain", "body_part": "knee", "pain": 4, "mobility": "limited"})
    store.add_visit(
        {
            "day": "2026-07-01",
            "physician": "Dr Example",
            "reason": "Follow-up",
            "summary": "Discussed labs",
            "instructions": "Continue walking",
            "next_appointment": "2026-10-01",
        }
    )

    ms = discover_milestones(persist=True)
    assert ms["ok"]
    titles = " ".join(str(m.get("title") or "") for m in ms["milestones"]).lower()
    assert "10 pounds" in titles or "a1c" in titles or "workouts" in titles

    sc = build_scorecard(days=28)
    assert sc["ok"] and sc["intent"] == "scorecard"
    assert "not a medical score" in (sc.get("boundary") or "").lower()
    assert sc.get("scores")

    adh = medication_adherence(days=7)
    assert adh["current_meds"] >= 1
    assert adh["taken_today"] or adh["missed_today"]
    assert adh.get("weekly_pct") is not None

    taken = ingest_message("I took Metformin.")
    assert taken["ok"]
    assert any("dose taken" in a for a in taken.get("applied") or [])

    recovery = ingest_message("Recovering from knee strain.")
    assert recovery["ok"]
    assert any("recovery" in a for a in recovery.get("applied") or [])

    tl = build_timeline(category="medications")
    assert tl["ok"]
    assert any(i["source"] in ("medications",) or "dose" in str(i.get("title") or "").lower() or "missed" in str(i.get("title") or "").lower() for i in tl["items"])
    tl_rec = build_timeline(category="recovery")
    assert any(i["source"] == "recovery" for i in tl_rec["items"])
    last = ingest_message("When was my last doctor visit?")
    assert last["intent"] == "last_visit"
    assert "dr example" in last["message"].lower() or "follow-up" in last["message"].lower()


def test_phase3_router_chat_routes():
    from jarvis.router import _natural_intent_route

    r = _natural_intent_route("How's my health?")
    assert r and r["action"] == "health_dashboard"
    r = _natural_intent_route("What changed this month?")
    assert r and r["action"] == "health_dashboard"
    r = _natural_intent_route("Have I improved?")
    assert r and r["action"] == "health_dashboard"
    r = _natural_intent_route("When was my last doctor visit?")
    assert r and r["action"] == "health_last_visit"
    r = _natural_intent_route("What medications am I take?")
    assert r and r["action"] == "health_medications"
    r = _natural_intent_route("Wellness scorecard.")
    assert r and r["action"] == "health_scorecard"
    r = _natural_intent_route("Show my milestones.")
    assert r and r["action"] == "health_milestones"
    r = _natural_intent_route("Medication adherence.")
    assert r and r["action"] == "health_adherence"


def test_phase3_handlers_registered():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import action_names

    ensure_handlers_loaded()
    names = action_names()
    for action in ("health_scorecard", "health_milestones", "health_adherence", "health_last_visit"):
        assert action in names
