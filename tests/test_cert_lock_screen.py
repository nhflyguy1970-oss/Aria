"""Live certification: the first screen every user sees.

Focus fell through to a hidden PIN field when status had not arrived yet, so
nothing was focused at all; and pressing Unlock with an empty field showed a
message identical to the prompt already on screen, which reads as a dead button.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SCRIPT = Path("jarvis/gui/static/lock_screen.js")
PAGE = Path("jarvis/gui/static/index.html")


@pytest.fixture(scope="module")
def source() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_focus_targets_a_visible_field(source):
    show = source[source.index("function showLock(") : source.index("function applyLockMode(")]
    assert "offsetParent" in show, "focus is not checked against what is actually on screen"
    assert show.count("focus()") >= 1


def test_empty_submit_says_what_is_missing(source):
    assert "Enter your Aria Master Password first." in source
    prompt = "Aria is locked. Enter your Aria Master Password to unlock the house."
    unlock = source[source.index("async function unlockHouse(") :]
    empty_branch = unlock[: unlock.index("try {")]
    assert prompt not in empty_branch, "the empty-field message repeats the standing prompt"


def test_the_password_field_is_labelled_and_typed():
    html = PAGE.read_text(encoding="utf-8")
    field = re.search(r'<input[^>]*id="lockMasterInput"[^>]*>', html)
    assert field, "the master password field is missing"
    tag = field.group(0)
    assert 'type="password"' in tag
    assert "aria-label=" in tag
    assert 'autocomplete="current-password"' in tag


def test_the_unlock_control_exists_and_is_named():
    html = PAGE.read_text(encoding="utf-8")
    assert re.search(r'id="lockUnlockBtn"', html)
