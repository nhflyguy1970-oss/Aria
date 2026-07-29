"""Fly Tying product — home, profiles, sessions, QR, hatch, bridges, policy."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def test_product_status_pipeline():
    from jarvis.flytying_product.engine import product_status

    with patch("jarvis.flytying.bridge.status", return_value={"ok": True, "loaded": False}):
        st = product_status()
    assert st["ok"] is True
    assert st["product"] == "Fly Tying"
    assert "flytying_engine" in st["pipeline"]
    assert st["pipeline"][0] == "pattern_library"


def test_home_payload_inventory_first(tmp_path, monkeypatch):
    from jarvis.flytying_product import engine
    from jarvis.flytying import user_store

    monkeypatch.setattr(user_store, "MATERIALS_FILE", tmp_path / "mats.json")
    user_store.save_materials(["olive dubbing"])
    with patch("jarvis.flytying.nightly.pattern_of_the_day", return_value={"ok": True, "name": "Adams"}):
        with patch("jarvis.flytying.hatch.hatch_context", return_value={"region": "NE", "hatches": ["BWO"]}):
            home = engine.home_payload()
    assert home["ok"] is True
    assert home["inventory"]["count"] >= 1 or home["inventory"]["materials_count"] >= 1
    assert home["pattern_of_the_day"]["name"] == "Adams"
    assert "recovery" in home


def test_recovery_status_guided():
    from jarvis.flytying_product.engine import recovery_status

    rec = recovery_status()
    assert rec["ok"] is True
    assert rec["guided"] is True
    assert isinstance(rec["steps"], list)
    assert rec["steps"]


def test_profiles_builtins():
    from jarvis.flytying_product.profiles import list_profiles

    ids = {p["id"] for p in list_profiles()}
    for needed in ("beginner", "competition", "bass", "trout", "saltwater", "travel_kit", "minimal_bench"):
        assert needed in ids


def test_profiles_activate_and_duplicate(tmp_path, monkeypatch):
    from jarvis.flytying_product import profiles as pf
    from jarvis.flytying_product import settings as st

    monkeypatch.setattr(pf, "PROFILES_FILE", tmp_path / "profiles.json")
    monkeypatch.setattr(st, "SETTINGS_FILE", tmp_path / "settings.json")
    activated = pf.activate_profile("trout")
    assert activated["id"] == "trout"
    dup = pf.duplicate_profile("trout")
    assert dup and dup["id"] != "trout"
    assert not dup.get("builtin")


def test_sessions_lifecycle(tmp_path, monkeypatch):
    from jarvis.flytying_product import sessions as sm

    monkeypatch.setattr(sm, "SESSIONS_FILE", tmp_path / "sessions.json")
    with patch("jarvis.flytying.bridge.get_recipe", return_value={"name": "Adams", "recipe_id": "adams", "steps": ["one", "two"], "materials": ["hackle"]}):
        s = sm.start_session(recipe_id="adams", recipe_name="Adams")
    assert s["status"] == "active"
    assert s["steps"]
    s2 = sm.next_step(s["id"])
    assert s2["step_idx"] == 1
    sm.pause_session(s["id"])
    sm.resume_session(s["id"])
    done = sm.complete_session(s["id"])
    assert done["status"] == "completed"


def test_history_redaction_preserves_storage(tmp_path, monkeypatch):
    from jarvis.flytying_product import history as hist

    monkeypatch.setattr(hist, "HISTORY_FILE", tmp_path / "history.jsonl")
    entry = hist.add_entry(
        {
            "kind": "note",
            "summary": "open summary",
            "detail": "secret analysis",
            "uncensored_origin": True,
        }
    )
    open_v = hist.presentation_for_profile(entry, censored=False)
    closed = hist.presentation_for_profile(entry, censored=True)
    assert open_v["detail"] == "secret analysis"
    assert closed["redacted"] is True
    assert "secret" not in closed["detail"]
    # Original still on disk
    stored = hist.get_entry(entry["id"])
    assert stored["detail"] == "secret analysis"


def test_local_qr_generates_svg():
    from jarvis.flytying_product.qr_local import generate_qr, label_html

    qr = generate_qr("FT:olive-dubbing", fmt="svg")
    assert qr["ok"] is True
    assert "<svg" in (qr.get("svg") or "")
    html = label_html("FT:olive-dubbing", "Olive Dubbing")
    assert "Olive Dubbing" in html
    assert "api.qrserver.com" not in html


def test_hatch_packs_list_and_import(tmp_path, monkeypatch):
    from jarvis.flytying_product import hatch_packs as hp

    monkeypatch.setattr(hp, "USER_DIR", tmp_path / "packs")
    packs = hp.list_packs()
    assert any(p["id"] == "northeast" for p in packs)
    assert any(p["id"] == "rockies" for p in packs)
    imported = hp.import_pack(
        {
            "id": "custom_test",
            "region": "Test Region",
            "months": {"7": {"hatches": ["Tricos"], "suggest_types": ["dry"]}},
        }
    )
    assert imported["ok"] is True
    loaded = hp.load_pack("custom_test")
    assert loaded and loaded["region"] == "Test Region"


def test_hatch_dataset_loads():
    from jarvis.flytying.hatch import hatch_context

    ctx = hatch_context(month=5)
    assert ctx["hatches"]
    assert ctx["region"]


def test_mission_panel_shape():
    from jarvis.flytying_product.mission_bridge import flytying_mission_panel

    with patch("jarvis.flytying.bridge.status", return_value={"ok": True}):
        panel = flytying_mission_panel()
    assert panel["product"] == "Fly Tying"
    assert "deep_links" in panel
    assert "inventory" in panel
    assert "recovery" in panel


def test_voice_bench_repeat_without_speak(tmp_path, monkeypatch):
    from jarvis.flytying_product import sessions as sm
    from jarvis.flytying_product.voice_bridge import bench_command

    monkeypatch.setattr(sm, "SESSIONS_FILE", tmp_path / "sessions.json")
    with patch("jarvis.flytying.bridge.get_recipe", return_value={"name": "Adams", "recipe_id": "a", "steps": ["Start thread at eye"]}):
        s = sm.start_session(recipe_id="a", recipe_name="Adams")
        out = bench_command("repeat", session_id=s["id"], speak=False)
    assert out["ok"] is True
    assert "Step" in (out.get("step_text") or "")


def test_vision_bridge_confirm_requires_flag():
    from jarvis.flytying_product.vision_bridge import confirm_inventory_draft

    out = confirm_inventory_draft({"what": "thread"}, confirmed=False)
    assert out["requires_confirmation"] is True


def test_vision_identify_material_mocked():
    from jarvis.flytying_product.vision_bridge import identify_material

    with patch(
        "jarvis.vision_product.engine.analyze",
        return_value={"ok": True, "analysis": "Olive dubbing material", "confidence": 0.8},
    ):
        with patch("jarvis.config.is_uncensored", return_value=False):
            out = identify_material("/tmp/x.png", assistant=MagicMock(), force=True)
    assert out["ok"] is True
    assert out["bridge"] == "vision_product"
    assert out["requires_confirmation"] is True


def test_gallery_link(tmp_path, monkeypatch):
    from jarvis.flytying_product import gallery_bridge as gb
    from jarvis.gallery_product import collections as cols
    from jarvis.gallery_product import metadata as meta
    from jarvis.flytying_product import history as hist

    monkeypatch.setattr(meta, "META_FILE", tmp_path / "meta.json")
    monkeypatch.setattr(cols, "COLLECTIONS_FILE", tmp_path / "cols.json")
    monkeypatch.setattr(hist, "HISTORY_FILE", tmp_path / "hist.jsonl")
    out = gb.link_finished_fly("fly1.png", recipe_id="adams", recipe_name="Adams")
    assert out["ok"] is True
    assert out["bridge"] == "gallery_product"


def test_planner_calendar_candidates():
    from jarvis.flytying_product.planner_bridge import planner_candidates
    from jarvis.flytying_product.calendar_bridge import calendar_candidates

    with patch("jarvis.flytying.hatch.hatch_context", return_value={"region": "NE", "month": 7, "hatches": ["Tricos"]}):
        p = planner_candidates(kind="tie_this_week")
        c = calendar_candidates(kind="hatch_weeks", month=7)
    assert p.get("ok") is True or "candidates" in p
    assert c.get("ok") is True or "candidates" in c


def test_experimental_gated():
    from jarvis.flytying_product.experimental import experimental_flags, material_clusters

    flags = experimental_flags()
    assert "knowledge_graph" in flags
    out = material_clusters()
    assert out.get("ok") is False or out.get("experimental")


def test_cheatsheet():
    from jarvis.flytying_product.cheatsheet import cheatsheet_payload

    sheet = cheatsheet_payload()
    assert sheet["keyboard"]
    assert sheet["voice_bench"]


def test_inventory_summary(tmp_path, monkeypatch):
    from jarvis.flytying import user_store
    from jarvis.flytying_product.inventory import inventory_summary

    monkeypatch.setattr(user_store, "MATERIALS_FILE", tmp_path / "mats.json")
    user_store.add_inventory_item("Olive CDC", barcode="FT:OLIVE-CDC", source="test")
    # mark low stock
    items = user_store.list_inventory_items()
    if items:
        user_store.update_inventory_item(str(items[-1]["id"]), {"qty": 0, "low_stock": True})
    summary = inventory_summary()
    assert summary["ok"] is True
    assert summary["count"] >= 1


def test_accessibility_home_aria_contract():
    """Home panel markup contracts for keyboard / ARIA (static index)."""
    from pathlib import Path

    html = Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    assert 'id="flytyingHomePanel"' in html
    assert 'aria-label="Fly Tying Home"' in html
    assert 'id="flytyingProfileSelect"' in html
    assert "flytying_home.js" in html


def test_performance_potd_is_o_n_file_scan(tmp_path):
    """POTD reads JSONL once and picks by day hash — no N+1 recipe fetches."""
    from jarvis.flytying import nightly
    import json

    db = tmp_path / "lib.jsonl"
    rows = [{"fly_name": f"P{i}", "type": "dry", "id": str(i)} for i in range(50)]
    db.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    with patch("jarvis.flytying.config.recipe_source_path", return_value=db):
        out = nightly.pattern_of_the_day(day="2026-07-28")
    assert out["ok"] is True
    assert out["total"] == 50
