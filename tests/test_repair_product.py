"""Guided Repair Engine — approval, verification, no false success."""

from __future__ import annotations

import pytest


@pytest.fixture()
def repair_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    from jarvis.repair_product import store
    from jarvis.repair_product.registry import clear_registry_for_tests
    from jarvis.repair_product import modules

    # Re-bind store paths
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


def test_modules_registered(repair_data):
    from jarvis.repair_product.registry import all_modules

    ids = {m.id for m in all_modules()}
    assert "provider_ollama" in ids
    assert "scheduler" in ids
    assert "search_index" in ids
    assert "destructive_guard" in ids
    assert "health_store" in ids


def test_approval_required_and_no_false_success(repair_data):
    from jarvis.repair_product.engine import execute_repair, prepare_issue
    from jarvis.repair_product.registry import DetectedIssue

    det = DetectedIssue(
        module_id="mission_control_cache",
        subsystem="mission_control",
        title="Stale Mission Control cache",
        summary="test",
        severity="warning",
        code="stale_cache",
    )
    prepared = prepare_issue(det)
    assert prepared["ok"]
    issue_id = prepared["issue"]["id"]
    panel = prepared["panel"]
    assert panel["evidence"] is not None
    assert panel["plan_steps"]
    assert "confidence_label" in panel

    blocked = execute_repair(issue_id, approved=False)
    assert blocked.get("approval_required") is True
    assert blocked.get("success_claimed") is not True

    done = execute_repair(issue_id, approved=True, actor="jeff")
    # Success only if verified (may enter monitoring afterward)
    if done.get("ok"):
        assert done.get("verified") is True
        assert done.get("success_claimed") is True
        assert done.get("result") == "verified_success"
        assert done.get("issue", {}).get("state") in ("monitoring", "repair_successful")
    else:
        assert done.get("success_claimed") is False
        assert done.get("result") in ("failed", "executed_unverified", "not_executed")


def test_destructive_requires_explicit_confirm(repair_data):
    from jarvis.repair_product.engine import execute_repair, prepare_issue
    from jarvis.repair_product.registry import DetectedIssue

    det = DetectedIssue(
        module_id="destructive_guard",
        subsystem="security",
        title="Delete everything",
        summary="operator asked to wipe",
        severity="critical",
        code="wipe",
    )
    prepared = prepare_issue(det)
    issue_id = prepared["issue"]["id"]
    out = execute_repair(issue_id, approved=True, confirm_destructive=False)
    assert out.get("needs_explicit_confirmation") is True
    assert out.get("ok") is False
    forced = execute_repair(issue_id, approved=True, confirm_destructive=True)
    assert forced.get("ok") is False
    assert forced.get("success_claimed") is False
    assert forced.get("outcome", {}).get("executed") is False or forced.get("result") == "not_executed"


def test_history_and_learning(repair_data):
    from jarvis.repair_product import store
    from jarvis.repair_product.engine import execute_repair, prepare_issue
    from jarvis.repair_product.registry import DetectedIssue

    det = DetectedIssue(
        module_id="caches_temp",
        subsystem="system",
        title="Clean temp",
        summary="tmp full",
        code="tmp",
    )
    issue_id = prepare_issue(det)["issue"]["id"]
    execute_repair(issue_id, approved=True)
    hist = store.list_history(limit=10)
    assert hist
    assert "verified_ok" in hist[0]
    learn = store.learning_stats()
    assert "common_failures" in learn or "successful_repairs" in learn


def test_plan_from_event_maps_provider(repair_data):
    from jarvis.repair_product.engine import plan_from_event

    out = plan_from_event({"title": "Ollama timeout", "detail": "provider inference failed", "category": "inference"})
    assert out.get("ok")
    assert out.get("panel") or out.get("matched") is False or out.get("issue")


def test_product_status(repair_data):
    from jarvis.repair_product.engine import product_status

    st = product_status()
    assert st["ok"]
    assert st["product"] == "Guided Repair"
    assert st["modules"]
