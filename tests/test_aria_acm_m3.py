"""M3 — Aria ACM primary authority gates (blueprint INTEGRATION_TEST_PLAN)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aria_core import acm_bridge, capability_bus, conversation_trace, memory_manager


@pytest.fixture(autouse=True)
def _m3_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data_dir: Path):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "0")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "1")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_primary.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


def _enable_primary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    acm_bridge.reset_for_tests()


@pytest.mark.m3
def test_m3_01_cap_bus_remember_recall_from_acm(monkeypatch: pytest.MonkeyPatch) -> None:
    """M3-01: Cap Bus remember/recall from ACM when PRIMARY."""
    _enable_primary(monkeypatch)
    assert acm_bridge.acm_is_authoritative() is True

    entry = capability_bus.remember(
        "User favorite coffee is costa rica light roast",
        entry_type="preference",
        namespace="profile",
    )
    assert isinstance(entry, dict)
    assert entry.get("source") == "acm"
    assert entry.get("id")

    hits = capability_bus.recall(query="costa rica coffee", limit=5)
    assert isinstance(hits, list)
    assert hits
    assert hits[0].get("source") == "acm" or "costa" in str(hits[0].get("content") or "").lower()

    panel = memory_manager.mission_control_panel()
    assert panel.get("authoritative") == "acm"
    obs = acm_bridge.panel_observables()
    assert obs["legacy_writes_while_primary"] == 0
    assert obs["primary_encode"] >= 1
    assert obs["primary_recall"] >= 1


@pytest.mark.m3
def test_m3_02_memory_behavior_matrix_acm_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """M3-02: MemoryEngine actions route to ACM under PRIMARY."""
    _enable_primary(monkeypatch)
    from jarvis.behaviors.memory.engine import MemoryEngine

    ctx = MagicMock()
    ctx.session.memory_namespace = "default"
    ctx.session.note_module = MagicMock()
    ctx.refresh_system_prompt = MagicMock()
    ctx.memory = MagicMock()

    rem = MemoryEngine.remember(ctx, {"text": "remember my dog is named River"}, "remember")
    assert rem.get("ok") is True
    assert rem.get("source") == "acm" or "River" in str(
        rem.get("response") or rem.get("message") or rem
    )

    search = MemoryEngine.memory_search(ctx, {"query": "River"}, "River")
    assert search.get("ok") is True
    assert search.get("source") == "acm"

    recall = MemoryEngine.recall(ctx, {"query": "dog"}, "what is my dog name")
    assert recall.get("ok") is True
    assert recall.get("source") == "acm"


@pytest.mark.m3
def test_m3_03_correction_soft_forget(monkeypatch: pytest.MonkeyPatch) -> None:
    """M3-03: correction revise + soft cool (no hard delete experiences)."""
    _enable_primary(monkeypatch)
    entry = memory_manager.remember("Favorite tea is chai", entry_type="preference")
    exp_id = entry["id"]
    before = len(acm_bridge.get_engine().store.experiences)

    ok = memory_manager.update_memory(exp_id, content="Favorite tea is green tea")
    assert ok is True
    after_revise = len(acm_bridge.get_engine().store.experiences)
    assert after_revise >= before  # lineage retained

    forget_ok = memory_manager.forget(entry_id=exp_id)
    assert isinstance(forget_ok, bool)
    # soft cool may target concept; experiences stay
    assert len(acm_bridge.get_engine().store.experiences) >= after_revise
    cooled = acm_bridge.primary_forget(query="tea")
    assert cooled.get("deleted") is False
    assert cooled.get("experiences_unchanged") is True or cooled.get("deleted") is False


@pytest.mark.m3
def test_m3_04_prepare_context_acm_no_cot(monkeypatch: pytest.MonkeyPatch) -> None:
    """M3-04: prepare_context from ACM; no CoT fields."""
    _enable_primary(monkeypatch)
    memory_manager.remember("User enjoys woodworking", entry_type="preference", namespace="profile")
    from jarvis.behaviors.memory.engine import MemoryEngine

    ctx = MagicMock()
    ctx.session.memory_namespace = "default"
    ctx.memory = MagicMock()
    parts, _citations = MemoryEngine.prepare_context(ctx, "what do I enjoy?")
    blob = "\n".join(parts).lower()
    assert "chain of thought" not in blob
    assert "cot" not in blob.split()
    assert "<think>" not in blob


@pytest.mark.m3
def test_m3_05_latency_slo(monkeypatch: pytest.MonkeyPatch) -> None:
    """M3-05: encode/remember p95 within blueprint encode SLO (≤500ms local)."""
    _enable_primary(monkeypatch)
    for i in range(25):
        memory_manager.remember(f"latency fact item{i}", entry_type="fact")
        memory_manager.search_memory(f"item{i}", limit=3)
    obs = acm_bridge.panel_observables()
    p95 = obs.get("shadow_p95_ms")
    assert p95 is not None
    assert p95 <= 500.0, f"p95 {p95} exceeds 500ms encode/recall SLO"


@pytest.mark.m3
def test_m3_06_rollback_drill(monkeypatch: pytest.MonkeyPatch) -> None:
    """M3-06: ROLLBACK flag restores legacy Cap Bus answers."""
    _enable_primary(monkeypatch)
    memory_manager.remember("acm only fact zebra42", entry_type="fact")

    monkeypatch.setenv("ARIA_ACM_PRIMARY", "0")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "1")
    assert acm_bridge.authoritative_route() == "rollback"
    assert acm_bridge.acm_is_authoritative() is False

    entry = memory_manager.remember("legacy after rollback fact", entry_type="fact")
    assert isinstance(entry, dict)
    # legacy entries use store ids; source may be absent
    assert entry.get("source") != "acm"
    panel = memory_manager.mission_control_panel()
    assert panel.get("authoritative") == "legacy"

    trace = conversation_trace.build_conversation_trace(
        prompt="x",
        intent={},
        action="recall",
        route="memory",
        handler="memory",
        latency_ms=1.0,
        route_latency_ms=1.0,
        response_length=0,
        error=None,
        conversation_id="m3-rb",
    )
    assert (trace.get("memory_operation") or {}).get("authoritative") == "legacy"


@pytest.mark.m3
def test_m3_isolation_keeps_legacy_available() -> None:
    """M3 suite isolations force PRIMARY off so legacy façades remain testable."""
    assert acm_bridge.primary_enabled() is False
    assert acm_bridge.acm_is_authoritative() is False
    entry = memory_manager.remember("still legacy when primary forced off", entry_type="fact")
    assert entry.get("source") != "acm"


@pytest.mark.m3
def test_m3_sup02_no_legacy_writes_while_primary(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_primary(monkeypatch)
    before = acm_bridge.panel_observables()["legacy_writes_while_primary"]
    for i in range(5):
        memory_manager.remember(f"primary write {i}", entry_type="fact")
    after = acm_bridge.panel_observables()["legacy_writes_while_primary"]
    assert after == before == 0
