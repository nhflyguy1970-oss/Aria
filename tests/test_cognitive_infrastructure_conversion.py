"""Cognitive Infrastructure Conversion — ACM sole brain gates."""

from __future__ import annotations

from pathlib import Path

import pytest

from aria_core import acm_bridge, conversation_trace, memory_manager


@pytest.fixture(autouse=True)
def _cic_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ARIA_ACM_ROLLBACK", raising=False)
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_cic.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.cic
def test_cic_01_store_search_projects_acm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """MemoryStore.search under PRIMARY terminates in ACM, not legacy JSON pool."""
    monkeypatch.setenv("JARVIS_MEMORY_BACKEND", "json")
    from jarvis.modules.memory import create_memory_store

    store = create_memory_store(tmp_path / "mem.json")
    encoded = acm_bridge.primary_remember(
        "Jeff prefers concise answers", entry_type="preference", tags=["cic"]
    )
    assert encoded.get("id") or encoded.get("source") == "acm"
    hits = store.search("concise answers", limit=5)
    assert hits
    assert any(h.get("source") == "acm" or "concise" in str(h.get("content", "")).lower() for h in hits)


@pytest.mark.cic
def test_cic_02_list_entries_projects_acm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_MEMORY_BACKEND", "json")
    from jarvis.modules.memory import create_memory_store

    store = create_memory_store(tmp_path / "mem2.json")
    acm_bridge.primary_remember("Project Aria uses embedded ACM", entry_type="fact")
    rows = store.list_entries()
    assert isinstance(rows, list)
    assert any("ACM" in str(r.get("content") or "") or r.get("source") == "acm" for r in rows)


@pytest.mark.cic
def test_cic_03_mission_control_is_acm_dashboard() -> None:
    panel = memory_manager.mission_control_panel(limit=20)
    assert panel.get("authoritative") == "acm"
    assert panel.get("legacy_disconnected") is True
    assert "ACM" in str(panel.get("title") or "")
    assert panel.get("organs", {}).get("dispatch") is True
    assert "experiences" in panel
    assert "memory_health" in panel
    assert panel.get("provider", "").startswith("aria_core.acm_bridge")


@pytest.mark.cic
def test_cic_04_conversation_trace_acm_diagnostics() -> None:
    acm_bridge.primary_cognitive_speak("Who are you?")
    trace = conversation_trace.build_conversation_trace(
        prompt="Who are you?",
        intent={"action": "recall", "params": {}},
        action="recall",
        route="Capability",
        handler="capability_bus",
        latency_ms=12.0,
        route_latency_ms=1.0,
        response_length=40,
        error=None,
        conversation_id="cic-trace-1",
    )
    mop = trace["memory_operation"]
    assert mop.get("authoritative") == "acm"
    assert mop.get("schema") == "memory_operation.v3"
    assert mop.get("intent") or mop.get("primary_cognitive_owner") or mop.get("acm_verb")
    assert "acm" in (trace.get("cognition") or {})
    acm_block = trace["cognition"]["acm"]
    assert "intent" in acm_block
    assert "termination_organ" in acm_block or "primary_cognitive_owner" in acm_block


@pytest.mark.cic
def test_cic_05_system_prompt_from_acm() -> None:
    from jarvis.memory_context import system_prompt_block

    acm_bridge.primary_remember("My name is Jeff", entry_type="fact", tags=["ns:profile"])
    block = system_prompt_block(object(), max_chars=2200)
    assert "Persistent cognitive context (ACM)" in block or block == ""


@pytest.mark.cic
def test_cic_06_no_legacy_cognitive_authority() -> None:
    assert acm_bridge.acm_is_authoritative() is True
    assert acm_bridge.authoritative_route() == "acm"
    dash = acm_bridge.acm_dashboard()
    assert dash["authoritative"] == "acm"
    assert "MemoryStore" not in str(dash.get("implementation") or "")
    assert "MemoryEngine" not in str(dash.get("title") or "")
