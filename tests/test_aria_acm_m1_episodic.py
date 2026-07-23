"""M1 episodic — ACM autobiographical memory (vendored package).

Gates the promoted ACM through Aria's acm_bridge. Does **not** add Aria host
episodic NLU — cognitive authority is the unchanged ACM package only.

Distinct from ``tests/test_aria_acm_m1.py`` (legacy Shadow measure gates).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager


TEACHINGS = (
    "Yesterday I bought a kayak.",
    "Yesterday I cleaned my garage.",
    "Last week I went fishing.",
    "This morning I installed a GPU.",
    "Last Tuesday I visited my brother.",
)


@pytest.fixture(autouse=True)
def _m1ep_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m1ep.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    monkeypatch.setenv("ARIA_TEACHING_DEBUG", "0")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


def _speak(q: str) -> tuple[dict, str]:
    out = acm_bridge.primary_cognitive_speak(q)
    return out["result"], (out.get("speech") or "").strip()


@pytest.mark.m1ep
def test_m1ep_01_version_pin() -> None:
    ver = Path(__file__).resolve().parents[1] / "aria_acm" / "VERSION.json"
    data = json.loads(ver.read_text())
    assert data["source_version"] == "0.42.0"
    assert data["source_tag"] == "v0.42.0"
    assert data["aria_acm_local_version"] == "aria-acm-v0.42.0-1"
    from aria_acm.acm._version import __version__

    assert __version__ == "0.42.0"


@pytest.mark.m1ep
def test_m1ep_02_event_teaching_and_temporal_reconstruction() -> None:
    for t in TEACHINGS:
        r, _ = _speak(t)
        assert "teaching_encoded" in (r.get("reasoning_path") or []), t

    r, spoken = _speak("What happened yesterday?")
    assert r["status"] == "known"
    low = spoken.lower()
    assert "kayak" in low and "garage" in low

    r, spoken = _speak("What did I buy yesterday?")
    assert r["status"] == "known"
    assert "kayak" in spoken.lower()

    r, spoken = _speak("What happened last week?")
    assert r["status"] == "known"
    assert "fishing" in spoken.lower()

    r, spoken = _speak("What happened before buying the kayak?")
    assert r["status"] == "known"
    assert "fishing" in spoken.lower() or "brother" in spoken.lower()

    r, spoken = _speak("What happened after cleaning the garage?")
    assert r["status"] == "known"
    assert "gpu" in spoken.lower()


@pytest.mark.m1ep
def test_m1ep_03_event_evidence_and_unknown() -> None:
    for t in TEACHINGS:
        _speak(t)

    r, spoken = _speak("Show me the evidence.")
    assert r["status"] == "known"
    low = spoken.lower()
    assert "kayak" in low and "yesterday i bought a kayak" in low

    r, spoken = _speak("What happened last month?")
    assert r["status"] == "unknown"
    assert "don't currently know" in spoken.lower()


@pytest.mark.m1ep
def test_m1ep_04_m0_regression_through_bridge() -> None:
    for t in (
        "My name is Jeffrey.",
        "My favorite color is blue.",
        "My favorite color is green.",
    ):
        _speak(t)
    r, spoken = _speak("What is my favorite color?")
    assert r["status"] == "known"
    assert "green" in spoken.lower()
    r, spoken = _speak("Why isn't blue active?")
    assert r["status"] == "known"
    assert "blue" in spoken.lower() and "green" in spoken.lower()
