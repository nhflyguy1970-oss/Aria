"""Aria promotion gates — ACM v0.45.1 B21 Relationship Presentation."""
from __future__ import annotations

import json
from pathlib import Path


def test_b21_pin() -> None:
    data = json.loads(
        (Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json").read_text()
    )
    assert data["source_version"] == "0.45.1"
    assert data["aria_acm_local_version"] == "aria-acm-v0.45.1-1"
    assert data["promotion"] == "PLATFORM-PRACTICAL-COMPLETE"
    assert "B21" in data["includes"]


def test_b21_relationship_parity() -> None:
    from aria_acm.acm._version import __version__
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    assert __version__ == "0.45.1"
    eng = CognitiveEngine(
        agent_id="aria-b21",
        assistant_identity={"name": "Aria", "role": "assistant"},
    )
    eng.encode("My name is Jeff.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    eng.encode(
        "We are working on the ACM project together.",
        pin=True,
        provenance=TRUSTED_USER_STATEMENT,
    )
    who = eng.cognitive_respond("Who are you?")["memory"].lower()
    assert "aria" in who and "jeff" not in who
    rel = eng.cognitive_respond("How do we know each other?")
    assert rel["status"] == "known"
    assert "jeff" in (rel.get("memory") or "").lower() or "acm" in (rel.get("memory") or "").lower()
