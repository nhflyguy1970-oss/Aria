"""Browser util coverage."""

from __future__ import annotations

from jarvis.browser_util import browser_candidates


def test_browser_candidates_nonempty():
    names = browser_candidates()
    assert isinstance(names, list)
    assert len(names) >= 1
