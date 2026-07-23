"""M0K — ACM v0.23.0 multi-domain preference isolation + evidence lineage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager


def _seed_assistant_aria() -> None:
    from aria_acm.acm.identity.assistant_profile import AssistantIdentityProfile

    eng = acm_bridge.get_engine()
    eng.identity.set_assistant_profile(AssistantIdentityProfile(name="ARIA", role="assistant"))


@pytest.fixture(autouse=True)
def _m0k_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0k.db"))
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


@pytest.mark.m0k
def test_m0k_01_multi_domain_evidence_lineage() -> None:
    """M0K corrections remain in the embedded tree after later promotions."""
    organ = Path("aria_acm/acm/remembering/organ.py").read_text(encoding="utf-8")
    classification = Path("aria_acm/acm/authority/classification.py").read_text(
        encoding="utf-8"
    )
    assert "favorite_" in organ
    assert "_reconstruct_evidence" in organ or "Evidence (preference lineage)" in organ
    assert "evidence_cue" in classification
    meta = json.loads(Path("aria_acm/VERSION.json").read_text(encoding="utf-8"))
    # Superseded by M0L/M1+; pin must remain at least M0K lineage.
    assert meta["source_version"] >= "0.23.0"
    assert meta["promotion"] in (
        "M0K",
        "M0L",
        "M1",
        "M3-ACM",
        "M3-ACM-post",
        "M3-ACM-semantic",
        "M3-ACM-evolution",
        "M3-ACM-relational",
        "M3-ACM-relational-stab",
        "M3-ACM-prediction-stab",
        "M3-ACM-prediction-final",
        "M4-ACM-AML",
        "M5-ACM-CAP5-TEMPORAL",
        "M5-ACM-CAP6-EXPLAIN",
        "M5-ACM-CAP7-STABILITY",
        "B09-DIAGNOSTIC-SAFETY",
        "B10-CONVERSATION-DEBUG",
    ) or "M0K" in meta.get("notes", "")


@pytest.mark.m0k
def test_m0k_02_definition_of_done_conversation() -> None:
    """Exact M0K definition-of-done conversation through Memory Authority."""
    _seed_assistant_aria()
    for t in (
        "My favorite color is blue.",
        "My favorite food is pizza.",
        "My favorite fish is brook trout.",
    ):
        r, speech = _speak(t)
        assert "teaching_encoded" in r["reasoning_path"], t
        assert speech

    _, speech = _speak("What is my favorite color?")
    assert "your favorite color is blue" in speech.lower()
    _, speech = _speak("What is my favorite food?")
    assert "your favorite food is pizza" in speech.lower()
    _, speech = _speak("What is my favorite fish?")
    assert "brook trout" in speech.lower()

    _speak("My favorite color is green.")
    _, speech = _speak("What is my favorite color?")
    assert "your favorite color is green" in speech.lower()
    _, speech = _speak("What is my favorite food?")
    assert "your favorite food is pizza" in speech.lower()
    _, speech = _speak("What is my favorite fish?")
    assert "brook trout" in speech.lower()

    engine = acm_bridge.get_engine()
    n = len(engine.store.experiences)
    er, er_speech = _speak("Show me the evidence.")
    assert er["status"] == "known"
    text = (er.get("memory") or er_speech or "").lower()
    assert "favorite color" in text
    assert "blue" in text and "green" in text
    assert "retired" in text and "active" in text
    assert "pizza" in text
    assert "brook trout" in text or "fish" in text
    assert len(engine.store.experiences) == n


@pytest.mark.m0k
def test_m0k_03_cross_domain_isolation_and_lineage() -> None:
    _seed_assistant_aria()
    for color in ("blue", "green", "red", "purple", "black"):
        _speak(f"My favorite color is {color}.")
    _speak("My favorite food is pizza.")
    _speak("My favorite fish is brook trout.")

    _, speech = _speak("What is my favorite color?")
    assert "black" in speech.lower()
    assert "pizza" not in speech.lower()

    engine = acm_bridge.get_engine()
    values = {
        (a.key, a.value, a.active)
        for c in engine.store.concepts.values()
        for a in c.attributes
        if a.key.startswith("favorite_")
    }
    assert ("favorite_color", "black", True) in values
    assert ("favorite_color", "blue", False) in values
    assert ("favorite_food", "pizza", True) in values
    assert ("favorite_fish", "brook trout", True) in values

    er, _ = _speak("Show the evidence for my favorite color.")
    text = (er.get("memory") or "").lower()
    for color in ("blue", "green", "red", "purple", "black"):
        assert color in text
    assert "retired" in text


@pytest.mark.m0k
def test_m0k_04_restart_preserves_domains(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_assistant_aria()
    _speak("My favorite color is blue.")
    _speak("My favorite food is pizza.")
    _speak("My favorite fish is brook trout.")
    _speak("My favorite color is green.")
    acm_bridge.get_engine().flush(kind="m0k")

    acm_bridge.reset_for_tests()
    _, speech = _speak("What is my favorite color?")
    assert "green" in speech.lower()
    _, speech = _speak("What is my favorite food?")
    assert "pizza" in speech.lower()
    _, speech = _speak("What is my favorite fish?")
    assert "brook trout" in speech.lower()


@pytest.mark.m0k
def test_m0k_05_teaching_response_matches_domain() -> None:
    """Teaching food must not answer with an unrelated color preference."""
    _seed_assistant_aria()
    _speak("My favorite color is black.")
    r, speech = _speak("My favorite food is pizza.")
    assert "teaching_encoded" in r["reasoning_path"]
    assert "pizza" in speech.lower()
    assert "color" not in speech.lower() or "food" in speech.lower()
    assert "black" not in speech.lower()
