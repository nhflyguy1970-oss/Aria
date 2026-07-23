"""Aria promotion gates — Cap6 explainability retained under ACM v0.34.0 pin."""

from __future__ import annotations

import json
from pathlib import Path


def test_m5_cap6_pin() -> None:
    data = json.loads(
        (Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json").read_text()
    )
    assert data["source_version"] == "0.34.0"
    assert data["aria_acm_local_version"] == "aria-acm-v0.34.0-1"
    assert data["promotion"] == "M5-ACM-CAP7-STABILITY"


def test_m5_cap6_explain_learning_parity() -> None:
    from aria_acm.acm._version import __version__
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    assert __version__ == "0.34.0"
    eng = CognitiveEngine(agent_id="aria-m5-c6")
    eng.encode("I prefer local AI models.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    concept = max(
        (c for c in eng.store.concepts.values() if c.evidence_ids),
        key=lambda c: len(c.evidence_ids),
    )
    out = eng.explain_learning(concept.id)
    assert out["known"] is True
    assert out["exposes_internals"] is False
    assert out["invents_experiences"] is False
