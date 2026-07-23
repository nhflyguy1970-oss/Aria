"""Aria promotion gates — ACM v0.41.0 B10 Conversation-Safe Debugging."""

from __future__ import annotations

import json
from pathlib import Path


def test_b10_pin() -> None:
    data = json.loads(
        (Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json").read_text()
    )
    assert data["source_version"] == "0.41.0"
    assert data["aria_acm_local_version"] == "aria-acm-v0.41.0-1"
    assert data["promotion"] == "B21-RELATIONSHIP-PRESENTATION"


def test_b10_debug_capture_parity() -> None:
    from aria_acm.acm._version import __version__
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.authority.debug_capture import (
        ConversationDebugPolicy,
        with_debug_enabled,
    )
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    assert __version__ == "0.41.0"
    eng = CognitiveEngine(
        agent_id="aria-b10",
        conversation_debug_policy=with_debug_enabled(
            ConversationDebugPolicy(), enabled=True
        ),
    )
    eng.encode("My favorite color is blue.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    out = eng.debug_capture("What is my favorite color?")
    assert out["status"] == "captured"
    assert out["store_unchanged"] is True
    assert out["invents_experiences"] is False
