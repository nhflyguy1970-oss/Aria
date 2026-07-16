"""M0E — ACM v0.18.3 Identity Rendering Isolation promotion gates (D043+D044)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager


def _seed_assistant_aria() -> None:
    from aria_acm.acm.identity.assistant_profile import AssistantIdentityProfile

    eng = acm_bridge.get_engine()
    eng.identity.set_assistant_profile(
        AssistantIdentityProfile(name="ARIA", role="assistant")
    )


@pytest.fixture(autouse=True)
def _m0e_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0e.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    _seed_assistant_aria()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


def _speak(q: str) -> tuple[dict, str]:
    out = acm_bridge.primary_cognitive_speak(q)
    return out["result"], (out.get("speech") or "").strip()


@pytest.mark.m0e
def test_m0e_01_embedded_version_pin() -> None:
    """M0E-01: embedded ACM matches standalone v0.18.3 pin."""
    import json

    from aria_acm.acm import __version__

    assert __version__ == "0.18.3"
    meta = json.loads(Path("aria_acm/VERSION.json").read_text(encoding="utf-8"))
    assert meta["source_version"] == "0.18.3"
    assert meta["source_tag"] == "v0.18.3"
    assert meta["source_commit"] == "7a695275f6311f3c782e14721892dabfa5b42823"
    assert meta["promotion"] == "M0E"
    assert "D044" in meta.get("includes", []) or meta.get("promotion_decision") == "D044"


@pytest.mark.m0e
def test_m0e_02_d043_d044_modules_vendored() -> None:
    """M0E-02: D043 assistant profile + D044 rendering isolation vendored."""
    from aria_acm.acm.identity.assistant_profile import AssistantIdentityProfile
    from aria_acm.acm.identity.rendering import isolate_identity_text
    from aria_acm.acm.identity.rendering import IdentityRenderTarget

    assert AssistantIdentityProfile(name="ARIA").resolved_name("aria") == "ARIA"
    out = isolate_identity_text(
        "I'm ARIA, and you know me as Jeff.",
        target=IdentityRenderTarget.ASSISTANT,
        forbidden_values={"Jeff"},
    )
    assert out is None or "jeff" not in out.lower()


@pytest.mark.m0e
def test_m0e_03_fresh_who_am_i_unknown() -> None:
    """M0E-03: fresh memory → Who am I? → unknown / insufficient."""
    result, speech = _speak("Who am I?")
    assert result["status"] in ("unknown", "low_confidence", "insufficient_evidence")
    low = speech.lower()
    assert "jeff" not in low
    assert "aria" not in low or "don't" in low or "not confident" in low or "know" in low


@pytest.mark.m0e
def test_m0e_04_teach_jeff_who_am_i() -> None:
    """M0E-04: teach name → Who am I? → Your name is Jeff."""
    acm_bridge.primary_remember("My name is Jeff.", entry_type="fact", tags=["identity"])
    result, speech = _speak("Who am I?")
    assert result["status"] == "known"
    assert "your name is jeff" in speech.lower()
    assert "aria" not in speech.lower()


@pytest.mark.m0e
def test_m0e_05_who_are_you_assistant_only() -> None:
    """M0E-05: Who are you? → My name is ARIA (no user facts)."""
    acm_bridge.primary_remember("My name is Jeff.", entry_type="fact")
    result, speech = _speak("Who are you?")
    assert result["status"] == "known"
    low = speech.lower()
    assert "aria" in low
    assert "jeff" not in low
    assert "know me" not in low
    assert "known as" not in low


@pytest.mark.m0e
def test_m0e_06_call_me_jeffrey_assistant_unchanged() -> None:
    """M0E-06: Call me Jeffrey → user updated; assistant still ARIA."""
    acm_bridge.primary_remember("My name is Jeff.", entry_type="fact")
    acm_bridge.primary_remember("Call me Jeffrey.", entry_type="fact")
    user_speech = _speak("Who am I?")[1].lower()
    assert "jeffrey" in user_speech or "jeff" in user_speech
    asst = _speak("Who are you?")[1].lower()
    assert "aria" in asst
    assert "jeffrey" not in asst
    assert "jeff" not in asst


@pytest.mark.m0e
def test_m0e_07_persistence_across_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """M0E-07: identity survives engine singleton reset (restart simulation)."""
    persist = tmp_path / "acm_m0e_persist.db"
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(persist))
    acm_bridge.reset_for_tests()
    _seed_assistant_aria()
    acm_bridge.primary_remember("My name is Jeff.", entry_type="fact")
    assert "jeff" in _speak("Who am I?")[1].lower()
    assert "aria" in _speak("Who are you?")[1].lower()

    acm_bridge.reset_for_tests()
    _seed_assistant_aria()
    assert _speak("Who am I?")[0]["status"] == "known"
    assert "your name is jeff" in _speak("Who am I?")[1].lower()
    assert "jeff" not in _speak("Who are you?")[1].lower()


@pytest.mark.m0e
def test_m0e_08_prior_authority_intact() -> None:
    """M0E-08: D038–D040 APIs remain available."""
    eng = acm_bridge.get_engine()
    assert hasattr(eng, "classify_request")
    assert hasattr(eng, "route_request")
    assert hasattr(eng, "dispatch_request")
    assert hasattr(eng, "cognitive_respond")
    assert hasattr(eng.identity, "render_user_identity")
    assert hasattr(eng.identity, "render_assistant_identity")
