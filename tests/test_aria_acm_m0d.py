"""M0D — ACM v0.18.1 Identity Pipeline + Semantic Extraction promotion gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager


@pytest.fixture(autouse=True)
def _m0d_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0d.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.m0d
def test_m0d_01_d042_promotion_lineage() -> None:
    """M0D-01: D042 Identity Pipeline promotion lineage retained after later promotions."""
    import json

    meta = json.loads(Path("aria_acm/VERSION.json").read_text(encoding="utf-8"))
    assert "D042" in meta.get("includes", [])
    assert "D041" in meta.get("includes", [])
    problem = Path("docs/acm_integration/PROBLEM_REPORT_M0D.md").read_text(encoding="utf-8")
    assert "v0.18.1" in problem
    assert "D042" in problem
    assert "137c24a40e6332744b972f6cb726ccb624248e5d" in problem


@pytest.mark.m0d
def test_m0d_02_semantic_and_trace_present() -> None:
    """M0D-02: D041 semantic + D042 pipeline_trace vendored."""
    from aria_acm.acm.identity.pipeline_trace import trace_identity_pipeline
    from aria_acm.acm.semantic import extract_semantics

    result = extract_semantics("My name is Jeff.", kind="experience")
    assert result.facts
    assert result.facts[0].value == "Jeff"
    assert callable(trace_identity_pipeline)


@pytest.mark.m0d
def test_m0d_03_identity_pipeline_via_bridge() -> None:
    """M0D-03: fresh memory → teach name → Who am I? → Your name is Jeff."""
    before = acm_bridge.primary_cognitive_speak("Who am I?")
    assert before["result"]["status"] in ("low_confidence", "unknown", "insufficient_evidence")
    assert "not confident" in (before.get("speech") or "").lower() or not (
        before["result"].get("memory") or ""
    ).strip()

    encoded = acm_bridge.primary_remember("My name is Jeff.", entry_type="fact", tags=["identity"])
    assert encoded.get("id") or encoded.get("source") == "acm"

    after = acm_bridge.primary_cognitive_speak("Who am I?")
    result = after["result"]
    speech = (after.get("speech") or "").strip()
    assert result["status"] == "known"
    assert result["confidence"] >= 0.85
    assert "your name is jeff" in (result.get("memory") or "").lower()
    assert "your name is jeff" in speech.lower()
    assert "mentioned" not in speech.lower()


@pytest.mark.m0d
def test_m0d_04_persistence_survives_engine_reset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """M0D-04: identity survives engine singleton reset (restart simulation)."""
    persist = tmp_path / "acm_m0d_persist.db"
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(persist))
    acm_bridge.reset_for_tests()
    acm_bridge.primary_remember("My name is Jeff.", entry_type="fact")
    after1 = acm_bridge.primary_cognitive_speak("Who am I?")
    assert "jeff" in (after1.get("speech") or "").lower()

    acm_bridge.reset_for_tests()
    after2 = acm_bridge.primary_cognitive_speak("Who am I?")
    assert after2["result"]["status"] == "known"
    assert "your name is jeff" in (after2.get("speech") or "").lower()


@pytest.mark.m0d
def test_m0d_05_prior_authority_intact() -> None:
    """M0D-05: D038–D040 APIs remain available."""
    eng = acm_bridge.get_engine()
    assert hasattr(eng, "classify_request")
    assert hasattr(eng, "route_request")
    assert hasattr(eng, "dispatch_request")
    assert hasattr(eng, "cognitive_respond")
    assert hasattr(eng, "speak_cognitive_result")
    cl = acm_bridge.primary_classify_request("Who am I?")
    assert cl.get("intent") == "user_identity"
    route = acm_bridge.primary_route_request("Who am I?")
    assert (route.get("ownership") or {}).get("primary_organ") == "identity"


@pytest.mark.m0d
def test_m0d_06_no_assistant_user_confusion() -> None:
    """M0D-06: user name does not land on assistant schema."""
    acm_bridge.primary_remember("My name is Jeff.", entry_type="fact")
    eng = acm_bridge.get_engine()
    user = eng.identity.schema_concept("user")
    agent = eng.identity.schema_concept("agent")
    assert any(a.key == "name" and a.value == "Jeff" and a.active for a in user.attributes)
    assert not any(a.key == "name" and a.value == "Jeff" and a.active for a in agent.attributes)
