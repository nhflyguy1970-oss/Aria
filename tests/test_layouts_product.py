"""Layouts product tests — schema, catalog, apply, restore, integrations."""

from __future__ import annotations

from jarvis.layouts_product.apply import (
    catalog_payload,
    commit_apply,
    preview_apply,
    resolve_layout,
    save_layout_from_client,
    undo_last,
)
from jarvis.layouts_product.catalog import get_builtin, list_builtins, search_builtins
from jarvis.layouts_product.diagnostics import (
    health_summary,
    intent_coach,
    project_layout_suggestion,
    voice_switch_script,
)
from jarvis.layouts_product.engine import home_payload, product_status
from jarvis.layouts_product.mission_bridge import layouts_mission_panel
from jarvis.layouts_product.restore import recovery_status, restore_plan
from jarvis.layouts_product.schema import (
    SCHEMA_VERSION,
    diff_snapshots,
    empty_snapshot,
    make_snapshot,
    migrate_snapshot,
    validate_snapshot,
)
from jarvis.layouts_product.terminology import BOUNDARIES, MENTAL_MODEL, TERMINOLOGY


def _patch_store(tmp_path, monkeypatch):
    from jarvis.layouts_product import store as store_mod

    monkeypatch.setattr(store_mod, "ROOT", tmp_path)
    monkeypatch.setattr(store_mod, "CUSTOM_FILE", tmp_path / "custom.json")
    monkeypatch.setattr(store_mod, "SETTINGS_FILE", tmp_path / "settings.json")
    monkeypatch.setattr(store_mod, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(store_mod, "UNDO_FILE", tmp_path / "undo.json")


def test_terminology_and_boundaries():
    assert TERMINOLOGY["operator_name"] == "Layouts"
    assert TERMINOLOGY["product"] == "Layouts"
    assert "layout_catalog" in BOUNDARIES["owns"]
    assert "projects" in BOUNDARIES["does_not_own"]
    assert "secrets" in BOUNDARIES["does_not_own"]
    assert "automatic_ai_layouts" in BOUNDARIES["does_not_own"]
    assert MENTAL_MODEL["layouts"]
    assert "Projects" in MENTAL_MODEL["projects"] or "identity" in MENTAL_MODEL["projects"].lower()


def test_schema_version_and_validation():
    snap = empty_snapshot(view="chat")
    assert snap["schema_version"] == SCHEMA_VERSION
    assert validate_snapshot(snap) == []
    errs = validate_snapshot({"schema_version": 1})
    assert "missing_view" in errs
    sensitive_errs = validate_snapshot({"view": "chat", "password": "nope", "schema_version": 1})
    assert any(e.startswith("sensitive_field") for e in sensitive_errs)


def test_migrate_strips_secrets():
    raw = {"view": "chat", "token": "secret", "favorites": ["chat"], "schema_version": 0}
    out = migrate_snapshot(raw)
    assert "token" not in out
    assert out["schema_version"] == SCHEMA_VERSION
    assert out["view"] == "chat"


def test_diff_snapshots():
    a = empty_snapshot(view="chat", theme="dark")
    b = empty_snapshot(view="planner", theme="dark")
    changes = diff_snapshots(a, b)
    assert any(c["field"] == "view" for c in changes)


def test_catalog_starters_are_frozen():
    builtins = list_builtins()
    assert len(builtins) >= 8
    ids = {b["id"] for b in builtins}
    for need in ("coding", "writing", "research", "planning", "media", "maker", "home"):
        assert need in ids
    coding = get_builtin("coding")
    assert coding["kind"] == "starter"
    assert coding["snapshot"]["view"]
    assert isinstance(coding["snapshot"]["favorites"], list)
    assert get_builtin("dashboard")["id"] == "home"  # alias
    assert get_builtin("dev")["id"] == "coding"
    hits = search_builtins("coding layout")
    assert hits and hits[0]["id"] == "coding"


def test_preview_and_apply_pipeline(tmp_path, monkeypatch):
    _patch_store(tmp_path, monkeypatch)
    current = empty_snapshot(view="chat", theme="dark")
    preview = preview_apply("coding", current=current)
    assert preview["ok"] is True
    assert preview["layout_id"] == "coding"
    assert "frozen" in (preview.get("note") or "").lower() or preview.get("changes") is not None
    applied = commit_apply("coding", current=current, client_ok=True)
    assert applied["ok"] is True
    assert applied["active_layout"] == "coding"
    from jarvis.layouts_product.store import load_history, load_settings, load_undo

    assert load_settings()["active_layout"] == "coding"
    assert load_undo() is not None
    hist = load_history()
    assert hist and hist[-1]["action"] == "apply"


def test_undo_and_history(tmp_path, monkeypatch):
    _patch_store(tmp_path, monkeypatch)
    current = empty_snapshot(view="chat")
    commit_apply("writing", current=current)
    undone = undo_last(current=empty_snapshot(view="journal"))
    assert undone["ok"] is True
    assert undone["snapshot"]["view"] == "chat"
    again = undo_last()
    assert again["ok"] is False


def test_save_custom_confirm_and_delete(tmp_path, monkeypatch):
    _patch_store(tmp_path, monkeypatch)
    snap = empty_snapshot(view="maker", favorites=["maker", "chat"])
    first = save_layout_from_client("My Maker", snap)
    assert first["ok"] is True
    again = save_layout_from_client("My Maker", snap, overwrite=False)
    assert again.get("needs_confirm") or again.get("error") == "exists"
    overwrite = save_layout_from_client("My Maker", snap, overwrite=True)
    assert overwrite["ok"] is True
    from jarvis.layouts_product.store import delete_custom, load_customs

    assert "my-maker" in load_customs()
    assert delete_custom("my-maker") is True
    assert "my-maker" not in load_customs()


def test_restore_opt_in(tmp_path, monkeypatch):
    _patch_store(tmp_path, monkeypatch)
    plan = restore_plan()
    assert plan["should_restore"] is False
    assert plan["reason"] == "restore_on_boot_disabled"
    from jarvis.layouts_product.store import save_settings

    save_settings({"restore_on_boot": True, "active_layout": "coding"})
    plan2 = restore_plan()
    assert plan2["should_restore"] is True
    assert plan2["layout_id"] == "coding"
    assert validate_snapshot(plan2["snapshot"]) == []
    save_settings({"restore_on_boot": True, "active_layout": "missing-layout-xyz"})
    plan3 = restore_plan()
    assert plan3["should_restore"] is False
    assert plan3["reason"] == "active_layout_missing"
    recovery = recovery_status()
    assert recovery["ready"] is True


def test_export_import_roundtrip(tmp_path, monkeypatch):
    _patch_store(tmp_path, monkeypatch)
    save_layout_from_client("Pack Test", empty_snapshot(view="gallery"))
    cat = catalog_payload()
    payload = {
        "format": "aria_layouts_export",
        "schema_version": SCHEMA_VERSION,
        "customs": cat["customs"],
        "settings": {"restore_on_boot": True},
    }
    # Simulate API import logic
    from jarvis.layouts_product.schema import make_snapshot as ms
    from jarvis.layouts_product.schema import validate_snapshot as vs
    from jarvis.layouts_product.store import load_customs, save_customs, save_settings

    customs = load_customs()
    for item in payload["customs"]:
        lid = item["id"]
        snap = ms(item.get("snapshot") or item, label=item.get("label") or lid, kind="custom")
        if vs(snap):
            continue
        customs[lid] = snap
    save_customs(customs)
    save_settings(payload["settings"])
    assert "pack-test" in load_customs()
    from jarvis.layouts_product.store import load_settings

    assert load_settings()["restore_on_boot"] is True


def test_product_status_and_home():
    status = product_status()
    assert status["product"] == "Layouts"
    assert status["schema_version"] == SCHEMA_VERSION
    assert status["builtin_count"] >= 8
    home = home_payload()
    assert home["home"] == "Layouts"
    assert "frozen" in (home.get("note") or "").lower()
    assert home.get("builtins")


def test_resolve_and_unknown():
    assert resolve_layout("coding")["id"] == "coding"
    assert resolve_layout("nope-not-real") is None
    bad = preview_apply("nope-not-real")
    assert bad["ok"] is False


def test_project_suggestion_never_forces():
    sug = project_layout_suggestion(project_slug="jarvis-core")
    assert sug["force"] is False
    assert sug["layout_id"] == "coding" or sug["recommend"] == "coding"
    sug2 = project_layout_suggestion(project_slug="garden-notes")
    assert sug2["force"] is False


def test_intent_coach_and_voice_experimental():
    coach = intent_coach("open coding layout for git")
    assert coach["auto_apply"] is False
    assert coach["suggest"] == "coding"
    voice = voice_switch_script("writing")
    assert voice["experimental"] is True
    assert "Writing" in voice["script"]


def test_diagnostics_and_mission():
    health = health_summary()
    assert health["product"] == "Layouts"
    assert health["schema_version"] == SCHEMA_VERSION
    panel = layouts_mission_panel()
    assert panel["product"] == "Layouts"
    assert "diagnostics" in panel["deep_links"]
    assert "edit" in (panel.get("note") or "").lower() or "Layouts UI" in (panel.get("note") or "")


def test_search_layouts_retriever():
    from jarvis.search_product.retrievers import retrieve_layouts
    from jarvis.search_product.terminology import FACETS

    assert "layouts" in FACETS
    hits = retrieve_layouts("coding", 8)
    assert hits
    assert any(h.get("source") == "layouts" for h in hits)


def test_settings_catalog_registers_layouts():
    from jarvis.settings_product.catalog import build_catalog, search_catalog

    prefs = build_catalog()
    ids = {p["id"] for p in prefs}
    assert "appearance.layouts_restore" in ids
    assert "appearance.layouts_defaults" in ids
    assert "products.layouts" in ids
    hits = search_catalog("layouts restore")
    assert hits
    restore = next(p for p in prefs if p["id"] == "appearance.layouts_restore")
    assert restore["owner"] == "Layouts"
    assert (restore.get("deep_link") or {}).get("action") == "open_layouts"


def test_honest_starter_note_in_catalog(tmp_path, monkeypatch):
    _patch_store(tmp_path, monkeypatch)
    cat = catalog_payload()
    for b in cat["builtins"]:
        assert b.get("frozen") is True
        assert "frozen" in (b.get("honest_note") or "").lower()
