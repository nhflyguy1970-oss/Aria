"""M0G — ACM v0.19.0 Trusted Memory Ingestion promotion gates (D046)."""

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
def _m0g_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0g.db"))
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


def _graph_counts() -> tuple[int, int, int]:
    eng = acm_bridge.get_engine()
    return (
        len(eng.store.experiences),
        len(eng.store.concepts),
        len(eng.store.provenance),
    )


def _untrusted_sources() -> list[tuple[str, object]]:
    from aria_acm.acm.provenance import (
        HostOperation,
        IngestionActor,
        IngestionProvenance,
        MessageRole,
    )

    return [
        (
            "Tool memory_search worked for: Show the evidence for my favorite color.",
            IngestionProvenance(
                actor=IngestionActor.TOOL,
                host_operation=HostOperation.MEMORY_SEARCH,
                message_role=MessageRole.TOOL_RESULT,
            ),
        ),
        (
            "Diagnostic: my favorite color is probe-yellow.",
            IngestionProvenance(
                actor=IngestionActor.DIAGNOSTIC,
                host_operation=HostOperation.DIAGNOSTIC,
                message_role=MessageRole.DIAGNOSTIC_OUTPUT,
            ),
        ),
        (
            "Reflection trace: my favorite color is inferred-green.",
            IngestionProvenance(
                actor=IngestionActor.REFLECTION,
                host_operation=HostOperation.REFLECTION,
                message_role=MessageRole.REFLECTION_OUTPUT,
            ),
        ),
        (
            "System message: my favorite color is system-orange.",
            IngestionProvenance(
                actor=IngestionActor.SYSTEM,
                host_operation=HostOperation.SYSTEM_EVENT,
                message_role=MessageRole.SYSTEM_MESSAGE,
            ),
        ),
        (
            "Infrastructure log: my favorite color is log-white.",
            IngestionProvenance(
                actor=IngestionActor.INFRASTRUCTURE,
                host_operation=HostOperation.SYSTEM_EVENT,
                message_role=MessageRole.INFRASTRUCTURE_LOG,
            ),
        ),
        (
            "Implementation metadata: my favorite color is metadata-black.",
            IngestionProvenance(
                actor=IngestionActor.INFRASTRUCTURE,
                host_operation=HostOperation.ENCODING,
                message_role=MessageRole.METADATA,
            ),
        ),
    ]


@pytest.mark.m0g
def test_m0g_01_d046_promotion_lineage() -> None:
    """M0G-01: D046 Trusted Memory Ingestion lineage retained after later promotions."""
    import json

    meta = json.loads(Path("aria_acm/VERSION.json").read_text(encoding="utf-8"))
    for decision in (
        "D038",
        "D039",
        "D040",
        "D041",
        "D042",
        "D043",
        "D044",
        "D045",
        "D046",
    ):
        assert decision in meta.get("includes", [])
    problem = Path("docs/acm_integration/PROBLEM_REPORT_M0G.md").read_text(encoding="utf-8")
    assert "v0.19.0" in problem
    assert "D046" in problem
    assert "48938bc3c340a427b007527feff256ede34fc61a" in problem


@pytest.mark.m0g
def test_m0g_02_d046_trust_model_vendored() -> None:
    """M0G-02: D046 ingestion trust model is present and behaves identically."""
    from aria_acm.acm.provenance import (
        TRUSTED_USER_STATEMENT,
        HostOperation,
        IngestionActor,
        IngestionProvenance,
        MessageRole,
        evaluate_ingestion,
    )

    assert evaluate_ingestion(None).eligible is False
    assert evaluate_ingestion(None).reason == "missing_provenance"
    assert evaluate_ingestion(TRUSTED_USER_STATEMENT).eligible is True
    assert evaluate_ingestion(TRUSTED_USER_STATEMENT).reason == "trusted_user_statement"
    tool = IngestionProvenance(
        actor=IngestionActor.TOOL,
        host_operation=HostOperation.TOOL_EXECUTION,
        message_role=MessageRole.TOOL_RESULT,
    )
    decision = evaluate_ingestion(tool)
    assert decision.eligible is False
    assert decision.reason == "actor_not_autobiographical"


@pytest.mark.m0g
def test_m0g_03_missing_and_unknown_provenance_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M0G-03: missing/unknown provenance rejects before Semantic Extraction."""
    from aria_acm.acm.provenance import (
        HostOperation,
        IngestionActor,
        IngestionProvenance,
        MessageRole,
    )

    engine = acm_bridge.get_engine()
    before = _graph_counts()

    def _must_not_extract(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("semantic extraction must not run for rejected sources")

    monkeypatch.setattr("acm.semantic.extract_semantics", _must_not_extract)
    missing = engine.encode("My favorite color is blue.")
    unknown = engine.encode(
        "My favorite color is blue.",
        provenance=IngestionProvenance(
            actor=IngestionActor.UNKNOWN,
            host_operation=HostOperation.UNKNOWN,
            message_role=MessageRole.UNKNOWN,
        ),
    )

    assert missing["encoded"] is False
    assert missing["reason"] == "memory_trust"
    assert missing["detail"] == "missing_provenance"
    assert unknown["encoded"] is False
    assert unknown["reason"] == "memory_trust"
    assert unknown["detail"] == "unknown_actor"
    assert _graph_counts() == before


@pytest.mark.m0g
def test_m0g_04_untrusted_sources_never_become_memory() -> None:
    """M0G-04: tool/diagnostic/reflection/system/infra output rejected, zero mutation."""
    engine = acm_bridge.get_engine()
    before = _graph_counts()
    for text, provenance in _untrusted_sources():
        rejected = engine.encode(text, kind="preference", pin=True, provenance=provenance)
        assert rejected["encoded"] is False
        assert rejected["reason"] == "memory_trust"
        assert rejected["ingestion"]["eligible"] is False
    assert _graph_counts() == before
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "unknown"
    assert result["memory"] is None
    low = speech.lower()
    for artifact in ("probe-yellow", "inferred-green", "system-orange", "log-white"):
        assert artifact not in low


@pytest.mark.m0g
def test_m0g_05_user_knowledge_still_encodes() -> None:
    """M0G-05: genuine user knowledge stores through the host memory path."""
    name = acm_bridge.primary_remember("My name is Jeff.", entry_type="fact", tags=["identity"])
    color = acm_bridge.primary_remember(
        "My favorite color is blue.", entry_type="preference", tags=["preference"]
    )
    assert name.get("encoded") is True
    assert color.get("encoded") is True
    who_result, who_speech = _speak("Who am I?")
    assert who_result["status"] == "known"
    assert "your name is jeff" in who_speech.lower()
    color_result, color_speech = _speak("What is my favorite color?")
    assert color_result["status"] == "known"
    assert "your favorite color is blue" in color_speech.lower()
    assert color_result["uncertainty"] is None


@pytest.mark.m0g
def test_m0g_06_tool_artifact_cannot_contaminate_preference() -> None:
    """M0G-06: the original tool artifact cannot displace a taught preference."""
    acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")
    engine = acm_bridge.get_engine()
    text, provenance = _untrusted_sources()[0]
    for _ in range(5):
        rejected = engine.encode(text, provenance=provenance)
        assert rejected["encoded"] is False
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "known"
    assert "your favorite color is blue" in speech.lower()
    assert result["uncertainty"] is None


@pytest.mark.m0g
def test_m0g_07_source_provenance_durably_recorded() -> None:
    """M0G-07: accepted encodes record who/how/why in durable provenance."""
    entry = acm_bridge.primary_remember(
        "My favorite color is blue.", entry_type="preference"
    )
    engine = acm_bridge.get_engine()
    exp_id = str(entry.get("id") or "")
    assert exp_id
    records = engine.provenance_of(exp_id)
    assert records
    assert records[0]["source_actor"] == "user"
    assert records[0]["host_operation"] == "encoding"
    assert records[0]["message_role"] == "user_teaching"
    assert records[0]["eligibility_reason"] == "trusted_user_teaching"
    metadata = dict(engine.store.experiences[exp_id].metadata)
    assert metadata["source_actor"] == "user"
    assert metadata["source_eligibility_reason"] == "trusted_user_teaching"


@pytest.mark.m0g
def test_m0g_08_identity_regression_no_blend() -> None:
    """M0G-08: Identity certification (D042–D044) unchanged after D046."""
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


@pytest.mark.m0g
def test_m0g_09_preference_regression_update_retires_old() -> None:
    """M0G-09: Preference certification (D045) unchanged after D046."""
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


@pytest.mark.m0g
def test_m0g_10_speech_contamination_defense_retained() -> None:
    """M0G-10: D038 memory protection remains behind the D046 trust gate."""
    from aria_acm.acm.provenance import TRUSTED_USER_STATEMENT

    engine = acm_bridge.get_engine()
    blocked = engine.encode(
        "I fabricated that the user loves anchovy pizza",
        kind="experience",
        context_tags=("llm_generated",),
        provenance=TRUSTED_USER_STATEMENT,
    )
    assert blocked.get("encoded") is False
    assert blocked.get("reason") == "memory_protection"


@pytest.mark.m0g
def test_m0g_11_persistence_survives_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M0G-11: trusted memory and its source provenance persist across restart."""
    persist = tmp_path / "acm_m0g_persist.db"
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(persist))
    acm_bridge.reset_for_tests()
    _seed_assistant_aria()
    entry = acm_bridge.primary_remember(
        "My favorite color is blue.", entry_type="preference"
    )
    exp_id = str(entry.get("id") or "")
    assert "blue" in _speak("What is my favorite color?")[1].lower()

    acm_bridge.reset_for_tests()
    _seed_assistant_aria()
    engine = acm_bridge.get_engine()
    records = engine.provenance_of(exp_id)
    assert records
    assert records[0]["source_actor"] == "user"
    assert records[0]["message_role"] == "user_teaching"
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "known"
    assert "your favorite color is blue" in speech.lower()
