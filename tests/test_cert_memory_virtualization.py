"""Performance certification: the memory archive must not render everything.

Rendering every row put ~10,000 DOM nodes on the page for ~1,100 entries. The
list is now windowed: a chunk at a time, with the rest reachable by an explicit
control (and an observer for scrolling). Search and filtering stay server-side
over the whole dataset, so nothing is hidden from a search by not being drawn.
"""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path("jarvis/gui/static/memory_browser.js")


def _source() -> str:
    return SRC.read_text(encoding="utf-8")


def test_the_list_renders_a_window_not_the_whole_dataset():
    src = _source()
    assert "MEMORY_WINDOW_SIZE" in src
    assert "function renderMemoryWindow" in src
    render = src[
        src.index("function renderMemoryWindow") : src.index("async function loadMemoryListOnly")
    ]
    assert "entries.slice(shown, shown + MEMORY_WINDOW_SIZE)" in render, "the window is not sliced"


def test_the_window_is_a_sensible_size():
    match = re.search(r"const MEMORY_WINDOW_SIZE = (\d+)", _source())
    assert match, "window size is not declared"
    size = int(match.group(1))
    assert 20 <= size <= 200, f"window size {size} is not a viewport-sized chunk"


def test_the_rest_of_the_dataset_is_reachable_without_a_mouse():
    """An observer alone would strand keyboard users and depends on which
    ancestor happens to scroll."""
    src = _source()
    assert "memory-window-more" in src
    marker = 'class="memory-window-sentinel">'
    assert marker in src, "the sentinel markup is missing"
    markup = src[src.index(marker) : src.index(marker) + 220]
    assert "<button" in markup, markup[:160]
    assert 'addEventListener("click"' in src[src.index("const moreBtn") :][:320]


def test_the_control_disappears_once_everything_is_shown():
    render = _source()
    assert "sentinel.remove()" in render


def test_per_item_controls_are_rebound_after_each_chunk():
    src = _source()
    append = src[
        src.index("const appendChunk") : src.index(
            'el.innerHTML = `<div class="memory-window-sentinel"'
        )
    ]
    assert "bindMemoryCardActions(el)" in append, (
        "appended rows would have dead Edit/Forget buttons"
    )


def test_search_and_filtering_remain_server_side():
    """Windowing must never turn a search into 'only what is drawn'."""
    src = _source()
    load = src[src.index("async function loadMemoryListOnly") :]
    assert 'params.set("q", q)' in load
    assert 'params.set("type", type)' in load
    assert 'params.set("namespace", namespace)' in load
    assert "fetch(`/api/memory/all?${params}`)" in load


def test_the_empty_state_is_preserved():
    src = _source()
    assert "memory-empty" in src
    assert "memoryEmptyChatBtn" in src


def test_the_observer_is_disconnected_between_loads():
    """Otherwise every reload leaks another observer onto the old sentinel."""
    render = _source()
    assert "_memoryWindowObserver.disconnect()" in render
