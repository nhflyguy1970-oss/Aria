"""M4 — Legacy cognitive SoT retirement gates (blueprint INTEGRATION_TEST_PLAN)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aria_core import acm_bridge, capability_bus, memory_manager


@pytest.fixture(autouse=True)
def _m4_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, data_dir: Path):
    monkeypatch.delenv("ARIA_ACM_ROLLBACK", raising=False)
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_SHADOW", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "acm_m4.db"))
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "1")
    monkeypatch.delenv("JARVIS_ALLOW_DUALWRITE_LEGACY", raising=False)
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()


@pytest.mark.m4
def test_m4_01_ci_forbid_retired_sot_writers() -> None:
    """M4-01: supremacy check module enforces PRIMARY default + DualWrite off."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts" / "acm_supremacy_check.py"
    spec = importlib.util.spec_from_file_location("acm_supremacy_check", path)
    assert spec and spec.loader
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)

    assert check.check_primary_default() is True
    assert check.check_dualwrite_disabled() is True
    assert check.check_forbid_patterns() is True


@pytest.mark.m4
def test_m4_02_dualwrite_authority_disabled() -> None:
    """M4-02: DualWrite wrap is identity; platform never cognitive-authoritative."""
    from jarvis.modules.memory_adapter_store import (
        memory_adapter_enabled,
        platform_data_authoritative,
        wrap_memory_store,
    )

    assert memory_adapter_enabled() is False
    assert platform_data_authoritative() is False
    sentinel = object()
    assert wrap_memory_store(sentinel) is sentinel


@pytest.mark.m4
def test_m4_03_specialized_modules_acm_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    """M4-03: experience / relationship / trust writers encode via ACM."""
    from jarvis.experience_memory import record_experience
    from jarvis.relationship_memory import record_link
    from jarvis.trust_memory import record_strategy

    store = MagicMock()
    store.similar_exists.return_value = False
    store.list_entries.return_value = []
    store.add.side_effect = AssertionError("legacy store.add must not be used under PRIMARY")

    exp = record_experience(store, outcome="success", task="ship M4", detail="ok")
    assert isinstance(exp, dict)
    assert exp.get("source") == "acm"
    store.add.assert_not_called()

    strat = record_strategy(store, "Prefer concise answers", namespace="jarvis")
    assert isinstance(strat, dict)
    assert strat.get("source") == "acm"

    link = record_link("Jeff", "prefers", "coffee")
    assert link.get("predicate")
    assert link.get("source") == "acm" or link.get("id")


@pytest.mark.m4
def test_m4_production_acm_sole_sot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cap Bus remember → ACM; legacy write counters stay 0."""
    assert acm_bridge.acm_is_authoritative() is True
    entry = capability_bus.remember("M4 sole sot fact about tea", entry_type="fact")
    assert entry.get("source") == "acm"
    hits = capability_bus.recall(query="tea", limit=3)
    assert hits
    assert acm_bridge.panel_observables()["legacy_writes_while_primary"] == 0


@pytest.mark.m4
def test_m4_store_add_redirects_to_acm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from jarvis.modules.memory import create_memory_store

    store = create_memory_store(tmp_path / "legacy.json")
    before = len(store.list_entries()) if hasattr(store, "list_entries") else 0
    entry = store.add("fact", "redirected autobiographical fact zeta99")
    assert entry.get("source") == "acm"
    # Legacy JSON body must not grow cognitive writes
    after = len(store.list_entries())
    assert after == before


@pytest.mark.m4
def test_m4_hierarchy_consolidate_noop_under_acm(tmp_path: Path) -> None:
    from jarvis.memory.hierarchy import consolidate
    from jarvis.modules.memory import create_memory_store

    store = create_memory_store(tmp_path / "h.json")
    out = consolidate(store)
    assert out.get("authoritative") == "acm"
    assert out.get("pruned") == 0


@pytest.mark.m4
def test_m4_default_primary_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARIA_ACM_PRIMARY", raising=False)
    monkeypatch.delenv("ARIA_ACM_ROLLBACK", raising=False)
    acm_bridge.reset_for_tests()
    assert acm_bridge.primary_enabled() is True
    assert acm_bridge.acm_is_authoritative() is True
