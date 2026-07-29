"""Command Palette — modular registry, ranking, Ask Aria, and wiring contracts."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "jarvis" / "gui" / "static"


def _read(*parts: str) -> str:
    return (STATIC.joinpath(*parts)).read_text(encoding="utf-8")


def test_palette_stack_files_exist():
    for name in (
        "command_registry.js",
        "aria_actions.js",
        "command_catalog.js",
        "command_palette.js",
    ):
        assert (STATIC / name).is_file(), name


def test_html_wires_registry_stack():
    html = _read("index.html")
    assert "command_registry.js" in html
    assert "aria_actions.js" in html
    assert "command_catalog.js" in html
    assert "command_palette.js" in html
    assert 'id="commandPaletteStatus"' in html
    assert 'id="commandPaletteLive"' in html
    assert 'id="commandPaletteHelp"' in html
    assert 'id="commandPaletteRetryBtn"' in html


def test_connections_in_navigate():
    catalog = _read("command_catalog.js")
    assert '["connections", "Connections"' in catalog
    assert "Open Connections" in catalog


def test_catalog_uses_aria_actions_not_raw_clicks():
    catalog = _read("command_catalog.js")
    # Domain catalog should call AriaActions, not DOM click simulation for primary nav
    assert "A().goView" in catalog or "AriaActions" in catalog
    # Allow section expand / focus helpers; forbid view-tab click navigation
    assert 'view-tab")?.click()' not in catalog
    assert 'data-view="' not in catalog or "switchToView" in catalog or "A().goView" in catalog


def test_palette_ask_aria_autosend():
    palette = _read("command_palette.js")
    actions = _read("aria_actions.js")
    assert "askAria" in palette
    assert "autoSend: true" in palette or "askAria?.(trimmed" in palette
    assert "function askAria" in actions or "askAria(text" in actions
    assert "jarvisAskAria" in actions


def test_honest_search_states():
    palette = _read("command_palette.js")
    assert 'searching' in palette
    assert "Searching knowledge" in palette or "Searching…" in palette
    assert "No knowledge matches" in palette
    assert "Knowledge search unavailable" in palette or "Search failed" in palette
    assert "commandPaletteRetryBtn" in palette


def test_registry_modes_and_sentence_detection():
    reg = _read("command_registry.js")
    assert "parseMode" in reg
    assert "looksLikeSentence" in reg
    assert ">navigate" in reg or "navigate" in reg
    assert "ALIASES" in reg


def test_keyboard_pin_and_help():
    palette = _read("command_palette.js")
    assert 'toLowerCase() === "p"' in palette or '=== "p"' in palette
    assert "toggleHelp" in palette
    assert "Tab" in palette


def test_action_ids_present_in_catalog():
    catalog = _read("command_catalog.js")
    for act in (
        "act:backup",
        "act:theme-toggle",
        "act:planner-task",
        "act:calendar-today",
        "act:clear-chat",
        "act:open-connections",
        "act:compare-images",
        "act:new-branch",
        "search:memory",
        "search:documents",
    ):
        assert act in catalog, act


def test_registry_scoring_node():
    """Exercise fuzzy + mode parsing via Node without a browser DOM."""
    script = r"""
const fs = require('fs');
const vm = require('vm');
const code = fs.readFileSync('jarvis/gui/static/command_registry.js', 'utf8');
const sandbox = { window: {}, console };
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const R = sandbox.window.AriaCommandRegistry;
if (!R) throw new Error('no registry');
R.register({ id: 'act:demo', title: 'Open Planner', keywords: 'todo task', group: 'Actions', run() {} });
R.register({ id: 'nav:chat', title: 'Go to Chat', keywords: 'conversation', group: 'Navigate', run() {} });
const s1 = R.scoreCommand(R.get('act:demo'), 'plan');
const s2 = R.scoreCommand(R.get('act:demo'), 'zzzqqq');
if (!(s1 > s2)) throw new Error('fuzzy score failed');
const m = R.parseMode('>ask hello world');
if (m.mode !== 'ask' || m.query !== 'hello world') throw new Error('mode parse failed');
if (!R.looksLikeSentence('What should I focus on in Planner today?')) throw new Error('sentence detect failed');
if (R.looksLikeSentence('open')) throw new Error('false sentence');
console.log('ok');
"""
    proc = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "ok" in proc.stdout


def test_documentation_exists():
    doc = ROOT / "docs" / "COMMAND_PALETTE_IMPLEMENTATION.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "Modular" in text or "registry" in text.lower()
    assert "Ask Aria" in text
    assert "AriaActions" in text
