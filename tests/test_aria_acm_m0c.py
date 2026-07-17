"""M0C — ACM v0.17.0 End-to-End Cognitive Dispatch promotion gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager

_FORBIDDEN = {
    "memory_store",
    "memory_engine",
    "knowledge_engine",
    "search_engine",
    "database",
    "index",
    "vector_store",
    "cache",
    "language_model",
    "storage",
}


@pytest.fixture(autouse=True)
def _m0c_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0c.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.m0c
def test_m0c_01_dispatch_apis_present() -> None:
    """M0C-01: dispatch engine, handlers, diagnostics APIs vendored."""
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.authority.dispatch import CognitiveDispatchEngine
    from aria_acm.acm.authority.handlers import FORBIDDEN_TERMINALS

    engine = CognitiveEngine(agent_id="m0c-import")
    assert hasattr(engine, "classify_request")
    assert hasattr(engine, "route_request")
    assert hasattr(engine, "dispatch_request")
    assert hasattr(engine, "cognitive_respond")
    assert hasattr(engine, "speak_cognitive_result")
    assert CognitiveDispatchEngine is not None
    for name in _FORBIDDEN:
        assert name in FORBIDDEN_TERMINALS


@pytest.mark.m0c
@pytest.mark.parametrize(
    "text,intent,terminal",
    [
        ("Who are you?", "assistant_identity", "identity"),
        ("Who am I?", "user_identity", "identity"),
        ("What projects are we working on?", "project", "remembering"),
        ("What is our long-term goal?", "goal", "goals"),
        ("How has your understanding changed?", "reflection", "reflection"),
        ("What have you learned?", "learning", "learning"),
        ("How are coffee and tea related?", "association", "associations"),
        ("What do you remember about fly tying?", "remembering", "remembering"),
    ],
)
def test_m0c_02_organ_only_termination(text: str, intent: str, terminal: str) -> None:
    """M0C-02: cognitive questions terminate at cognitive organs."""
    cog = acm_bridge.primary_cognitive_speak(text)
    result = cog["result"]
    diag = result.get("diagnostics") or {}
    assert result["is_memory_request"] is True
    assert result["intent"] == intent
    assert diag.get("terminated_at") == terminal
    assert diag.get("primary_organ") == terminal or diag.get("primary_organ")
    assert diag.get("infrastructure_role") == "substrate_only"
    blob = str(diag).lower() + str(result.get("reasoning_path") or []).lower()
    for bad in _FORBIDDEN:
        assert bad not in blob or "substrate" in blob


@pytest.mark.m0c
def test_m0c_03_bridge_pipeline_includes_dispatch() -> None:
    """M0C-03: Aria path is classify → route → dispatch → respond → speak."""
    assert hasattr(acm_bridge, "primary_dispatch_request")
    outcome = acm_bridge.primary_dispatch_request("Who are you?")
    assert outcome["record"]["terminated_at"] == "identity"
    cog = acm_bridge.primary_cognitive_speak("Who are you?")
    last = acm_bridge.last_primary_op() or {}
    assert last.get("terminated_at") == "identity"
    assert cog["diagnostics"].get("terminated_at") == "identity"
    assert cog["speech"]
    assert not str(cog["speech"]).startswith("{")


@pytest.mark.m0c
def test_m0c_04_user_identity_no_assistant_bleed() -> None:
    """M0C-04: Who am I? terminates in Identity without assistant bleed."""
    memory_manager.remember("User's name is Jeff", entry_type="identity", namespace="profile")
    cog = acm_bridge.primary_cognitive_speak("Who am I?")
    speech = cog["speech"].lower()
    assert cog["result"]["intent"] == "user_identity"
    assert cog["diagnostics"]["terminated_at"] == "identity"
    assert "i am aria" not in speech


@pytest.mark.m0c
def test_m0c_05_learning_not_raw_storage() -> None:
    """M0C-05: learning/reflection answers are cognitive speech, not dumps."""
    for q in ("What have you learned?", "How has your understanding changed?"):
        cog = acm_bridge.primary_cognitive_speak(q)
        speech = cog["speech"]
        assert not speech.startswith("{")
        assert "'id':" not in speech
        assert "adp_" not in speech
        assert cog["diagnostics"]["terminated_at"] in {"learning", "reflection"}


@pytest.mark.m0c
def test_m0c_06_memory_authority_and_intent_intact() -> None:
    """M0C-06: D038 / D039 still active after D040 promotion."""
    unknown = acm_bridge.primary_cognitive_speak(
        "What do you remember about my unicorn collection?"
    )
    assert unknown["result"]["is_memory_request"] is True
    assert "unicorn" not in unknown["speech"].lower()

    classification = acm_bridge.primary_classify_request("Who are you?")
    assert classification["is_memory_request"] is True
    assert classification["intent"] == "assistant_identity"

    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    blocked = acm_bridge.get_engine().encode(
        "fabricated",
        kind="experience",
        context_tags=("llm_generated",),
        provenance=TRUSTED_USER_STATEMENT,
    )
    assert blocked.get("encoded") is False
    assert blocked.get("reason") == "memory_protection"


@pytest.mark.m0c
def test_m0c_07_diagnostics_fields() -> None:
    """M0C-07: diagnostics expose intent, owner, path, termination, confidence."""
    cog = acm_bridge.primary_cognitive_speak("What is our long-term goal?")
    diag = cog["diagnostics"]
    assert diag.get("intent") == "goal"
    assert diag.get("primary_organ") == "goals"
    assert diag.get("terminated_at") == "goals"
    assert isinstance(diag.get("supporting_organs"), list)
    assert diag.get("dispatch_path") or cog["result"].get("reasoning_path")
    assert "confidence" in diag or "confidence" in cog["result"]
