"""Aria promotion gates — ACM v0.40.0 B13 Conflict Resolution."""
from __future__ import annotations
import json
from pathlib import Path

def test_b13_pin() -> None:
    data = json.loads((Path(__file__).resolve().parents[1]/"aria_acm"/"VERSION.json").read_text())
    assert data["source_version"]=="0.40.0"
    assert data["aria_acm_local_version"]=="aria-acm-v0.40.0-1"
    assert data["promotion"]=="B20-IDENTITY-CORRECTION"

def test_b13_conflict_parity() -> None:
    from aria_acm.acm._version import __version__
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT
    assert __version__=="0.40.0"
    eng=CognitiveEngine(agent_id="aria-b13")
    eng.encode("My favorite color is blue.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    eng.encode("My favorite color is red.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    opened=eng.open_conflict_resolution("What is my favorite color?")
    assert opened["status"]=="open"
    out=eng.confirm_conflict_resolution(opened["session"]["id"], "blue")
    assert out["status"]=="confirmed"
