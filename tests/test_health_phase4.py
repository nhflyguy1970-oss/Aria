"""Health Phase 4 — foundations through backup/visit prep; isolated temp DB only."""

from __future__ import annotations

import pytest


@pytest.fixture()
def health_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("JARVIS_HEALTH_STEP_UP", "0")
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    from jarvis.health_product import store

    monkeypatch.setattr(store, "HEALTH_DIR", tmp_path / "health_product")
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "health_product" / "health.db")
    monkeypatch.setattr(store, "DOCS_DIR", tmp_path / "health_product" / "documents")
    store.reset_migration_cache()
    store.ensure_dirs()
    return tmp_path


def test_schema_version_and_provenance_columns(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.provenance import describe, stamp

    assert store.schema_version() == "4"
    cols = store.table_columns_safe("medications")
    for c in ("provenance", "confidence", "confirmed", "person_id", "source_system", "external_id", "device_id"):
        assert c in cols
    med = store.upsert_medication({"name": "Metformin", "status": "current"})
    assert med.get("provenance")
    assert med.get("confidence")
    badge = describe(med)
    assert badge.get("badge")


def test_export_includes_phase4_tables(health_data):
    from jarvis.health_product import store

    store.upsert_family_history({"relation": "father", "condition": "Diabetes"})
    store.upsert_preventive({"name": "Colonoscopy", "slug": "colonoscopy", "last_done": "2020-01-01", "interval_months": 120})
    store.add_nutrition({"kind": "meal", "description": "oatmeal", "meal_slot": "breakfast"})
    bundle = store.export_bundle()
    assert bundle["schema_version"] == "4"
    assert bundle["family_history"]
    assert bundle["preventive_care"]
    assert bundle["nutrition_log"]
    assert "calories" not in bundle["nutrition_log"][0]


def test_family_history_nl_confirm_search_timeline(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.engine import ingest_message
    from jarvis.health_product.timeline import build_timeline

    out = ingest_message("My father had diabetes.")
    assert out.get("confirm_required") is True
    assert not store.list_table("family_history")
    ingest_message("yes")
    rows = store.list_table("family_history")
    assert any(r["condition"].lower().startswith("diabetes") for r in rows)
    hits = store.search_all("diabetes")
    assert any(h["source"] == "family_history" for h in hits)
    tl = build_timeline(category="family_history")
    assert any(i["source"] == "family_history" for i in tl["items"])
    summary = ingest_message("What runs in my family?")
    assert summary["intent"] == "family_history"
    assert "diabetes" in summary["message"].lower()


def test_preventive_due_and_last_colonoscopy(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.engine import ingest_message
    from jarvis.health_product.preventive import save
    from jarvis.health_product.timeline import build_timeline

    save({"name": "Colonoscopy", "slug": "colonoscopy", "last_done": "2015-06-01", "interval_months": 120})
    due = ingest_message("Am I due for any screenings?")
    assert due["intent"] == "preventive"
    last = ingest_message("When was my last colonoscopy?")
    assert "2015" in last["message"] or "colonoscop" in last["message"].lower()
    hits = store.search_all("colonoscopy")
    assert any(h["source"] == "preventive_care" for h in hits)
    tl = build_timeline(category="preventive")
    assert any(i["source"] == "preventive" for i in tl["items"])


def test_nutrition_nl_not_medication(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.engine import ingest_message
    from jarvis.health_product.timeline import build_timeline

    out = ingest_message("I had oatmeal for breakfast.")
    assert out["ok"]
    assert store.list_table("nutrition_log")
    assert not store.list_table("medications")
    assert not store.list_table("dose_logs")
    water = ingest_message("I drank 80 ounces of water.")
    assert water["ok"]
    beer = ingest_message("I had three beers.")
    assert beer["ok"]
    kinds = {r["kind"] for r in store.list_table("nutrition_log")}
    assert "meal" in kinds and "water" in kinds and "alcohol" in kinds
    for row in store.list_table("nutrition_log"):
        assert "calories" not in row or row.get("calories") in (None, "")
    tl = build_timeline(category="nutrition")
    assert any(i["source"] == "nutrition" for i in tl["items"])
    habits = ingest_message("What are my nutrition habits?")
    assert habits["intent"] in ("nutrition", "nutrition_habits")


def test_insights_observations_safe_language(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.engine import ingest_message
    from jarvis.health_product.patterns import FORBIDDEN_PHRASINGS, build_insights

    # Seed enough co-occurrence for sleep/headache style patterns
    for i in range(5):
        day = f"2026-07-{10+i:02d}"
        store.upsert_checkin({"day": day, "sleep_hours": 5.0, "mood": 4, "exercise": "walk", "water": ""})
        store.add_symptom({"name": "headache", "day": day, "notes": "morning"})
        store.add_vital("blood_sugar", 140 + i, day=day)
    store.add_activity({"kind": "walking", "duration_min": 30, "day": "2026-07-12", "title": "Walk"})
    insights = build_insights(days=60)
    assert insights["ok"]
    blob = insights["message"].lower()
    assert "observation" in blob or "educational" in blob
    for bad in ("you have diabetes", "caused by", "you should take"):
        assert bad not in blob
    # Generated observation statements should not claim diagnosis
    for row in store.list_table("health_observations"):
        stmt = (row.get("statement") or "").lower()
        assert "diagnos" not in stmt
        assert not stmt.startswith("you have")
    chat = ingest_message("Do you see any patterns?")
    assert chat["intent"] == "insights"


def test_visit_prep_and_report(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.engine import ingest_message
    from jarvis.health_product.reports import report_html
    from jarvis.health_product.visit_prep import build_visit_prep

    store.upsert_medication({"name": "Metformin", "status": "current"})
    store.add_symptom({"name": "knee pain", "day": "2026-07-01"})
    store.add_doctor_question("Ask about A1C")
    store.add_lab({"name": "A1C", "value": 6.4, "units": "%", "day": "2026-06-01"})
    prep = build_visit_prep(since="2026-01-01")
    assert prep["ok"]
    assert "Metformin" in prep["message"]
    assert "knee pain" in prep["message"].lower() or prep["symptoms"]
    assert "not a physician" in prep["message"].lower() or "disclaimer" in prep
    html = report_html("visit_prep")
    assert "physician" in html.lower() or "visit" in html.lower()
    assert "not a physician" in html.lower() or "disclaimer" in html.lower() or "Aria" in html
    chat = ingest_message("Prepare me for tomorrow's appointment.")
    assert chat["intent"] in ("visit_prep", "doctor_visit")


def test_backup_encrypt_restore_confirm(health_data, monkeypatch):
    pytest.importorskip("cryptography")
    from jarvis.health_product import backup, store

    store.upsert_medication({"name": "Metformin", "status": "current"})
    store.add_nutrition({"kind": "meal", "description": "eggs"})
    created = backup.create(password="test-pass-123", kind="manual")
    assert created["ok"]
    bak = created["backup"]
    assert __import__("pathlib").Path(bak["path"]).is_file()
    v = backup.verify(bak["id"])
    assert v["ok"] is True
    # Wrong password
    with pytest.raises(Exception):
        backup.decrypt_bundle(__import__("json").loads(__import__("pathlib").Path(bak["path"]).read_text()), "wrong")
    # Restore without confirm
    refused = backup.restore(password="test-pass-123", backup_id=bak["id"], confirm=False)
    assert refused.get("confirm_required") is True
    # Restore with confirm
    done = backup.restore(password="test-pass-123", backup_id=bak["id"], confirm=True, mode="merge")
    assert done["ok"]
    assert store.list_table("restore_log")


def test_gate_disabled_by_default_in_tests(health_data):
    from jarvis.health_product.gate import health_step_up_enabled, require, status

    assert health_step_up_enabled() is False
    assert require(None, "export_record") is None
    st = status(None)
    assert st["ok"]


def test_phase4_router_and_handlers():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import action_names
    from jarvis.router import _natural_intent_route

    ensure_handlers_loaded()
    names = action_names()
    for action in (
        "health_family_history",
        "health_preventive",
        "health_nutrition",
        "health_insights",
        "health_visit_prep",
        "health_backup",
        "health_restore",
        "health_integrity",
    ):
        assert action in names

    r = _natural_intent_route("When was my last colonoscopy?")
    assert r and r["action"] == "health_preventive"
    r = _natural_intent_route("Does diabetes run in my family?")
    assert r and r["action"] == "health_family_history"
    r = _natural_intent_route("Prepare me for tomorrow's appointment.")
    assert r and r["action"] in ("health_visit_prep", "health_doctor_visit")
    r = _natural_intent_route("Am I due for any screenings?")
    assert r and r["action"] == "health_preventive"


def test_confirmed_record_guard(health_data):
    from jarvis.health_product.provenance import ConfirmedRecordGuard, guard_update

    existing = {"id": "x", "confirmed": 1, "name": "Metformin"}
    with pytest.raises(ConfirmedRecordGuard):
        guard_update(existing, {"name": "Metformin", "dose": "1000"})
    ok = guard_update(existing, {"name": "Metformin", "dose": "1000"}, allow_confirmed=True)
    assert ok["dose"] == "1000"


def test_live_write_still_blocked(monkeypatch):
    from pathlib import Path

    from jarvis.config import _DATA_DEFAULT
    from jarvis.health_product import store
    from jarvis.health_product.trust import HealthWriteBlocked, is_live_record

    live = Path(_DATA_DEFAULT) / "health_product" / "health.db"
    assert is_live_record(live)
    monkeypatch.setattr(store, "DB_PATH", live)
    assert is_live_record()
    with pytest.raises(HealthWriteBlocked):
        store.upsert_family_history({"relation": "father", "condition": "SHOULD_NOT_WRITE"})
