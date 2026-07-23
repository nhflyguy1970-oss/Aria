"""Aria promotion gates — ACM v0.45.0 M5 Cap7 Learning Stability."""

from __future__ import annotations

import json
from pathlib import Path


def test_m5_cap7_pin() -> None:
    data = json.loads(
        (Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json").read_text()
    )
    assert data["source_version"] == "0.45.0"
    assert data["aria_acm_local_version"] == "aria-acm-v0.45.0-1"
    assert data["promotion"] == "PLATFORM-PRACTICAL-COMPLETE"
    assert "M5-Cap7" in data["includes"]


def test_m5_cap7_stability_parity() -> None:
    from aria_acm.acm._version import __version__
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    assert __version__ == "0.45.0"
    eng = CognitiveEngine(agent_id="aria-m5-c7")
    eng.encode("Bounded learning matters.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    report = eng.check_learning_stability()
    assert report["invents_experiences"] is False
    assert report["exposes_internals"] is False
    concept = next(iter(eng.store.concepts.values()))
    concept.confidence = 1.5
    out = eng.enforce_learning_stability()
    assert out["status"] == "enforced"
    assert concept.confidence <= eng.learning.stability_limits.max_confidence
    sleep_out = eng.sleep()
    assert sleep_out["learning_stability"]["status"] == "enforced"
