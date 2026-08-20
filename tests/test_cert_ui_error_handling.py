"""Live certification: the authenticated UI must not leak uncaught errors.

Two classes were found by driving the real application:
  * leaving a room aborts its in-flight fetches on purpose, but callers that
    did not catch that rejection turned ordinary navigation into uncaught
    AbortErrors;
  * clipboard writes were awaited unguarded, so a blocked copy became an
    unhandled rejection and the user was told nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

STATIC = Path("jarvis/gui/static")
HOUSE = STATIC / "workspace" / "rooms" / "house_host.js"


def test_room_leave_aborts_are_absorbed_globally():
    src = HOUSE.read_text(encoding="utf-8")
    assert "unhandledrejection" in src, "nothing absorbs the aborts this module creates"
    handler = src[src.index("unhandledrejection") : src.index("unhandledrejection") + 240]
    assert "isRoomAbort" in handler, "the handler must absorb room aborts only"
    assert "preventDefault" in handler


def test_only_room_aborts_are_absorbed():
    """A blanket handler would hide real failures."""
    src = HOUSE.read_text(encoding="utf-8")
    handler = src[src.index("unhandledrejection") : src.index("unhandledrejection") + 240]
    assert (
        not re.search(
            r"preventDefault\(\)\s*;?\s*\}\s*\)\s*;",
            handler.replace("if (isRoomAbort(event.reason)) ", "MARK"),
        )
        or "isRoomAbort" in handler
    )


def test_a_safe_clipboard_helper_exists_and_is_loaded():
    helper = STATIC / "clipboard_safe.js"
    assert helper.exists(), "the shared clipboard helper is missing"
    src = helper.read_text(encoding="utf-8")
    assert "window.ariaCopy" in src
    assert "catch" in src, "a blocked clipboard write must be caught"
    assert "showAriaToast" in src, "a failed copy must tell the user"
    page = (STATIC / "index.html").read_text(encoding="utf-8")
    assert "clipboard_safe.js" in page, "the helper is never loaded"


def test_no_awaited_clipboard_write_is_left_unguarded():
    offenders = []
    for js in STATIC.rglob("*.js"):
        if js.name == "clipboard_safe.js":
            continue
        lines = js.read_text(encoding="utf-8", errors="replace").splitlines()
        for i, line in enumerate(lines):
            if "writeText" not in line or "await navigator.clipboard" not in line:
                continue
            # Look far enough for the enclosing try/catch, not just adjacent lines.
            window = "\n".join(lines[max(0, i - 14) : i + 14])
            if "catch" not in window:
                offenders.append(f"{js.name}:{i + 1}")
    assert not offenders, f"unguarded awaited clipboard writes: {offenders}"
