"""Guided Repair Phase 2 — confidence, preview, maintenance, knowledge, monitoring."""

from __future__ import annotations

import time

import pytest


@pytest.fixture()
def repair_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    from jarvis.repair_product import modules, store
    from jarvis.repair_product.registry import clear_registry_for_tests

    store.REPAIR_DIR = tmp_path / "repair_product"
    store.HISTORY_PATH = store.REPAIR_DIR / "history.jsonl"
    store.ISSUES_PATH = store.REPAIR_DIR / "issues.json"
    store.LEARNING_PATH = store.REPAIR_DIR / "learning.json"
    store.AUTO_APPROVE_PATH = store.REPAIR_DIR / "auto_approve.json"
    store.KNOWLEDGE_PATH = store.REPAIR_DIR / "knowledge.json"
    store.ROOT_CAUSES_PATH = store.REPAIR_DIR / "root_causes.json"
    store.MAINTENANCE_PATH = store.REPAIR_DIR / "maintenance.json"
    store.MONITORS_PATH = store.REPAIR_DIR / "monitors.json"
    store.ensure_dirs()
    clear_registry_for_tests()
    modules._REGISTERED = False
    modules.register_all()
    return tmp_path


def test_confidence_reasons_and_impact(repair_data):
    from jarvis.repair_product.engine import prepare_issue, preview_repair
    from jarvis.repair_product.registry import DetectedIssue

    det = DetectedIssue(
        module_id="mission_control_cache",
        subsystem="mission_control",
        title="Stale cache",
        summary="series stale",
        severity="warning",
        code="stale_cache",
    )
    out = prepare_issue(det)
    assert out["ok"]
    panel = out["panel"]
    assert panel["confidence_reasons"]
    assert "First occurrence" in " ".join(panel["confidence_reasons"]) or panel["confidence"] <= 0.6
    assert panel["impact"]["affected"]
    assert panel["impact"]["not_affected"]
    assert panel["priority"]
    assert panel["dependency"]["chain"]
    assert panel["rollback"]["kind"] in ("available", "unavailable", "partial")
    prev = preview_repair(out["issue"]["id"])
    assert prev["ok"] and prev["preview"] is True and prev["modifies_system"] is False
    assert prev["commands"]


def test_maintenance_mode_and_export(repair_data):
    from jarvis.repair_product import maintenance
    from jarvis.repair_product.export_bundle import build_bundle, write_bundle

    en = maintenance.enable(reason="rebuilding_indexes", note="test")
    assert en["enabled"] is True
    assert maintenance.should_suppress_recommendations() is True
    bundle = build_bundle(approved_sensitive=False)
    assert "health_product_status" not in bundle or bundle["privacy"]["includes_health"] is False
    assert bundle["privacy"]["includes_memory"] is False
    written = write_bundle()
    assert written["ok"] and written["bytes"] > 100
    dis = maintenance.disable(run_verification=True)
    assert dis["enabled"] is False
    assert dis.get("verification") is not None


def test_monitoring_after_verified_repair(repair_data):
    from jarvis.repair_product.engine import execute_repair, prepare_issue
    from jarvis.repair_product.monitoring import status, tick
    from jarvis.repair_product.registry import DetectedIssue

    det = DetectedIssue(
        module_id="caches_temp",
        subsystem="system",
        title="Clean temp",
        code="tmp",
        summary="tmp",
    )
    issue_id = prepare_issue(det)["issue"]["id"]
    done = execute_repair(issue_id, approved=True)
    assert done.get("verified") is True
    assert done.get("monitoring", {}).get("ok") is True
    st = status(issue_id)
    assert "Monitoring" in st.get("display", "") or st.get("monitoring")
    # Force checkpoints due
    mon = st["monitoring"]
    for cp in mon.get("checkpoints") or []:
        cp["at"] = time.time() - 1
    from jarvis.repair_product import store

    store.save_monitor(issue_id, mon)
    store.update_issue(issue_id, {"monitoring": mon})
    tick(now=time.time() + 10)
    # Eventually stable or still monitoring — must not lie
    again = status(issue_id)
    assert again["ok"]


def test_knowledge_reputation_root_causes(repair_data):
    from jarvis.repair_product import knowledge, reputation, root_causes
    from jarvis.repair_product.engine import execute_repair, prepare_issue
    from jarvis.repair_product.registry import DetectedIssue

    det = DetectedIssue(module_id="caches_temp", subsystem="system", title="Clean temp", code="tmp", summary="x")
    issue_id = prepare_issue(det)["issue"]["id"]
    execute_repair(issue_id, approved=True)
    arts = knowledge.search("temp")
    assert arts
    reps = reputation.all_reputations()
    assert any(r["module_id"] == "caches_temp" for r in reps)
    root_causes.ensure_seeded()
    assert root_causes.lookup("provider_ollama", "provider_offline")


def test_history_search_filters(repair_data):
    from jarvis.repair_product import store
    from jarvis.repair_product.engine import execute_repair, prepare_issue
    from jarvis.repair_product.registry import DetectedIssue

    det = DetectedIssue(module_id="caches_temp", subsystem="system", title="Clean temp", code="tmp", summary="x")
    execute_repair(prepare_issue(det)["issue"]["id"], approved=True)
    rows = store.list_history(subsystem="system", successful=True, q="temp")
    assert rows


def test_priority_sort(repair_data):
    from jarvis.repair_product.impact import sort_by_priority

    rows = sort_by_priority(
        [
            {"priority": "low", "title": "a"},
            {"priority": "critical", "title": "b"},
            {"priority": "medium", "title": "c"},
        ]
    )
    assert rows[0]["priority"] == "critical"
