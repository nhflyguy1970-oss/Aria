"""M1 — Aria ACM Shadow measure gates (blueprint INTEGRATION_TEST_PLAN)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aria_core import acm_bridge, conversation_trace, memory_manager


@pytest.fixture(autouse=True)
def _m1_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data_dir: Path):
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "0")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_shadow.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.m1
def test_m1_01_dual_call_legacy_authoritative(monkeypatch: pytest.MonkeyPatch) -> None:
    """M1-01: dual-call; authoritative=legacy; user_visible_changed=false."""
    monkeypatch.setenv("ARIA_ACM_SHADOW", "1")
    acm_bridge.reset_for_tests()

    entry = memory_manager.remember(
        "User favorite coffee is espresso",
        entry_type="preference",
        tags=["coffee"],
        namespace="profile",
    )
    assert isinstance(entry, dict)
    assert entry.get("content") or entry.get("id")
    assert acm_bridge.authoritative_route() == "legacy"
    assert acm_bridge.user_visible_uses_acm() is False

    hits = memory_manager.search_memory("espresso", limit=5)
    assert isinstance(hits, list)
    # Legacy return unchanged shape
    assert all(isinstance(h, dict) for h in hits)
    panel = memory_manager.mission_control_panel()
    assert panel.get("authoritative") == "legacy"
    shadow = panel.get("shadow") or {}
    assert shadow.get("authoritative") == "legacy"
    assert shadow.get("user_visible_changed") is False
    assert shadow.get("shadow_calls", 0) >= 1


@pytest.mark.m1
def test_m1_02_shadow_agreement_golden_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """M1-02: agreement rate ≥ 85% on N≥100 golden comparisons (closes cert Condition 1 path)."""
    monkeypatch.setenv("ARIA_ACM_SHADOW", "1")
    acm_bridge.reset_for_tests()

    n = 100
    for i in range(n):
        memory_manager.remember(
            f"Fact number {i} about item{i} marker unique{i}",
            entry_type="fact",
            tags=[f"item{i}"],
            namespace="default",
        )

    for i in range(n):
        memory_manager.search_memory(f"unique{i}", limit=3)

    obs = acm_bridge.panel_observables()
    compared = int(obs["shadow_agree"]) + int(obs["shadow_disagree"])
    assert compared >= n, f"expected ≥{n} compares, got {compared}"
    rate = obs.get("agreement_rate")
    assert rate is not None
    assert rate >= 0.85, f"agreement_rate {rate} < 0.85 (agree={obs['shadow_agree']} disagree={obs['shadow_disagree']})"


@pytest.mark.m1
def test_m1_03_shadow_latency_overhead(monkeypatch: pytest.MonkeyPatch) -> None:
    """M1-03: Shadow ACM-side p95 overhead ≤ 100ms on local encode/remember path."""
    monkeypatch.setenv("ARIA_ACM_SHADOW", "1")
    acm_bridge.reset_for_tests()

    # Warm-up
    memory_manager.remember("warm up fact alpha", entry_type="fact")
    memory_manager.search_memory("alpha", limit=3)

    for i in range(30):
        memory_manager.remember(f"latency probe {i} value{i}", entry_type="fact")
        memory_manager.search_memory(f"value{i}", limit=3)

    obs = acm_bridge.panel_observables()
    p95 = obs.get("shadow_p95_ms")
    assert p95 is not None
    assert p95 <= 100.0, f"shadow p95 {p95} ms exceeds 100ms gate"


@pytest.mark.m1
def test_m1_04_mission_control_agreement_counters(monkeypatch: pytest.MonkeyPatch) -> None:
    """M1-04: MC panel exposes shadow agree/disagree without contents."""
    monkeypatch.setenv("ARIA_ACM_SHADOW", "1")
    acm_bridge.reset_for_tests()
    memory_manager.remember("User likes hiking trails", entry_type="preference")
    memory_manager.search_memory("hiking", limit=5)
    panel = memory_manager.mission_control_panel()
    shadow = panel["shadow"]
    assert "shadow_agree" in shadow
    assert "shadow_disagree" in shadow
    assert "agreement_rate" in shadow
    # Trace additive fields
    trace = conversation_trace.build_conversation_trace(
        prompt="what about hiking?",
        intent={"router": "nlu"},
        action="recall",
        route="memory",
        handler="memory",
        latency_ms=1.0,
        route_latency_ms=1.0,
        response_length=0,
        error=None,
        conversation_id="m1-test",
    )
    mop = trace.get("memory_operation") or {}
    assert mop.get("authoritative") == "legacy"
    assert mop.get("schema") == "memory_operation.v3"
    assert "shadow_agree" in mop


@pytest.mark.m1
def test_m1_shadow_off_no_acm_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    acm_bridge.reset_for_tests()
    memory_manager.remember("quiet fact", entry_type="fact")
    memory_manager.search_memory("quiet", limit=3)
    obs = acm_bridge.panel_observables()
    assert obs["shadow_enabled"] is False
    assert obs["shadow_calls"] == 0


@pytest.mark.m1
def test_m1_sup_04_facade_calls_cognitive_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    """SUP-04: façades call CognitiveEngine; Trace shows acm_verb."""
    monkeypatch.setenv("ARIA_ACM_SHADOW", "1")
    acm_bridge.reset_for_tests()
    memory_manager.remember("engine path fact", entry_type="fact")
    memory_manager.search_memory("engine path", limit=3)
    cmp = acm_bridge.last_shadow_compare()
    assert cmp is not None
    trace = conversation_trace.build_conversation_trace(
        prompt="engine path",
        intent={},
        action="memory_search",
        route="memory",
        handler="memory",
        latency_ms=1.0,
        route_latency_ms=1.0,
        response_length=0,
        error=None,
        conversation_id="m1-sup",
    )
    assert (trace.get("memory_operation") or {}).get("acm_verb") == "remember"
