"""Tier 2 foundation: Repair identity, Integrity truth, Planner add/focus, isolation."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path("/media/jeff/AI/jarvis")


def test_repair_room_identity_is_not_mission_control():
    registry = (ROOT / "jarvis/gui/static/workspace/registry.js").read_text(encoding="utf-8")
    furnish = (ROOT / "jarvis/gui/static/workspace/rooms/furnish.js").read_text(encoding="utf-8")
    router = (ROOT / "jarvis/gui/static/view_router.js").read_text(encoding="utf-8")
    assert 'id: "repair"' in registry
    assert 'viewId: "repair"' in registry
    assert 'id: "repair", kind: "room"' in registry.replace(" ", "") or 'id: "repair", kind: "room"' in registry
    assert 'viewId: "workstation"' not in registry.split('id: "repair"')[1].split("}")[0]
    assert "repair: \"workstation\"" not in furnish
    assert "switchMcTab?.(\"recovery\")" not in furnish
    assert "repair: \"repair\"" in router
    assert "workstation: \"mission\"" in router


def test_integrity_score_is_derived_from_findings():
    from jarvis.integrity_product.score import compute_score
    from jarvis.integrity_product.terminology import STATUS_CLEAN

    clean = compute_score({"findings": [], "status": STATUS_CLEAN})
    assert clean["overall"] == 100
    assert clean["deductions"] == []

    dirty = compute_score(
        {
            "findings": [
                {
                    "title": "Ambiguous Health dose_logs: residency morning",
                    "category": "health",
                    "uncertain": True,
                    "safe_to_remove": False,
                }
            ],
            "status": "warning",
        }
    )
    assert dirty["overall"] < 100
    assert dirty["deductions"]
    assert dirty["deductions"][0]["title"] == "Ambiguous Health dose_logs: residency morning"


def test_integrity_home_payload_exposes_findings(tmp_path, monkeypatch):
    from jarvis.integrity_product import scanner, store
    from jarvis.integrity_product.terminology import STATUS_CLEAN

    monkeypatch.setattr(store, "INTEGRITY_DIR", tmp_path)
    monkeypatch.setattr(store, "LAST_SCAN_FILE", tmp_path / "last_scan.json")
    monkeypatch.setattr(store, "HISTORY_FILE", tmp_path / "history.jsonl")
    scanner.invalidate_cache()
    store.save_last_scan(
        {
            "status": STATUS_CLEAN,
            "state": "ready",
            "clean": True,
            "scanned_at": 9e12,
            "findings": [],
            "counts": {"total": 0, "actionable": 0, "uncertain": 0, "safe_to_remove": 0},
            "score": {"overall": 100, "deductions": []},
        }
    )
    home = scanner.home_payload()
    assert home["findings"] == []
    assert home["score"]["overall"] == 100


def test_planner_add_then_snapshot_agrees(data_dir, monkeypatch):
    import jarvis.planner_store as ps

    monkeypatch.setattr(ps, "DATA_DIR", data_dir)
    monkeypatch.setattr(ps, "DB_PATH", data_dir / "planner.db")
    monkeypatch.setenv("JARVIS_PLANNER", "1")
    ps._init_db()
    task = ps.add_task("water the plants")
    snap = ps.planner_snapshot()
    texts = [t.get("text") for t in snap.get("tasks") or []]
    ids = [t.get("id") for t in snap.get("tasks") or []]
    assert task["id"] in ids
    assert "water the plants" in texts
    from jarvis.planner_services import daily_focus

    focus = daily_focus(None)
    assert focus["health"]["open_tasks"] >= 1
    assert any(t.get("id") == task["id"] for t in focus.get("top_priorities") or [])


def test_production_isolation_still_refuses_live_test_writes(monkeypatch):
    from jarvis.live_data_guard import disable_test_guard, enable_test_guard
    from jarvis.production_guard import (
        LIVE_DATA_ROOT,
        ProductionIsolationError,
        assert_owner_write_allowed,
    )
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", LIVE_DATA_ROOT)
    monkeypatch.setenv("JARVIS_ENVIRONMENT", "production")
    disable_test_guard()
    try:
        with pytest.raises(ProductionIsolationError):
            assert_owner_write_allowed("ARIA-REPAIR-E2E-PLAN-PHASE2", store="planner")
    finally:
        enable_test_guard()
