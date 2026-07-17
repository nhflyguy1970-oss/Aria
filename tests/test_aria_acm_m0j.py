"""M0J — ACM v0.22.0 Teaching Recognition promotion gates.

Certified standalone ACM v0.22.0 restores Preference behavioral certification
after a valid teaching regression: declarative statements spoken through
Memory Authority (``cognitive_respond``) encode before dispatch so
blue → green retires the previous preference correctly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager

LIVE_CONTAMINATION = (
    "Tool `memory_search` worked for: Show the evidence for my favorite color.",
    "Tool `memory_search` worked for: My favorite color is yellow.",
    "Tool `whatever` worked for: My favorite color is mauve.",
    "Auto-saved on exit — module memory; recent asks: who are you.",
    "Diagnostic: probe-yellow",
)


def _seed_assistant_aria() -> None:
    from aria_acm.acm.identity.assistant_profile import AssistantIdentityProfile

    eng = acm_bridge.get_engine()
    eng.identity.set_assistant_profile(AssistantIdentityProfile(name="ARIA", role="assistant"))


@pytest.fixture(autouse=True)
def _m0j_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0j.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


def _speak(q: str) -> tuple[dict, str]:
    out = acm_bridge.primary_cognitive_speak(q)
    return out["result"], (out.get("speech") or "").strip()


def _active_preferences() -> list[tuple[str, str]]:
    engine = acm_bridge.get_engine()
    return [
        (a.key, a.value)
        for c in engine.store.concepts.values()
        for a in c.attributes
        if a.key in ("favorite_color", "preference") and a.active
    ]


@pytest.mark.m0j
def test_m0j_01_embedded_version_pin() -> None:
    """M0J-01: embedded ACM matches standalone v0.22.0 pin."""
    from aria_acm.acm import __version__

    assert __version__ == "0.22.0"
    meta = json.loads(Path("aria_acm/VERSION.json").read_text(encoding="utf-8"))
    assert meta["source_version"] == "0.22.0"
    assert meta["source_tag"] == "v0.22.0"
    assert meta["source_commit"] == "2dd3715c211f1fdc5e1147dccf9c827be5af801b"
    assert meta["aria_acm_local_version"] == "aria-acm-v0.22.0-1"
    assert meta["promotion"] == "M0J"
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
        "D047",
    ):
        assert decision in meta.get("includes", [])
    teaching = Path("aria_acm/acm/authority/teaching.py")
    assert teaching.is_file()
    assert "detect_teaching" in teaching.read_text(encoding="utf-8")
    pipeline = Path("aria_acm/acm/authority/pipeline.py").read_text(encoding="utf-8")
    assert "_teach_if_declarative" in pipeline
    assert "teaching_encoded" in pipeline


@pytest.mark.m0j
def test_m0j_02_no_stale_vendored_files() -> None:
    """M0J-02: no bytecode tracked; Teaching Recognition present; no mixed pins."""
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "aria_acm"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    assert not [p for p in tracked if p.endswith(".pyc") or "__pycache__" in p]
    notice = Path("aria_acm/NOTICE").read_text(encoding="utf-8")
    assert "v0.22.0" in notice
    assert "2dd3715c211f1fdc5e1147dccf9c827be5af801b" in notice
    assert "Teaching Recognition" in notice
    # No mixed version strings in the vendored package version file
    assert Path("aria_acm/acm/_version.py").read_text(encoding="utf-8").strip() == (
        '__version__ = "0.22.0"'
    )


@pytest.mark.m0j
def test_m0j_03_cognitive_respond_blue_to_green_supersede(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M0J-03: teach blue then green via cognitive_respond; green wins; restart holds."""
    _seed_assistant_aria()

    result, _ = _speak("What is my favorite color?")
    assert result["status"] == "unknown"

    # Teach blue through Memory Authority (no explicit encode / remember)
    taught, speech = _speak("My favorite color is blue.")
    assert "teaching_encoded" in taught["reasoning_path"]
    assert "your favorite color is blue" in speech.lower()
    result, speech = _speak("What is my favorite color?")
    assert "your favorite color is blue" in speech.lower()

    # Teach green — the exact live certification regression
    taught, speech = _speak("My favorite color is green.")
    assert "teaching_encoded" in taught["reasoning_path"]
    assert "your favorite color is green" in speech.lower()
    result, speech = _speak("What is my favorite color?")
    assert "your favorite color is green" in speech.lower()

    engine = acm_bridge.get_engine()
    values = {
        (a.value, a.active)
        for c in engine.store.concepts.values()
        for a in c.attributes
        if a.key == "favorite_color"
    }
    assert values == {("blue", False), ("green", True)}

    # Evidence reflects teaching history and never mutates
    def _content_state() -> tuple:
        return (
            sorted(e.summary for e in engine.store.experiences.values()),
            sorted(
                (a.key, a.value, a.active)
                for c in engine.store.concepts.values()
                for a in c.attributes
            ),
        )

    before = _content_state()
    er, er_speech = _speak("Show the evidence for my favorite color.")
    assert er["status"] == "known"
    assert "green" in er_speech.lower()
    assert er.get("supporting_experiences")
    assert _content_state() == before

    # Re-teach green → no duplicate active attribute
    _speak("My favorite color is green.")
    assert _active_preferences() == [("favorite_color", "green")]

    engine.flush(kind="m0j")
    acm_bridge.reset_for_tests()
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "known"
    assert "your favorite color is green" in speech.lower()


@pytest.mark.m0j
def test_m0j_04_artifacts_and_questions_never_teach() -> None:
    """M0J-04: artifacts and interrogatives remain non-teaching through the pipeline."""
    _seed_assistant_aria()
    taught, _ = _speak("My favorite color is green.")
    assert "teaching_encoded" in taught["reasoning_path"]
    before = _active_preferences()

    for q in (
        "Is my favorite color yellow?",
        "What is my favorite color?",
        "Show the evidence for my favorite color.",
    ):
        r, _ = _speak(q)
        assert "teaching_encoded" not in r["reasoning_path"], q

    for wrap in LIVE_CONTAMINATION:
        r, _ = _speak(wrap)
        assert "teaching_encoded" not in r["reasoning_path"], wrap
    # Artifact with declarative shape is rejected by content trust
    r, _ = _speak("Tool `memory_search` worked for: My favorite color is mauve.")
    assert "teaching_encoded" not in r["reasoning_path"]
    assert any(p.startswith("teaching_rejected:") for p in r["reasoning_path"])

    assert _active_preferences() == before
    _, speech = _speak("What is my favorite color?")
    assert "your favorite color is green" in speech.lower()
    assert "tool" not in speech.lower()
    assert "mauve" not in speech.lower()


@pytest.mark.m0j
def test_m0j_05_identity_and_remember_path_regression() -> None:
    """M0J-05: Identity certification and primary_remember path remain valid."""
    _seed_assistant_aria()
    # Identity teaching via cognitive_respond
    taught, _ = _speak("My name is Jeff.")
    assert "teaching_encoded" in taught["reasoning_path"]
    result, speech = _speak("Who am I?")
    assert result["status"] == "known"
    assert "your name is jeff" in speech.lower()
    asst_result, asst_speech = _speak("Who are you?")
    assert "aria" in asst_speech.lower()
    assert "jeff" not in asst_speech.lower()

    # Explicit remember path still works (host remember action)
    entry = acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")
    assert entry["encoded"] is True
    _, speech = _speak("What is my favorite color?")
    assert "your favorite color is blue" in speech.lower()


@pytest.mark.m0j
def test_m0j_06_d046_trust_gate_intact() -> None:
    """M0J-06: D046 provenance gate still rejects untrusted actors."""
    from aria_acm.acm.provenance import (
        HostOperation,
        IngestionActor,
        IngestionProvenance,
        MessageRole,
    )

    _seed_assistant_aria()
    _speak("My favorite color is blue.")
    engine = acm_bridge.get_engine()
    before = len(engine.store.experiences)
    for actor, op, role in (
        (IngestionActor.TOOL, HostOperation.TOOL_EXECUTION, MessageRole.TOOL_RESULT),
        (IngestionActor.UNKNOWN, HostOperation.UNKNOWN, MessageRole.UNKNOWN),
    ):
        rejected = engine.encode(
            "My favorite color is artifact-mauve.",
            provenance=IngestionProvenance(actor=actor, host_operation=op, message_role=role),
        )
        assert rejected["encoded"] is False
        assert rejected["reason"] == "memory_trust"
    assert len(engine.store.experiences) == before
    _, speech = _speak("What is my favorite color?")
    assert "your favorite color is blue" in speech.lower()


@pytest.mark.m0j
def test_m0j_07_host_independence_teaching_module() -> None:
    """M0J-07: Teaching Recognition requires no host, model, or Aria import."""
    from aria_acm.acm.authority.teaching import detect_teaching

    assert detect_teaching("My favorite color is green.").is_teaching is True
    assert detect_teaching("What is my favorite color?").is_teaching is False
    assert detect_teaching("Is my favorite color yellow?").is_teaching is False
    assert detect_teaching("My name is Jeff.").is_teaching is True
