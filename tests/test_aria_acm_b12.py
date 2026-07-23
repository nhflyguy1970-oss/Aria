"""Aria promotion gates — ACM v0.39.0 B12 Preference Correction UX."""
from __future__ import annotations
import json
from pathlib import Path

def test_b12_pin() -> None:
    data = json.loads((Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json").read_text())
    assert data["source_version"] == "0.39.0"
    assert data["aria_acm_local_version"] == "aria-acm-v0.39.0-1"
    assert data["promotion"] == "B13-CONFLICT-RESOLUTION"

def test_b12_correction_parity() -> None:
    from aria_acm.acm._version import __version__
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT
    assert __version__ == "0.39.0"
    eng = CognitiveEngine(agent_id="aria-b12")
    eng.encode("My favorite color is blue.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    out = eng.apply_preference_correction("Actually, my favorite color is red.")
    assert out["is_correction"] is True
    assert eng.inspect_preference("color")["active"]["value"] == "red"
