"""Aria promotion gates — ACM v0.43.0 B20 Identity Correction & Assent UX."""
from __future__ import annotations

import json
from pathlib import Path


def test_b20_pin() -> None:
    data = json.loads(
        (Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json").read_text()
    )
    assert data["source_version"] == "0.43.0"
    assert data["aria_acm_local_version"] == "aria-acm-v0.43.0-1"
    assert data["promotion"] == "B47-POSSESSION-RECALL"
    assert "B20" in data["includes"]


def test_b20_identity_correction_parity() -> None:
    from aria_acm.acm._version import __version__
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    assert __version__ == "0.43.0"
    eng = CognitiveEngine(
        agent_id="aria-b20",
        assistant_identity={"name": "Aria", "role": "assistant"},
    )
    eng.encode("My name is Jeff.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    preview = eng.preview_identity_correction("My legal name changed to Jeffrey.")
    assert preview["status"] == "preview"
    out = eng.apply_identity_correction("My legal name changed to Jeffrey.")
    assert out["status"] == "applied"
    assert "jeffrey" in eng.cognitive_respond("Who am I?")["memory"].lower()
    asst = eng.cognitive_respond("Who are you?")["memory"].lower()
    assert "aria" in asst
    assert "jeffrey" not in asst
    blocked = eng.preview_identity_change(key="name", value="Jeffrey", who="assistant")
    assert blocked["status"] == "blocked_collision"
