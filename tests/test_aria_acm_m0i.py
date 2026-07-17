"""M0I — ACM v0.21.0 Preference Behavioral Certification promotion gates.

Live blocker: Aria answered "What is my favorite color?" with
"Your preference is Tool `memory_search` worked for: Show the evidence for
my favorite color." — a live-format tool wrapper stored pre-D046 that the
v0.20.0 classifier missed. v0.21.0 certifies Preferences end-to-end.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aria_core import acm_bridge, memory_manager

LIVE_CONTAMINATION = (
    "Tool `memory_search` worked for: Show the evidence for my favorite color.",
    "Tool `memory_search` worked for: My favorite color is yellow.",
    "Tool `memory_about_user` worked for: Who am I?",
    "Auto-saved on exit — module memory; recent asks: who are you.",
    "Diagnostic: probe-yellow",
)


def _seed_assistant_aria() -> None:
    from aria_acm.acm.identity.assistant_profile import AssistantIdentityProfile

    eng = acm_bridge.get_engine()
    eng.identity.set_assistant_profile(AssistantIdentityProfile(name="ARIA", role="assistant"))


@pytest.fixture(autouse=True)
def _m0i_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m0i.db"))
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


@pytest.mark.m0i
def test_m0i_01_embedded_version_pin() -> None:
    """M0I-01: embedded ACM matches standalone v0.21.0 pin."""
    from aria_acm.acm import __version__

    assert __version__ == "0.21.0"
    meta = json.loads(Path("aria_acm/VERSION.json").read_text(encoding="utf-8"))
    assert meta["source_version"] == "0.21.0"
    assert meta["source_tag"] == "v0.21.0"
    assert meta["source_commit"] == "818d89d8e4ba2efab491b5d947b03155b6303df4"
    assert meta["aria_acm_local_version"] == "aria-acm-v0.21.0-1"
    assert meta["promotion"] == "M0I"
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


@pytest.mark.m0i
def test_m0i_02_no_stale_vendored_files() -> None:
    """M0I-02: no bytecode tracked in git; no v0.20.0 remnants in the tree."""
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "aria_acm"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    assert not [p for p in tracked if p.endswith(".pyc") or "__pycache__" in p]
    # v0.21.0 content markers present (content gate + certification surfaces)
    root = Path("aria_acm/acm")
    protection = (root / "authority" / "protection.py").read_text(encoding="utf-8")
    assert "content_artifact" in protection
    cleanup = (root / "provenance" / "legacy_cleanup.py").read_text(encoding="utf-8")
    assert "host_autosave" in cleanup


@pytest.mark.m0i
def test_m0i_03_live_preference_certification_fresh_to_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M0I-03: fresh → unknown → blue → no duplicate → red → restart → red."""
    _seed_assistant_aria()

    # Fresh memory → Unknown
    result, _ = _speak("What is my favorite color?")
    assert result["status"] == "unknown"

    # Teach blue → Blue
    entry = acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")
    assert entry["encoded"] is True
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "known"
    assert "your favorite color is blue" in speech.lower()

    # Teach blue again → no duplicate active attribute
    acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")
    assert _active_preferences() == [("favorite_color", "blue")]

    # Teach red → Red, blue retired
    acm_bridge.primary_remember("My favorite color is red.", entry_type="preference")
    result, speech = _speak("What is my favorite color?")
    assert "your favorite color is red" in speech.lower()
    engine = acm_bridge.get_engine()
    values = {
        (a.value, a.active)
        for c in engine.store.concepts.values()
        for a in c.attributes
        if a.key == "favorite_color"
    }
    assert values == {("blue", False), ("red", True)}
    engine.flush(kind="m0i")

    # Restart (fresh bridge singleton over the same store) → Red
    acm_bridge.reset_for_tests()
    result, speech = _speak("What is my favorite color?")
    assert result["status"] == "known"
    assert "your favorite color is red" in speech.lower()


@pytest.mark.m0i
def test_m0i_04_live_contamination_payloads_ignored() -> None:
    """M0I-04: previous live contamination payloads cannot enter memory."""
    _seed_assistant_aria()
    acm_bridge.primary_remember("My favorite color is red.", entry_type="preference")
    engine = acm_bridge.get_engine()
    before = len(engine.store.experiences)

    for payload in LIVE_CONTAMINATION:
        entry = acm_bridge.primary_remember(payload, entry_type="strategy")
        assert entry["encoded"] is False, payload

    assert len(engine.store.experiences) == before
    assert _active_preferences() == [("favorite_color", "red")]
    _, speech = _speak("What is my favorite color?")
    assert "your favorite color is red" in speech.lower()


@pytest.mark.m0i
def test_m0i_05_evidence_request_no_mutation() -> None:
    """M0I-05: show evidence → evidence only; memory content unchanged."""
    _seed_assistant_aria()
    acm_bridge.primary_remember("My favorite color is red.", entry_type="preference")
    engine = acm_bridge.get_engine()

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
    result, speech = _speak("Show the evidence for my favorite color.")
    assert result["status"] == "known"
    assert "red" in speech.lower()
    assert "tool" not in speech.lower()
    assert result.get("supporting_experiences")

    # Recall reconsolidation may adjust confidence, but no experience or
    # attribute content may change and nothing new may be encoded.
    assert _content_state() == before
    assert _active_preferences() == [("favorite_color", "red")]


@pytest.mark.m0i
def test_m0i_06_repeat_contamination_still_red() -> None:
    """M0I-06: repeated contamination attempts leave the preference red."""
    _seed_assistant_aria()
    acm_bridge.primary_remember("My favorite color is red.", entry_type="preference")
    for _ in range(3):
        for payload in LIVE_CONTAMINATION:
            acm_bridge.primary_remember(payload, entry_type="strategy")
        _, speech = _speak("What is my favorite color?")
        assert "your favorite color is red" in speech.lower()
    engine = acm_bridge.get_engine()
    assert engine.cleanup_legacy_contamination()["clean"] is True


@pytest.mark.m0i
def test_m0i_07_tool_outcome_host_writer_cannot_contaminate() -> None:
    """M0I-07: the live writer (record_tool_outcome) is rejected end-to-end."""
    from jarvis.trust_memory import record_tool_outcome

    _seed_assistant_aria()
    acm_bridge.primary_remember("My favorite color is red.", entry_type="preference")

    class _Store:
        def similar_exists(self, content: str) -> bool:
            return False

        def add(self, entry_type: str, content: str, tags=None, namespace="jarvis"):
            return acm_bridge.primary_remember(content, entry_type=entry_type, tags=tags)

    entry = record_tool_outcome(
        _Store(), action="memory_search", detail="Show the evidence for my favorite color."
    )
    assert entry is not None and entry["encoded"] is False
    _, speech = _speak("What is my favorite color?")
    assert "your favorite color is red" in speech.lower()
    assert "tool" not in speech.lower()


@pytest.mark.m0i
def test_m0i_08_marker_version_upgrade_remigrates_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M0I-08: a store migrated by v0.20.0's defective classifier is re-migrated."""
    from aria_acm.acm.api.engine import CognitiveEngine
    from aria_acm.acm.types import Attribute

    persist = tmp_path / "live" / "cognitive.db"
    seeder = CognitiveEngine(agent_id="aria", persist_path=str(persist), auto_persist=True)
    # Live-format contaminated graph (backtick wrappers the old classifier missed).
    from aria_acm.acm.provenance import TRUSTED_USER_TEACHING

    seeder.encode("My favorite color is blue.", provenance=TRUSTED_USER_TEACHING)
    tool = LIVE_CONTAMINATION[0]
    exp = seeder.experiences.birth(
        summary=tool,
        metadata={
            "evidence": tool,
            "semantic_extraction": "1",
            "fact_0_kind": "preference",
            "fact_0_property": "favorite_color",
            "fact_0_subject": "user",
            "fact_0_value": "conflicting?",
        },
    )
    for c in seeder.store.concepts.values():
        if any(a.key == "favorite_color" for a in c.attributes):
            for a in c.attributes:
                if a.key == "favorite_color":
                    a.active = False
            c.attributes.append(
                Attribute(
                    key="favorite_color",
                    value="conflicting?",
                    confidence=0.8,
                    active=True,
                    version=2,
                    evidence_ids=[exp.id],
                )
            )
            c.attributes.append(
                Attribute(
                    key="preference",
                    value=tool,
                    confidence=0.8,
                    active=True,
                    version=1,
                    evidence_ids=[exp.id],
                )
            )
            if exp.id not in c.evidence_ids:
                c.evidence_ids.append(exp.id)
    seeder.flush(kind="checkpoint")

    # Simulate the v0.20.0 marker (that run found nothing).
    marker = persist.with_name(persist.name + ".d047_cleanup.json")
    marker.write_text(
        json.dumps({"acm_version": "0.20.0", "report": {"clean": True}}), encoding="utf-8"
    )

    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(persist))
    acm_bridge.reset_for_tests()
    engine = acm_bridge.get_engine()

    recorded = acm_bridge.legacy_cleanup_report()
    assert recorded is not None
    assert recorded["acm_version"] == "0.21.0"
    assert recorded["report"]["removed_experiences"] >= 1
    blob = " ".join(e.summary.lower() for e in engine.store.experiences.values())
    assert "tool `memory_search`" not in blob
    result = engine.cognitive_respond("What is my favorite color?")
    assert result["memory"] == "Your favorite color is blue."

    # Same-version restart: not processed again.
    marker_bytes = marker.read_bytes()
    acm_bridge.reset_for_tests()
    acm_bridge.get_engine()
    assert marker.read_bytes() == marker_bytes


@pytest.mark.m0i
def test_m0i_09_identity_and_d046_regression() -> None:
    """M0I-09: Identity certification and D046 provenance gate hold."""
    from aria_acm.acm.provenance import (
        HostOperation,
        IngestionActor,
        IngestionProvenance,
        MessageRole,
    )

    _seed_assistant_aria()
    acm_bridge.primary_remember("My name is Jeff.", entry_type="fact", tags=["identity"])
    acm_bridge.primary_remember("My favorite color is blue.", entry_type="preference")

    result, speech = _speak("Who am I?")
    assert result["status"] == "known"
    assert "your name is jeff" in speech.lower()
    asst_result, asst_speech = _speak("Who are you?")
    assert "aria" in asst_speech.lower()
    assert "jeff" not in asst_speech.lower()

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
