"""M0F — ACM v0.18.4 Preference Reconstruction Fix promotion gates (D045)."""

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
def _m0f_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0f.db"))
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


@pytest.mark.m0f
def test_m0f_01_d045_promotion_lineage() -> None:
    """M0F-01: D045 Preference Reconstruction lineage retained after later promotions."""
    import json

    meta = json.loads(Path("aria_acm/VERSION.json").read_text(encoding="utf-8"))
    for decision in ("D038", "D039", "D040", "D041", "D042", "D043", "D044", "D045"):
        assert decision in meta.get("includes", [])
    problem = Path("docs/acm_integration/PROBLEM_REPORT_M0F.md").read_text(encoding="utf-8")
    assert "v0.18.4" in problem
    assert "D045" in problem
    assert "3023ed85b1de5a9b19c5058509f1fda870f45555" in problem


@pytest.mark.m0f
def test_m0f_02_d045_answerability_apis_vendored() -> None:
    """M0F-02: D045 admissibility helpers are present in remembering organ."""
    from aria_acm.acm.remembering.organ import LEXICAL_SUPPORT_KEYS, _answerable
    from aria_acm.acm.concepts.model import Concept
    from aria_acm.acm.types import Attribute, ConceptRole

    assert "mentioned" in LEXICAL_SUPPORT_KEYS
    tokens = ["what", "favorite", "color"]
    lexical = Concept(
        id="c1",
        labels=["favorite"],
        attributes=[Attribute(key="mentioned", value="favorite")],
    )
    semantic = Concept(
        id="c2",
        labels=["favorite color"],
        role=ConceptRole.PREFERENCE,
        attributes=[Attribute(key="favorite_color", value="blue")],
    )
    assert _answerable(lexical, tokens) is False
    assert _answerable(semantic, tokens) is True


@pytest.mark.m0f
def test_m0f_03_unknown_preference() -> None:
    """M0F-03: fresh memory → What is my favorite color? → unknown."""
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "unknown"
    assert result["memory"] is None
    assert "blue" not in speech.lower()


@pytest.mark.m0f
def test_m0f_04_teach_store_retrieve_blue() -> None:
    """M0F-04: teach blue → retrieve → Your favorite color is blue."""
    encoded = acm_bridge.primary_remember(
        "My favorite color is blue.", entry_type="preference", tags=["preference"]
    )
    assert encoded.get("id") or encoded.get("source") == "acm"
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "known"
    assert "your favorite color is blue" in speech.lower()
    assert result["uncertainty"] is None


@pytest.mark.m0f
def test_m0f_05_repeated_identical_teach_no_conflict() -> None:
    """M0F-05: repeated identical teach → no duplicate conflict."""
    acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")
    acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "known"
    assert "your favorite color is blue" in speech.lower()
    assert result["uncertainty"] is None


@pytest.mark.m0f
def test_m0f_06_preference_update_retires_old() -> None:
    """M0F-06: blue → red update retires blue."""
    acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")
    acm_bridge.primary_remember(
        "Actually, my favorite color is red.", entry_type="preference"
    )
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "known"
    assert "your favorite color is red" in speech.lower()
    eng = acm_bridge.get_engine()
    values = {
        a.value: a.active
        for c in eng.store.concepts.values()
        for a in c.attributes
        if a.key == "favorite_color"
    }
    assert values.get("red") is True
    assert values.get("blue") is False


@pytest.mark.m0f
def test_m0f_07_lexical_support_never_artificial_conflict() -> None:
    """M0F-07: conversation-turn encoding must not manufacture competing_recollections."""
    acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")
    # Log the question as a conversation turn (the D045 false-conflict trigger).
    acm_bridge.primary_remember("What is my favorite color?", entry_type="experience")
    acm_bridge.primary_remember("What is my favorite color?", entry_type="experience")
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "known"
    assert result["uncertainty"] is None
    assert "your favorite color is blue" in speech.lower()
    assert result["uncertainty"] != "competing_recollections"


@pytest.mark.m0f
def test_m0f_08_true_semantic_conflict_preserved() -> None:
    """M0F-08: distinct semantic preference concepts still conflict."""
    acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")
    acm_bridge.primary_remember("My favourite colour is red.", entry_type="preference")
    eng = acm_bridge.get_engine()
    reconstruction = eng.remembering.what_do_i_remember("What is my favorite color?")
    assert reconstruction.ambiguous is True
    assert reconstruction.competing
    result, _speech = _speak("What is my favorite color?")
    assert result["status"] == "conflicting"
    assert result["uncertainty"] == "competing_recollections"


@pytest.mark.m0f
def test_m0f_09_lexical_metadata_never_rendered() -> None:
    """M0F-09: mentioned-only concepts never render as cognitive answers."""
    from aria_acm.acm.concepts.model import Concept
    from aria_acm.acm.types import Attribute, ConceptRole, ExplanationClass

    eng = acm_bridge.get_engine()
    concept = Concept(
        id="con_lexical_only",
        labels=["favorite"],
        role=ConceptRole.ENTITY,
        attributes=[Attribute(key="mentioned", value="favorite", confidence=0.9)],
    )
    answer, expl, conf = eng.remembering._format_from_concept(
        "What is my favorite color?", concept, energy=1.0
    )
    assert answer == ""
    assert expl == ExplanationClass.UNKNOWN
    assert conf == 0.0


@pytest.mark.m0f
def test_m0f_10_identity_regression_no_blend() -> None:
    """M0F-10: Identity certification still holds after Preference promotion."""
    acm_bridge.primary_remember("My name is Jeff.", entry_type="fact", tags=["identity"])
    user_result, user_speech = _speak("Who am I?")
    asst_result, asst_speech = _speak("Who are you?")
    assert user_result["status"] == "known"
    assert "your name is jeff" in user_speech.lower()
    assert "aria" not in user_speech.lower()
    assert asst_result["status"] == "known"
    assert "aria" in asst_speech.lower()
    assert "jeff" not in asst_speech.lower()
    assert "know me" not in asst_speech.lower()
