"""M0L — ACM v0.24.0 memory explanation + active-only personal summary.

Regression gates through the full Aria routing path (NLU → Memory Authority),
not ACM in isolation.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from aria_core import acm_bridge, memory_manager
from jarvis.nlu.mapping import apply_intent_guards, nlu_to_router_intent, resolve_memory_route
from jarvis.nlu.pipeline import analyze_prompt
from jarvis.runtime_routing import is_runtime_routing_question, route_runtime_priority
from jarvis.session import SessionContext


def _seed_assistant_aria() -> None:
    from aria_acm.acm.identity.assistant_profile import AssistantIdentityProfile

    eng = acm_bridge.get_engine()
    eng.identity.set_assistant_profile(AssistantIdentityProfile(name="ARIA", role="assistant"))


@pytest.fixture(autouse=True)
def _m0l_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0l.db"))
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


def _route(prompt: str) -> dict:
    with patch("jarvis.nlu.semantic.classify_semantic", return_value=None):
        result = analyze_prompt(prompt, SessionContext())
    intent = nlu_to_router_intent(result)
    assert intent is not None, prompt
    return intent


@pytest.mark.m0l
def test_m0l_01_embedded_version_pin() -> None:
    from aria_acm.acm import __version__

    assert __version__ == "0.24.0"
    meta = json.loads(Path("aria_acm/VERSION.json").read_text(encoding="utf-8"))
    assert meta["source_version"] == "0.24.0"
    assert meta["source_tag"] == "v0.24.0"
    assert meta["source_commit"] == "3c3bdbc0b1e7566da7922df422c72578e5550df5"
    assert meta["aria_acm_local_version"] == "aria-acm-v0.24.0-1"
    assert meta["promotion"] == "M0L"
    organ = Path("aria_acm/acm/remembering/organ.py").read_text(encoding="utf-8")
    assert "_reconstruct_explanation" in organ
    assert "_reconstruct_personal_summary" in organ
    assert "memory_explanation_cue" in Path(
        "aria_acm/acm/authority/classification.py"
    ).read_text(encoding="utf-8")


@pytest.mark.m0l
@pytest.mark.parametrize(
    "prompt",
    [
        "Why is green my favorite color?",
        "Why isn't blue active?",
        "What replaced pizza?",
        "Why is brown trout active?",
        "What do you know about me?",
    ],
)
def test_m0l_02_aria_routing_memory_authority_not_mission_control(prompt: str) -> None:
    """Full Aria path: NLU + runtime guards never send explanations to MC."""
    assert resolve_memory_route(prompt) is not None
    assert resolve_memory_route(prompt)["action"] == "memory_about_user"
    with patch("jarvis.nlu.semantic.classify_semantic", return_value=None):
        result = analyze_prompt(prompt, SessionContext())
    assert apply_intent_guards(result) == "memory"
    routed = _route(prompt)
    assert routed["action"] == "memory_about_user"
    assert routed["params"].get("question") == prompt
    assert is_runtime_routing_question(prompt) is False
    assert route_runtime_priority(prompt) is None


@pytest.mark.m0l
def test_m0l_03_definition_of_done_conversation() -> None:
    """Exact M0L definition-of-done conversation through Memory Authority."""
    _seed_assistant_aria()
    for t in (
        "My name is Jeffrey.",
        "My favorite color is blue.",
        "My favorite color is green.",
        "My favorite food is pizza.",
        "My favorite food is tacos.",
        "My favorite fish is brook trout.",
        "My favorite fish is brown trout.",
    ):
        r, speech = _speak(t)
        assert "teaching_encoded" in r["reasoning_path"] or r["status"] in (
            "known",
            "not_memory",
        ), t

    # Route each explanation through Aria NLU first, then Memory Authority.
    for q in (
        "Why is green my favorite color?",
        "Why isn't blue active?",
        "What replaced pizza?",
        "Why is brown trout active?",
        "What do you know about me?",
    ):
        routed = _route(q)
        assert routed["action"] == "memory_about_user"
        assert routed["params"]["question"] == q

    r, speech = _speak("Why is green my favorite color?")
    assert r["status"] == "known"
    assert r.get("uncertainty") is None
    text = (speech or r.get("memory") or "").lower()
    assert "green" in text and "blue" in text
    assert "retired" in text or "replaced" in text or "later taught" in text

    r, speech = _speak("Why isn't blue active?")
    assert r["status"] == "known"
    text = (speech or r.get("memory") or "").lower()
    assert "blue" in text and "green" in text

    r, speech = _speak("What replaced pizza?")
    assert r["status"] == "known"
    text = (speech or r.get("memory") or "").lower()
    assert "tacos" in text and "pizza" in text

    r, speech = _speak("Why is brown trout active?")
    assert r["status"] == "known"
    text = (speech or r.get("memory") or "").lower()
    assert "brown trout" in text
    assert "brook" in text or "replaced" in text or "taught" in text

    r, speech = _speak("What do you know about me?")
    assert r["status"] == "known"
    text = (speech or r.get("memory") or "").lower()
    assert "jeffrey" in text
    assert "green" in text
    assert "tacos" in text
    assert "brown trout" in text
    # Active-only summary
    assert "blue" not in text
    assert "pizza" not in text
    assert "brook" not in text


@pytest.mark.m0l
def test_m0l_04_multi_domain_explanation_and_evidence_backed() -> None:
    _seed_assistant_aria()
    for t in (
        "My favorite color is blue.",
        "My favorite color is green.",
        "My favorite food is pizza.",
        "My favorite food is tacos.",
        "My favorite fish is brook trout.",
        "My favorite fish is brown trout.",
    ):
        _speak(t)

    color = (_speak("Why is green my favorite color?")[1] or "").lower()
    food = (_speak("What replaced pizza?")[1] or "").lower()
    fish = (_speak("Why is brown trout active?")[1] or "").lower()
    assert "green" in color and "pizza" not in color
    assert "tacos" in food and "green" not in food
    assert "brown trout" in fish and "pizza" not in fish

    n = len(acm_bridge.get_engine().store.experiences)
    er, er_speech = _speak("Show me the evidence.")
    assert er["status"] == "known"
    etext = (er_speech or er.get("memory") or "").lower()
    assert "retired" in etext and "active" in etext
    assert len(acm_bridge.get_engine().store.experiences) == n


@pytest.mark.m0l
def test_m0l_05_active_only_personal_summary() -> None:
    _seed_assistant_aria()
    for t in (
        "My name is Jeffrey.",
        "My favorite color is blue.",
        "My favorite color is green.",
        "My favorite food is pizza.",
        "My favorite food is tacos.",
    ):
        _speak(t)
    r, speech = _speak("What do you know about me?")
    assert r["status"] == "known"
    text = (speech or r.get("memory") or "").lower()
    assert "jeffrey" in text
    assert "green" in text and "tacos" in text
    assert "blue" not in text and "pizza" not in text
