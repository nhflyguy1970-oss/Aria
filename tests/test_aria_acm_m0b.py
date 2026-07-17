"""M0B — ACM v0.16.0 Cognitive Intent Classification promotion gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager


@pytest.fixture(autouse=True)
def _m0b_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0b.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.m0b
def test_m0b_01_intent_routing_apis_present() -> None:
    """M0B-01: taxonomy, routing, route_request, D039 APIs vendored."""
    from aria_acm.acm import CognitiveIntent, classify_memory_request
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.authority.routing import CognitiveRoutingEngine
    from aria_acm.acm.authority.taxonomy import ORGAN_NONE

    engine = CognitiveEngine(agent_id="m0b-import")
    assert hasattr(engine, "classify_request")
    assert hasattr(engine, "route_request")
    assert hasattr(engine, "cognitive_respond")
    assert hasattr(engine, "speak_cognitive_result")
    assert CognitiveIntent.ASSISTANT_IDENTITY.value == "assistant_identity"
    assert ORGAN_NONE == "none"
    assert callable(classify_memory_request)
    assert CognitiveRoutingEngine is not None


@pytest.mark.m0b
@pytest.mark.parametrize(
    "text,intent,organ",
    [
        ("Who are you?", "assistant_identity", "identity"),
        ("Who am I?", "user_identity", "identity"),
        ("What projects are we working on?", "project", "remembering"),
        ("What is our long-term goal?", "goal", "goals"),
        ("How has your understanding changed?", "reflection", "reflection"),
        ("What do you think about ACM?", "reflection", "reflection"),
        ("How are coffee and tea related?", "association", "associations"),
        ("What have you learned?", "learning", "learning"),
    ],
)
def test_m0b_02_routing_matrix(text: str, intent: str, organ: str) -> None:
    """M0B-02: cognitive questions route to correct ownership."""
    decision = acm_bridge.primary_route_request(text)
    classification = decision["classification"]
    ownership = decision["ownership"]
    assert classification["is_memory_request"] is True
    assert classification["intent"] == intent
    assert ownership["primary_organ"] == organ


@pytest.mark.m0b
def test_m0b_03_pipeline_classify_route_respond_speak() -> None:
    """M0B-03: Aria path is classify → route → respond → speak."""
    cog = acm_bridge.primary_cognitive_speak("Who are you?")
    result = cog["result"]
    assert result["is_memory_request"] is True
    assert result["intent"] == "assistant_identity"
    assert result["allow_encode_from_speech"] is False
    assert cog["speech"]
    last = acm_bridge.last_primary_op() or {}
    assert last.get("primary_organ") == "identity"
    assert last.get("intent") == "assistant_identity"


@pytest.mark.m0b
def test_m0b_04_user_identity_distinct_from_assistant() -> None:
    """M0B-04: Who am I? must not use assistant who_am_i ownership swap."""
    user = acm_bridge.primary_route_request("Who am I?")
    assistant = acm_bridge.primary_route_request("Who are you?")
    assert user["classification"]["intent"] == "user_identity"
    assert assistant["classification"]["intent"] == "assistant_identity"
    cog = acm_bridge.primary_cognitive_speak("Who am I?")
    path = " ".join(cog["result"].get("reasoning_path") or [])
    assert "user_identity" in path or "user_identity_reconstruct" in path


@pytest.mark.m0b
def test_m0b_05_general_knowledge_not_forced_cognitive() -> None:
    """M0B-05: world knowledge remains non-cognitive."""
    c = acm_bridge.primary_classify_request("What is the speed of light?")
    assert c["is_memory_request"] is False
    assert c["intent"] in {"general_knowledge", "not_memory"}


@pytest.mark.m0b
def test_m0b_06_memory_authority_intact() -> None:
    """M0B-06: Memory Authority preserve — unknown + encode protection."""
    unknown = acm_bridge.primary_cognitive_speak(
        "What do you remember about my unicorn collection?"
    )
    assert unknown["result"]["is_memory_request"] is True
    assert "unicorn" not in unknown["speech"].lower()

    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    engine = acm_bridge.get_engine()
    blocked = engine.encode(
        "fabricated memory from speech",
        kind="experience",
        context_tags=("llm_generated",),
        provenance=TRUSTED_USER_STATEMENT,
    )
    assert blocked.get("encoded") is False
    assert blocked.get("reason") == "memory_protection"


@pytest.mark.m0b
def test_m0b_07_goal_and_project_search_routes() -> None:
    """M0B-07: Cap Bus/search façades inherit ownership via Memory Authority."""
    acm_bridge.get_engine().open_goal("Promote ACM cognitive routing", importance=0.8)
    memory_manager.remember(
        "We are working on the ACM M0B promotion project",
        entry_type="fact",
        tags=["project"],
    )
    goal = acm_bridge.primary_cognitive_speak("What is our long-term goal?")
    assert goal["result"]["intent"] == "goal"
    assert goal["result"]["is_memory_request"] is True

    project = acm_bridge.primary_route_request("What projects are we working on?")
    assert project["classification"]["intent"] == "project"
    assert project["classification"]["is_memory_request"] is True
