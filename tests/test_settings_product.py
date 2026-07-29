"""Settings product — catalog, Home, deep links, profiles, Search facet, MC."""

from __future__ import annotations

import pytest


@pytest.fixture()
def settings_data(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    import jarvis.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    import jarvis.settings_product.appearance as appearance
    import jarvis.settings_product.history as history
    import jarvis.settings_product.profiles as profiles

    (tmp_path / "settings_product").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(appearance, "APPEARANCE_FILE", tmp_path / "settings_product" / "appearance.json")
    monkeypatch.setattr(appearance, "GLOBAL_FILE", tmp_path / "settings_product" / "global.json")
    monkeypatch.setattr(history, "HISTORY_FILE", tmp_path / "settings_product" / "history.json")
    monkeypatch.setattr(profiles, "PROFILES_FILE", tmp_path / "settings_product" / "profiles.json")
    return tmp_path


def test_terminology_boundaries():
    from jarvis.settings_product.terminology import BOUNDARIES, CATEGORIES, TERMINOLOGY

    assert TERMINOLOGY["product"] == "Settings"
    assert "preference_catalog" in BOUNDARIES["owns"]
    assert "voice_settings_store" in BOUNDARIES["does_not_own"]
    assert "monolithic_settings_database" in BOUNDARIES["does_not_own"]
    assert "appearance" in CATEGORIES
    assert "secrets" in CATEGORIES


def test_preference_schema():
    from jarvis.settings_product.schema import make_preference, validate_preference

    p = make_preference(
        id="appearance.theme",
        title="Theme",
        description="Light or dark",
        category="appearance",
        owner="Settings",
        type="select",
        default="dark",
        aliases=["dark"],
    )
    assert validate_preference(p)


def test_catalog_search_and_ia(settings_data):
    from jarvis.settings_product.catalog import build_catalog, catalog_by_category, search_catalog

    cat = build_catalog()
    assert len(cat) > 20
    assert any(e["id"] == "appearance.theme" for e in cat)
    assert any(e["id"] == "security.pin" for e in cat)
    assert any(e["id"].startswith("products.voice") for e in cat)
    themes = search_catalog("theme")
    assert themes and themes[0]["category"] == "appearance"
    sec = catalog_by_category("security")
    assert all(e["category"] == "security" for e in sec)


def test_deep_link_router(settings_data):
    from jarvis.settings_product.router import resolve_deep_link

    out = resolve_deep_link("security.pin")
    assert out["ok"] is True
    assert out["open"]["view"] == "security"
    miss = resolve_deep_link("no.such.pref")
    assert miss["ok"] is False


def test_appearance_and_profiles(settings_data):
    from jarvis.settings_product.appearance import load_appearance, save_appearance
    from jarvis.settings_product.profiles import activate_profile, export_bundle, list_profiles, save_profile

    save_appearance({"theme": "light", "accent": "blue"})
    assert load_appearance()["theme"] == "light"
    saved = save_profile("Lab")
    assert saved["ok"] is True
    act = activate_profile(saved["profile"]["id"])
    assert act["ok"] is True
    assert list_profiles()["active"] == saved["profile"]["id"]
    bundle = export_bundle()
    assert bundle["appearance"]["accent"] == "blue"


def test_home_and_status(settings_data):
    from jarvis.settings_product.engine import home_payload, product_status

    st = product_status()
    assert st["product"] == "Settings"
    home = home_payload(q="whisper")
    assert home["home"] == "Settings Home"
    assert home["preferences"]
    assert "mental_model" in home


def test_diagnostics_coach_mission(settings_data):
    from jarvis.settings_product.coach import coach_warnings
    from jarvis.settings_product.diagnostics import diagnostics, recovery_status
    from jarvis.settings_product.mission_bridge import settings_mission_panel

    d = diagnostics()
    assert d["ok"] is True
    assert d["pipeline"] == "shared_settings_pipeline"
    assert recovery_status()["ok"] is True
    assert isinstance(coach_warnings(), list)
    panel = settings_mission_panel()
    assert panel["product"] == "Settings"
    assert panel["deep_links"]["home"] == "#settings"


def test_experimental_nl(settings_data):
    from jarvis.settings_product.experimental import experimental_status, nl_configure_suggest

    assert experimental_status()["features"]
    sug = nl_configure_suggest("change theme accent")
    assert sug["ok"] is True
    assert sug["suggestions"]
    assert sug["suggestions"][0]["auto_apply"] is False


def test_search_settings_facet(settings_data):
    from jarvis.search_product.retrievers import retrieve_settings

    hits = retrieve_settings("pin", 5)
    assert hits
    assert hits[0]["source"] == "settings"
    assert hits[0]["open"]["view"] == "security"


def test_api_routes(chat_app):
    res = chat_app.get("/api/settings/product")
    assert res.status_code == 200
    assert res.json().get("product") == "Settings"
    home = chat_app.get("/api/settings/product/home")
    assert home.status_code == 200
    assert home.json().get("home") == "Settings Home"
    catalog = chat_app.get("/api/settings/product/catalog?category=appearance")
    assert catalog.status_code == 200
    assert catalog.json()["count"] >= 1
    opened = chat_app.get("/api/settings/product/open?pref=appearance.theme")
    assert opened.status_code == 200
    assert opened.json()["ok"] is True
    mission = chat_app.get("/api/settings/product/mission")
    assert mission.json().get("product") == "Settings"


def test_settings_ui_wired():
    from pathlib import Path

    html = Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    home = Path("jarvis/gui/static/settings_home.js").read_text(encoding="utf-8")
    kb = Path("jarvis/gui/static/keyboard_nav.js").read_text(encoding="utf-8")
    movie = Path("jarvis/gui/static/movie_tiers.js").read_text(encoding="utf-8")
    mc = Path("jarvis/gui/static/mission_control.js").read_text(encoding="utf-8")
    assert 'data-view="settings"' in html
    assert 'id="settingsView"' in html
    assert "settings_home.js" in html
    assert "Voice &amp; Chat" in html or "Voice & Chat" in html
    assert "initSettingsHome" in home
    assert "openSettingsHome" in kb or "switchToView?.(\"settings\")" in kb
    assert "openVoiceChatSettings" in movie
    assert "runtime_config" in mc
    assert "Settings Home" in mc or "settings_product" in mc
