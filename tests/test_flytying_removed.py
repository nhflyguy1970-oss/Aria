"""ARIA's built-in fly-tying reference was removed in favour of the standalone
Fly Tying Reference app. Nothing should quietly bring it back, and fly-tying
questions are ordinary chat now."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from jarvis.router import route
from jarvis.session import SessionContext

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "jarvis" / "gui" / "static"


@pytest.mark.parametrize("module", ["jarvis.flytying", "jarvis.flytying_product", "jarvis.extensions.flytying"])
def test_packages_are_gone(module):
    assert importlib.util.find_spec(module) is None


def test_extension_is_not_discovered():
    from jarvis.extensibility.loader import _discover_extension_names

    assert "flytying" not in _discover_extension_names()


def test_no_fly_routes_or_actions(chat_app):
    rules = chat_app.get("/api/registry/router/rules").json()["rules"]
    assert not [r for r in rules if "fly" in str(r.get("name") or r.get("action") or "")]
    actions = chat_app.get("/api/registry/actions").json()["actions"]
    names = {a.get("name") if isinstance(a, dict) else str(a) for a in actions}
    assert not {n for n in names if str(n).startswith("fly_")}
    assert chat_app.get("/api/flytying/status").status_code == 404


@pytest.mark.parametrize(
    "text",
    [
        "how do I tie a parachute adams",
        "find fly patterns with marabou",
        "what should I tie for the caddis hatch",
    ],
)
def test_fly_tying_questions_are_chat(text):
    assert route(text, SessionContext()).get("action") == "chat"


def test_gui_has_no_fly_tying_view():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "flytying" not in html.lower()
    for name in ("flytying.js", "flytying_home.js", "workspace/rooms/flytying_room.js"):
        assert not (STATIC / name).exists()
    # The shared heading style survived the rename.
    assert ".section-subtitle" in (STATIC / "style.css").read_text(encoding="utf-8")
