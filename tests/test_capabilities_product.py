"""Capabilities product — registry, policy, contributions, API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def cap_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    # Reset module-level DATA_DIR dependents by reimporting policy paths via monkeypatch of config
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    import jarvis.capabilities_product.policy as policy
    import jarvis.capabilities_product.settings as settings
    import jarvis.capabilities_product.history as history
    import jarvis.intelligence.plugin_sdk as plugin_sdk

    monkeypatch.setattr(policy, "POLICY_FILE", tmp_path / "capabilities_product" / "policy.json")
    monkeypatch.setattr(settings, "SETTINGS_FILE", tmp_path / "capabilities_product" / "settings.json")
    monkeypatch.setattr(history, "HISTORY_FILE", tmp_path / "capabilities_product" / "activity.json")
    monkeypatch.setattr(plugin_sdk, "PLUGIN_DIR", tmp_path / "plugins")
    (tmp_path / "plugins").mkdir(parents=True, exist_ok=True)
    (tmp_path / "capabilities_product").mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_terminology_boundaries():
    from jarvis.capabilities_product.terminology import BOUNDARIES, TERMINOLOGY

    assert TERMINOLOGY["product"] == "Capabilities"
    assert "capability_registry" in BOUNDARIES["owns"]
    assert "voice" in BOUNDARIES["does_not_own"]
    assert "public_marketplace" in BOUNDARIES["does_not_own"]


def test_policy_defaults_and_persistence(cap_data):
    from jarvis.capabilities_product import policy as cap_policy

    assert cap_policy.is_enabled("sdk:demo", trust="trusted_local") is False
    assert cap_policy.is_enabled("host:git", trust="first_party") is True
    cap_policy.set_enabled("sdk:demo", True)
    assert cap_policy.is_enabled("sdk:demo", trust="trusted_local") is True
    cap_policy.set_enabled("sdk:demo", False)
    assert cap_policy.is_enabled("sdk:demo", trust="trusted_local") is False


def test_quarantine_threshold(cap_data):
    from jarvis.capabilities_product import policy as cap_policy

    for _ in range(3):
        cap_policy.record_failure("sdk:flaky", "boom")
    assert cap_policy.is_quarantined("sdk:flaky")
    assert cap_policy.is_enabled("sdk:flaky", trust="trusted_local") is False
    cap_policy.acknowledge_quarantine("sdk:flaky", reenable=True)
    assert not cap_policy.is_quarantined("sdk:flaky")
    assert cap_policy.is_enabled("sdk:flaky", trust="trusted_local")


def test_honest_isolation_note():
    from jarvis.capabilities_product.models import isolation_note

    note = isolation_note("none", sandbox_claimed=True)
    assert "does not isolate" in note.lower() or "in-process" in note.lower()


def test_registry_includes_host_layers(cap_data):
    from jarvis.capabilities_product.registry import list_capabilities, registry_snapshot

    items = list_capabilities()
    assert any(i["id"].startswith("host:") for i in items)
    snap = registry_snapshot()
    assert snap["product"] == "Capabilities"
    assert snap["count"] >= 1
    assert "isolation_policy" in snap


def test_sdk_scaffold_and_contributions(cap_data, monkeypatch):
    from jarvis.capabilities_product.scaffold import scaffold_capability
    from jarvis.capabilities_product.loader import enable_capability, load_capability
    from jarvis.handlers.registry import has_action
    from jarvis.router_table import invalidate_router_table, match_router_table
    from jarvis.session import SessionContext

    result = scaffold_capability("Demo Cap", description="demo", category="Utilities")
    assert result["ok"]
    assert result["enabled"] is False
    cap_id = result["id"]
    enable_capability(cap_id, load_now=True)
    report = load_capability(cap_id)
    assert report["ok"], report
    invalidate_router_table()
    assert has_action("demo_cap_status")
    hit = match_router_table("demo cap status", SessionContext())
    assert hit and hit["action"] == "demo_cap_status"


def test_hello_aria_example_contributions(cap_data):
    from jarvis.intelligence.plugin_sdk import create_example_plugin, load_plugin
    from jarvis.capabilities_product.contributions import register_contributions
    from jarvis.handlers.registry import has_action
    from jarvis.router_table import invalidate_router_table

    path = create_example_plugin()
    loaded = load_plugin(path)
    assert loaded.error == ""
    assert loaded.manifest.sandbox is False
    reg = register_contributions(f"sdk:{loaded.manifest.id}", loaded.manifest)
    assert reg["registered"]["actions"] >= 1
    invalidate_router_table()
    assert has_action("hello_aria")


def test_plugin_context_permission_gate(cap_data):
    from jarvis.intelligence.plugin_sdk import PluginContext, PluginManifest, PluginPermissionError

    ctx = PluginContext(PluginManifest(id="t", name="t", permissions=["rag.search"]))
    with pytest.raises(PluginPermissionError):
        ctx.memory_search("x")
    assert ctx.isolation == "none"
    assert ctx.sandbox_enforced is False


def test_export_import_bundle(cap_data):
    from jarvis.capabilities_product.engine import export_bundle, import_bundle
    from jarvis.capabilities_product import policy as cap_policy

    cap_policy.set_enabled("sdk:bundle_test", True)
    bundle = export_bundle(["sdk:bundle_test"])
    assert bundle["format"] == "aria_capabilities_bundle_v1"
    cap_policy.set_enabled("sdk:bundle_test", False)
    out = import_bundle(bundle, merge_policy=True)
    assert out["ok"]


def test_experimental_mcp_and_nl(cap_data):
    from jarvis.capabilities_product.experimental import experimental_status, mcp_export_tools, nl_generate_stub

    status = experimental_status()
    assert any(i["id"] == "process_isolation" and not i["available"] for i in status["items"])
    assert mcp_export_tools()["ok"]
    stub = nl_generate_stub("tide alerts helper")
    assert stub["ok"]
    assert stub["enabled"] is False


def test_mission_panel(cap_data):
    from jarvis.capabilities_product.mission_bridge import capabilities_mission_panel

    panel = capabilities_mission_panel()
    assert panel["product"] == "Capabilities"
    assert "deep_links" in panel


def test_home_payload(cap_data):
    from jarvis.capabilities_product.engine import home_payload

    home = home_payload()
    assert home["product"] == "Capabilities"
    assert "summary" in home
    assert home["security"]["sandbox"] is False


def test_registry_extensions_api(chat_app):
    from jarvis.handlers import ensure_handlers_loaded

    ensure_handlers_loaded()
    res = chat_app.get("/api/registry/extensions")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert any(e["name"] == "git" for e in body["extensions"])


def test_capabilities_product_api(chat_app, cap_data):
    res = chat_app.get("/api/capabilities/product")
    assert res.status_code == 200
    body = res.json()
    assert body["product"] == "Capabilities"
    home = chat_app.get("/api/capabilities/product/home")
    assert home.status_code == 200
    assert home.json()["ok"] is True
    diag = chat_app.get("/api/capabilities/product/diagnostics")
    assert diag.status_code == 200
    assert diag.json()["security"]["sandbox"] is False


def test_action_spec_extension_field():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import get_spec

    ensure_handlers_loaded()
    spec = get_spec("git_status")
    assert spec is not None
    assert spec.extension == "git"


def test_enrich_snapshot_capabilities(cap_data):
    from jarvis.mission_control_ops.enrich import enrich_snapshot

    snap = enrich_snapshot({})
    assert snap["capabilities"]["product"] == "Capabilities"


def test_load_report_structure(cap_data):
    from jarvis.capabilities_product.loader import load_all_enabled

    report = load_all_enabled(include_sdk=True)
    for key in ("loaded", "skipped", "disabled", "failed", "warnings", "duration_ms"):
        assert key in report
