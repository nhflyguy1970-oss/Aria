"""Health V1.0 maturity — lifelong PHR trust regressions (isolated temp DB only)."""

from __future__ import annotations

from datetime import date, timedelta

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


def test_list_vitals_prefers_recent_when_capped(health_data):
    from jarvis.health_product import store

    old = (date.today() - timedelta(days=365 * 10)).isoformat()
    new = date.today().isoformat()
    store.add_vital("weight", 250, day=old)
    store.add_vital("weight", 220, day=new)
    rows = store.list_vitals(kind="weight", limit=1)
    assert len(rows) == 1
    assert rows[0]["day"] == new
    assert float(rows[0]["value"]) == 220.0


def test_export_bundle_is_complete_no_silent_truncation(health_data):
    from jarvis.health_product import store

    for i in range(12):
        store.add_vital("blood_pressure", 120 + i, value2=80, day=(date.today() - timedelta(days=i)).isoformat())
    bundle = store.export_bundle()
    assert bundle.get("complete") is True
    assert bundle["record_counts"]["vitals"] == store.table_row_count("vitals")
    assert len(bundle["vitals"]) == store.table_row_count("vitals")
    # Documents keep full extracted text (not preview-only)
    store.add_document({"title": "Lab", "kind": "lab", "path": "/tmp/x.txt", "extracted_text": "A" * 800})
    bundle2 = store.export_bundle()
    assert len(bundle2["documents"][0].get("extracted_text") or "") == 800


def test_backup_restore_roundtrip_vitals(health_data):
    pytest.importorskip("cryptography")
    from jarvis.health_product import backup, store

    store.add_vital("weight", 231.5, day="2020-01-15")
    store.add_vital("weight", 220.0, day=date.today().isoformat())
    before = store.table_row_count("vitals")
    created = backup.create(password="maturity-roundtrip", kind="manual")
    assert created["ok"] and created.get("complete")
    with store._lock:
        conn = store.connect()
        try:
            conn.execute("DELETE FROM vitals")
            conn.commit()
        finally:
            conn.close()
    assert store.table_row_count("vitals") == 0
    refused = backup.restore(password="maturity-roundtrip", backup_id=created["backup"]["id"], confirm=False)
    assert refused.get("confirm_required")
    done = backup.restore(password="maturity-roundtrip", backup_id=created["backup"]["id"], confirm=True)
    assert done["ok"]
    assert store.table_row_count("vitals") == before
    assert any(float(v["value"]) == 231.5 for v in store.list_vitals(kind="weight", limit=None))


def test_insights_widen_window_for_sparse_lifelong_logs(health_data):
    from jarvis.health_product import store
    from jarvis.health_product.patterns import build_insights

    # Sparse history spanning years — short window alone would look empty
    for i in range(20):
        day = (date.today() - timedelta(days=30 * i)).isoformat()
        store.add_vital("weight", 240 - i * 0.8, day=day)
        store.add_vital("blood_pressure", 145 - i * 0.5, value2=90, day=day)
    insights = build_insights(days=45)
    assert insights["ok"]
    assert insights.get("window_days", 45) >= 45
    assert "observation" in insights["message"].lower() or "educational" in insights["message"].lower()
    assert "not a physician" in insights["message"].lower()
