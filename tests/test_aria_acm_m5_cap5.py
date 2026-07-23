"""Aria promotion gates — Cap5 temporal patterns retained under ACM v0.43.0 pin."""

from __future__ import annotations

import json
from pathlib import Path


def test_m5_cap5_pin_and_temporal_module() -> None:
    ver = Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json"
    data = json.loads(ver.read_text(encoding="utf-8"))
    assert data["source_version"] == "0.43.0"
    assert data["aria_acm_local_version"] == "aria-acm-v0.43.0-1"
    assert Path("aria_acm/acm/learning/temporal_pattern.py").is_file()
    assert Path("aria_acm/acm/concepts/model.py").is_file()


def test_m5_cap5_temporal_pattern_parity() -> None:
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT
    from aria_acm.acm._version import __version__

    assert __version__ == "0.43.0"
    eng = CognitiveEngine(agent_id="aria-m5-c5")
    eng.encode(
        "I usually drink coffee after breakfast.",
        pin=True,
        provenance=TRUSTED_USER_STATEMENT,
    )
    eid = next(iter(eng.store.experiences))
    out = eng.learning.observe_temporal_pattern(
        antecedent="breakfast",
        consequent="coffee",
        experience_id=eid,
        period_hint="morning",
    )
    assert out["status"] in {"formed", "reinforced"}
    listed = eng.list_temporal_patterns(cue="coffee")
    assert listed["count"] >= 1
    explain = eng.explain_temporal_pattern("coffee")
    assert explain["invents_experiences"] is False
