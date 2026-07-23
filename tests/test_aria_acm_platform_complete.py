"""Aria promotion gates — ACM v0.45.0 practical platform completion."""
from __future__ import annotations

import json
from pathlib import Path


def test_platform_complete_pin() -> None:
    data = json.loads(
        (Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json").read_text()
    )
    assert data["source_version"] == "0.45.0"
    assert data["aria_acm_local_version"] == "aria-acm-v0.45.0-1"
    assert data["promotion"] == "PLATFORM-PRACTICAL-COMPLETE"
    assert "B51" in data["includes"] and "B46" in data["includes"]


def test_platform_complete_parity_smoke() -> None:
    from aria_acm.acm._version import __version__
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    assert __version__ == "0.45.0"
    eng = CognitiveEngine(
        agent_id="aria-platform",
        assistant_identity={"name": "Aria", "role": "assistant"},
    )
    eng.encode("My name is Jeff.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    eng.encode("My dog's name is Zeus.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    assert "jeff" in eng.cognitive_respond("Who am I?")["memory"].lower()
    assert "zeus" in eng.cognitive_respond("What's my dog's name?")["memory"].lower()
    assert eng.preview_erase_request("Forget my old address.")["status"] in {
        "preview",
        "unrecognized",
    }
