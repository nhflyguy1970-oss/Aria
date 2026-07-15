"""M0A — ACM v0.15.0 Memory Authority promotion gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager


@pytest.fixture(autouse=True)
def _m0a_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0a.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.m0a
def test_m0a_01_authority_package_imported() -> None:
    """M0A-01: vendored authority package and D038 APIs present."""
    from aria_acm.acm import (
        CognitiveMemoryResult,
        MemoryStatus,
        classify_memory_request,
        speak_cognitive_result,
    )
    from aria_acm.acm.api.engine import CognitiveEngine

    engine = CognitiveEngine(agent_id="m0a-import")
    assert hasattr(engine, "classify_request")
    assert hasattr(engine, "cognitive_respond")
    assert hasattr(engine, "speak_cognitive_result")
    assert CognitiveMemoryResult is not None
    assert MemoryStatus.UNKNOWN.value == "unknown"
    assert callable(classify_memory_request)
    assert callable(speak_cognitive_result)


@pytest.mark.m0a
def test_m0a_02_bridge_routes_memory_through_pipeline() -> None:
    """M0A-02: primary search uses classify → cognitive_respond → speak."""
    memory_manager.remember(
        "User favorite coffee is costa rica light roast",
        entry_type="preference",
        namespace="profile",
    )
    classification = acm_bridge.primary_classify_request("What is my favorite coffee?")
    assert classification.get("is_memory_request") is True

    cog = acm_bridge.primary_cognitive_speak("What is my favorite coffee?")
    result = cog["result"]
    assert result.get("schema") == "cognitive_memory_result.v1"
    assert result.get("is_memory_request") is True
    assert result.get("allow_encode_from_speech") is False
    speech = cog["speech"]
    assert speech
    assert "invent" not in speech.lower()

    hits = memory_manager.search_memory("favorite coffee", limit=3)
    assert hits
    assert hits[0].get("source") == "acm"
    assert hits[0].get("cognitive_status")
    blob = str(hits[0].get("content") or "").lower()
    assert (
        "coffee" in blob
        or "roast" in blob
        or "don't" in blob
        or "conflicting" in blob
        or "competing" in blob
    )


@pytest.mark.m0a
def test_m0a_03_unknown_remains_unknown() -> None:
    """M0A-03: unknown memories stay unknown — speech cannot invent."""
    cog = acm_bridge.primary_cognitive_speak("What do you remember about my unicorn collection?")
    result = cog["result"]
    assert result.get("is_memory_request") is True
    assert result.get("status") in {"unknown", "insufficient_evidence", "low_confidence"}
    speech = cog["speech"].lower()
    assert speech
    assert "unicorn" not in speech
    assert any(
        phrase in speech
        for phrase in (
            "don't currently know",
            "enough experiences",
            "not confident",
            "don't yet",
        )
    )


@pytest.mark.m0a
def test_m0a_04_encode_rejects_llm_generated() -> None:
    """M0A-04: llm_generated / speech contamination blocked at encode."""
    engine = acm_bridge.get_engine()
    blocked = engine.encode(
        "I made up that the user loves pineapple pizza",
        kind="experience",
        context_tags=("llm_generated",),
    )
    assert blocked.get("encoded") is False
    assert blocked.get("reason") == "memory_protection"


@pytest.mark.m0a
def test_m0a_05_identity_uses_pipeline() -> None:
    """M0A-05: identity requests route through Memory Authority."""
    cog = acm_bridge.primary_cognitive_speak("Who are you?")
    result = cog["result"]
    assert result.get("intent") in {"identity", "assistant_identity"}
    assert result.get("is_memory_request") is True
    path = result.get("reasoning_path") or []
    assert any("classify" in step for step in path)
