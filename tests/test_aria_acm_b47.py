"""Aria promotion gates — ACM v0.45.0 B47 Possession Recall."""
from __future__ import annotations

import json
from pathlib import Path


def test_b47_pin() -> None:
    data = json.loads(
        (Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json").read_text()
    )
    assert data["source_version"] == "0.45.0"
    assert data["aria_acm_local_version"] == "aria-acm-v0.45.0-1"
    assert data["promotion"] == "PLATFORM-PRACTICAL-COMPLETE"
    assert "B47" in data["includes"]


def test_b47_possession_parity() -> None:
    from aria_acm.acm._version import __version__
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    assert __version__ == "0.45.0"
    eng = CognitiveEngine(
        agent_id="aria-b47",
        assistant_identity={"name": "Aria", "role": "assistant"},
    )
    eng.encode("My name is Jeff.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    eng.encode("My dog's name is Zeus.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    assert "zeus" not in eng.cognitive_respond("Who am I?")["memory"].lower()
    dog = eng.cognitive_respond("What's my dog's name?")
    assert dog["status"] == "known"
    assert "zeus" in (dog.get("memory") or "").lower()
    assert "jeff" not in (dog.get("memory") or "").lower()
