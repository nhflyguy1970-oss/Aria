"""Dashboard / Home product tests."""

from __future__ import annotations

from jarvis.dashboard_product.attention import build_attention
from jarvis.dashboard_product.brief import build_daily_brief
from jarvis.dashboard_product.cache import load_layout, save_layout
from jarvis.dashboard_product.greeting import greeting_payload, personalized_greeting
from jarvis.dashboard_product.router import resolve_deep_link
from jarvis.dashboard_product.schema import make_widget, validate_widget
from jarvis.dashboard_product.terminology import BOUNDARIES, TERMINOLOGY
from jarvis.dashboard_product.widgets import list_widget_defs, search_widgets


def test_terminology_and_boundaries():
    assert TERMINOLOGY["operator_name"] == "Home"
    assert TERMINOLOGY["product"] == "Dashboard"
    assert "home" in BOUNDARIES["owns"]
    assert "planner" in BOUNDARIES["does_not_own"]
    assert "morning_briefing" in BOUNDARIES["does_not_own"]
    assert "monolithic_dashboard_database" in BOUNDARIES["does_not_own"]


def test_widget_schema_honest_empty():
    w = make_widget(
        id="x",
        title="X",
        owner="Test",
        category="glance",
        available=True,
        empty=True,
        coach="Nothing here",
    )
    assert w["render"] == "coach"
    assert validate_widget(w) == []


def test_widget_catalog_search():
    defs = list_widget_defs()
    assert len(defs) >= 10
    assert any(d["id"] == "daily_brief" for d in defs)
    hits = search_widgets("brief")
    assert hits and hits[0]["id"] in ("daily_brief", "news")


def test_greeting_uses_time():
    g = personalized_greeting()
    assert g
    assert "Hello" in g or "Good" in g
    payload = greeting_payload()
    assert payload["greeting"]
    assert payload["time_display"]


def test_deep_links():
    assert resolve_deep_link("home")["view"] == "dashboard"
    assert resolve_deep_link("daily_brief")["widget"] == "daily_brief"
    assert resolve_deep_link("attention")["widget"] == "attention"


def test_layout_roundtrip(tmp_path, monkeypatch):
    from jarvis.dashboard_product import cache as cache_mod

    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(cache_mod, "LAYOUT_FILE", tmp_path / "layout.json")
    monkeypatch.setattr(cache_mod, "CACHE_FILE", tmp_path / "last_good_home.json")
    saved = save_layout({"density": "compact", "role": "developer", "hidden": ["news"]})
    assert saved["density"] == "compact"
    assert load_layout()["role"] == "developer"


def test_attention_and_brief_shapes():
    att = build_attention(assistant=None)
    assert "items" in att
    assert "empty" in att
    brief = build_daily_brief(assistant=None)
    assert "available" in brief
    assert brief.get("source") == "morning_briefing" or brief.get("coach")


def test_home_aggregate_honest(tmp_path, monkeypatch):
    from jarvis.dashboard_product import cache as cache_mod
    from jarvis.dashboard_product.engine import home_payload, product_status

    monkeypatch.setattr(cache_mod, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(cache_mod, "LAYOUT_FILE", tmp_path / "layout.json")
    monkeypatch.setattr(cache_mod, "CACHE_FILE", tmp_path / "last_good_home.json")

    status = product_status()
    assert status["product"] == "Dashboard"
    assert status["home"] == "Home"
    assert status["widget_count"] >= 10

    home = home_payload(assistant=None, stale_ok=True)
    assert home.get("ok") is True
    assert home.get("home") == "Home"
    widgets = home.get("widgets") or []
    assert widgets
    intel = home.get("intelligence") or {}
    assert "invented" in str(intel.get("note") or "").lower() or "attention" in str(intel.get("note") or "").lower()
    for w in widgets:
        assert w.get("render") in ("show", "hide", "coach")
        if w.get("empty") and w["id"] != "attention" and w.get("render") == "show":
            assert False, f"empty widget shown dishonestly: {w['id']}"


def test_search_dashboard_retriever():
    from jarvis.search_product.retrievers import retrieve_dashboard
    from jarvis.search_product.terminology import FACETS

    assert "dashboard" in FACETS
    hits = retrieve_dashboard("daily brief", 5)
    assert hits
    assert any(h.get("source") == "dashboard" for h in hits)


def test_mission_bridge():
    from jarvis.dashboard_product.mission_bridge import dashboard_mission_panel

    panel = dashboard_mission_panel(assistant=None)
    assert panel["product"] == "Dashboard"
    assert panel["operator_name"] == "Home"
    assert "home" in panel["deep_links"]


def test_system_info_greeting_compat():
    from jarvis.system_info import build_system_info

    info = build_system_info(assistant=None)
    assert info.get("greeting")
    assert info["greeting"] != ""  # fixed personalized_greeting path


def test_experimental_voice_script():
    from jarvis.dashboard_product.experimental import kiosk_hints, policy_layouts, voice_home_brief_script

    script = voice_home_brief_script({"greeting": {"greeting": "Good morning"}, "attention": {"items": [], "empty": True}})
    assert script["experimental"] is True
    assert "Good morning" in script["script"]
    assert "operations" in (policy_layouts().get("roles") or {})
    assert kiosk_hints()["mode"] == "kiosk"
