"""Aria promotion gates — ACM v0.44.0 B36 Erase Governance."""
from __future__ import annotations

import json
from pathlib import Path


def test_b36_pin() -> None:
    data = json.loads(
        (Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json").read_text()
    )
    assert data["source_version"] == "0.44.0"
    assert data["aria_acm_local_version"] == "aria-acm-v0.44.0-1"
    assert data["promotion"] == "PLATFORM-PRACTICAL-COMPLETE"
    assert "B36" in data["includes"]


def test_b36_erase_parity() -> None:
    from aria_acm.acm._version import __version__
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    assert __version__ == "0.44.0"
    eng = CognitiveEngine(agent_id="aria-b36")
    eng.encode("I live in Boston.", pin=True, provenance=TRUSTED_USER_STATEMENT)
    preview = eng.preview_erase_request("Forget my old address.")
    assert preview["status"] == "preview"
    out = eng.apply_erase_request("Forget my old address.")
    assert out["status"] == "applied"
    assert out["experiences_deleted"] is False
    blocked = eng.propose_erase_request("Forget my name.")
    assert blocked["status"] == "blocked_identity_protection"
