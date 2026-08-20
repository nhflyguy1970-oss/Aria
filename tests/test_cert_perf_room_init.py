"""Performance certification: one room transition, one panel init.

Entering the Memory room ran its panel loaders three times — once from the view
router and twice from the room shell's legacy init — so every panel was fetched
three times over and the archive six. Measured live: 62 requests at peak
concurrency 20, against a browser that allows six connections per host.
Guarding a repeat of the same view within a moment took that to 38 requests at
peak concurrency 6, and time-to-usable from 1.12s to 0.39s.

The duplicate init must be collapsed, but not to a single one: the room shell
re-renders the panel after mounting, and the shell's own init is what fills it.
"""

from __future__ import annotations

import re
from pathlib import Path

ROUTER = Path("jarvis/gui/static/view_router.js")
FURNISH = Path("jarvis/gui/static/workspace/rooms/furnish.js")


def test_the_view_router_does_not_reinitialise_the_same_view_twice():
    src = ROUTER.read_text(encoding="utf-8")
    assert "_lastRouterInit" in src
    body = src[src.index("function runInits(") : src.index("function runInits(") + 500]
    assert "_lastRouterInit.view" in body, "the guard is not applied at the top of runInits"
    assert "return;" in body


def test_the_room_shell_does_not_reinitialise_the_same_view_twice():
    src = FURNISH.read_text(encoding="utf-8")
    assert "_lastLegacyInit" in src
    body = src[src.index("function runLegacyInit(") : src.index("function runLegacyInit(") + 500]
    assert "_lastLegacyInit.view" in body
    assert "return;" in body


def test_the_guards_expire_so_a_real_re_entry_still_loads():
    """A user leaving and coming back must get fresh data."""
    for path in (ROUTER, FURNISH):
        src = path.read_text(encoding="utf-8")
        windows = [int(m) for m in re.findall(r"_now - _last\w+\.at < (\d+)", src)]
        assert windows, f"{path.name} has no expiry window"
        for w in windows:
            assert 200 <= w <= 5000, f"{path.name} window {w}ms is not a transition-sized guard"


def test_both_guards_are_kept_separate():
    """Collapsing to one shared guard left whichever fired first to win, and the
    room shell re-renders the panel afterwards — so the list drew into a node
    that was then replaced, and Memory Home rendered nothing."""
    router = ROUTER.read_text(encoding="utf-8")
    furnish = FURNISH.read_text(encoding="utf-8")
    assert "ariaShouldInitView" not in router, "a shared guard silently broke rendering"
    assert "ariaShouldInitView" not in furnish


def test_the_archive_render_targets_the_live_element():
    """The room shell can replace #memoryList while a load is in flight."""
    src = Path("jarvis/gui/static/memory_browser.js").read_text(encoding="utf-8")
    assert 'const target = document.getElementById("memoryList") || el;' in src
    assert "renderMemoryWindow(target, entries);" in src
