"""Shell / Global UX — hotkeys, tokens, breadcrumbs, discoverability, wiring."""

from __future__ import annotations

from pathlib import Path

from jarvis.shell.api import SHELL_BUNDLE_SCRIPTS
from jarvis.shell.design_tokens import DESIGN_TOKENS, token_css_variables
from jarvis.shell.engine import product_status
from jarvis.shell.hotkeys import HOTKEYS, chord_for, list_hotkeys, validate_registry
from jarvis.shell.product_home import PRODUCT_HOME_CHECKLIST, PRODUCT_VIEWS, checklist_payload
from jarvis.shell.terminology import BOUNDARIES, MENTAL_MODEL, TERMINOLOGY

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "jarvis" / "gui" / "static"
INDEX = STATIC / "index.html"


def test_terminology_and_boundaries():
    assert TERMINOLOGY["product"] == "Shell"
    assert "hotkey_registry" in BOUNDARIES["owns"]
    assert "movie_hud" in BOUNDARIES["does_not_own"]
    assert "notifications_delivery" in BOUNDARIES["does_not_own"]
    assert MENTAL_MODEL["sidebar"] == "Browse"
    assert MENTAL_MODEL["ctrl_k"] == "Act"
    assert MENTAL_MODEL["notifications"] == "Attention"


def test_hotkey_registry_unique_and_critical_chords():
    assert validate_registry() == []
    ids = {h["id"] for h in HOTKEYS}
    assert {"palette", "notifications", "layouts", "mission", "mini_chat", "split"} <= ids
    assert chord_for("mini_chat") == "Ctrl+Shift+K"
    assert chord_for("mission") == "Ctrl+Shift+M"
    assert chord_for("notifications") == "Ctrl+Shift+A"
    assert chord_for("layouts") == "Ctrl+Shift+L"
    assert any("Ctrl+Shift+P" in (h.get("aliases") or []) for h in HOTKEYS if h["id"] == "layouts")
    assert len(list_hotkeys()) == len(HOTKEYS)


def test_design_tokens_professional():
    assert DESIGN_TOKENS["theme_default"] == "professional_dark"
    assert "professional_light" in DESIGN_TOKENS["themes"]
    assert DESIGN_TOKENS["colors"]["accent"] == "#4f7cac"
    assert "neon_glow" in DESIGN_TOKENS["forbidden"]
    assert "movie_hud" in DESIGN_TOKENS["forbidden"]
    dens = DESIGN_TOKENS["density"]
    assert dens == ["comfortable", "standard", "compact", "operator"]
    css = token_css_variables()
    assert css["--accent"] == "#4f7cac"
    assert css["--space-4"] == "1rem"
    assert css["--font"].startswith('"IBM Plex Sans"')


def test_product_home_checklist():
    payload = checklist_payload()
    required = {
        "header",
        "breadcrumbs",
        "health",
        "actions",
        "search_or_filter",
        "deep_links",
        "status",
        "loading",
        "errors",
        "empty_state",
        "help",
        "esc_behavior",
        "accessibility",
        "consistent_spacing",
        "consistent_toolbar",
    }
    assert set(PRODUCT_HOME_CHECKLIST) == required
    assert "search" in PRODUCT_VIEWS
    assert "settings" in PRODUCT_VIEWS
    assert "notifications" in PRODUCT_VIEWS
    assert "layouts" in PRODUCT_VIEWS
    assert payload["ok"] is True


def test_engine_status_healthy():
    st = product_status()
    assert st["ok"] is True
    assert st["healthy"] is True
    assert st["hotkey_errors"] == []
    assert st["design_version"] == DESIGN_TOKENS["version"]


def test_breadcrumbs_map_covers_product_homes():
    src = (STATIC / "breadcrumbs.js").read_text(encoding="utf-8")
    for view in (
        "search",
        "settings",
        "models",
        "coding",
        "automation",
        "gallery",
        "browser",
        "voice",
        "vision",
        "flytying",
        "planner",
        "calendar",
        "journal",
        "projects",
        "memory",
        "documents",
        "notifications",
        "workstation",
        "jobs",
        "layouts",
        "dashboard",
    ):
        assert f"{view}:" in src, f"missing breadcrumb for {view}"


def test_discoverability_hotkeys_accurate():
    src = (STATIC / "discoverability.js").read_text(encoding="utf-8")
    assert 'chord("mini_chat", "Ctrl+Shift+K")' in src
    assert 'chord("mission", "Ctrl+Shift+M")' in src
    assert "tip-mc-hotkey" in src
    assert 'id: "tip-mini"' in src
    assert src.count('id: "tip-mc"') == 0  # duplicate tip-mc removed
    assert "Notifications" in src
    # Must not teach mini-chat as Ctrl+Shift+M
    assert "mini chat" in src.lower()
    assert 'Ctrl+Shift+M")}. ${chord("mission"' not in src.replace(" ", "")


def test_hotkey_js_fallback_matches_python():
    js = (STATIC / "hotkey_registry.js").read_text(encoding="utf-8")
    assert 'id: "mini_chat", chord: "Ctrl+Shift+K"' in js
    assert 'id: "mission", chord: "Ctrl+Shift+M"' in js
    for h in HOTKEYS:
        assert f'id: "{h["id"]}"' in js, f"missing fallback for {h['id']}"
        assert h["chord"] in js, f"missing chord {h['chord']} for {h['id']}"

def test_index_wires_design_system_and_bundle():
    html = INDEX.read_text(encoding="utf-8")
    assert "shell_design.css" in html
    assert "/api/shell/bundle.js" in html
    assert "IBM+Plex+Sans" in html
    # individual shell modules should not be double-loaded when bundled
    for name in SHELL_BUNDLE_SCRIPTS:
        assert f"/static/{name}" not in html, f"{name} should come from bundle only"
    assert "Professional Dark" in html
    assert "settingsDensitySelect" in html


def test_shell_design_css_kills_hud():
    css = (STATIC / "shell_design.css").read_text(encoding="utf-8")
    assert "body::before" in css
    assert "display: none !important" in css
    assert "--accent: #4f7cac" in css
    assert "prefers-reduced-motion" in css
    assert "neon" not in css.lower() or "Kill" in css or "Neutralize" in css


def test_keyboard_nav_bindings_match_registry():
    nav = (STATIC / "keyboard_nav.js").read_text(encoding="utf-8")
    # M = mission, K = mini chat
    assert 'e.key.toLowerCase() === "m"' in nav
    assert 'e.key.toLowerCase() === "k"' in nav
    assert 'e.key.toLowerCase() === "a"' in nav
    assert 'e.key.toLowerCase() === "l"' in nav


def test_command_catalog_notifications_naming():
    cat = (STATIC / "command_catalog.js").read_text(encoding="utf-8")
    assert "Open Notifications" in cat
    assert cat.count("Open Activity Center") == 0
    assert 'shortcut: "Ctrl+Shift+K"' in cat


def test_docs_exist():
    doc = ROOT / "docs" / "GLOBAL_UX_IMPLEMENTATION.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "hotkeys.py" in text
    assert "Product Home checklist" in text
    assert "Professional Dark" in text


def test_bundle_scripts_exist_on_disk():
    for name in SHELL_BUNDLE_SCRIPTS:
        assert (STATIC / name).is_file(), name


def test_appearance_defaults_professional():
    from jarvis.settings_product.appearance import APPEARANCE_DEFAULTS

    assert APPEARANCE_DEFAULTS["accent"] == "steel"
    assert APPEARANCE_DEFAULTS["density"] == "standard"
    assert APPEARANCE_DEFAULTS["theme"] == "dark"
