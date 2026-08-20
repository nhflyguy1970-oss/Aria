"""Live certification: the Safe-forget dialog's options must be usable.

openMemoryDialog resolves only when the user dismisses the dialog. The forget
flow awaited it and *then* bound the action handlers, so every option — Cool,
Correct, Erase — was inert for as long as the dialog was on screen. Clicking
Forget also gave no sign of life while its preview was in flight, which in the
Memory room can take many seconds.
"""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path("jarvis/gui/static/memory_browser.js")


def _forget_flow() -> str:
    t = SRC.read_text(encoding="utf-8")
    start = t.index("async function openForgetFlow")
    end = t.index("async function openEditMemoryDialog")
    return t[start:end]


def test_action_handlers_are_bound_while_the_dialog_is_open():
    flow = _forget_flow()
    open_at = flow.index("openMemoryDialog(")
    bind_at = flow.index('querySelectorAll(".forget-act")')
    assert open_at < bind_at, "test premise changed"
    between = flow[open_at:bind_at]
    assert "await openMemoryDialog(" not in between, (
        "awaiting the dialog binds the options only after it closes"
    )
    assert "const dismissed = openMemoryDialog(" in flow


def test_the_dialog_dismissal_is_still_awaited():
    """Binding early must not drop the await that keeps the flow alive."""
    assert re.search(r"await dismissed;", _forget_flow())


def test_the_click_is_acknowledged_before_the_preview_returns():
    flow = _forget_flow()
    preview_at = flow.index("forget-preview")
    early = flow[:preview_at]
    assert "openMemoryDialog(" in early, "nothing is shown until the preview lands"


def test_a_failed_preview_closes_the_placeholder():
    flow = _forget_flow()
    assert "closeMemoryDialog();" in flow[: flow.index("const entry")], (
        "a failed preview would leave the placeholder dialog stranded"
    )
