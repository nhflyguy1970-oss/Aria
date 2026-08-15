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
def test_m4_02_dualwrite_authority_disabled(tmp_path: Path) -> None:
    """M4-02: DualWrite adapter is deleted; platform never cognitive-authoritative."""
    from jarvis.modules.memory import create_memory_store
    from jarvis.platform_cutover import platform_data_authoritative

    assert platform_data_authoritative() is False
    store = create_memory_store(tmp_path / "legacy.json")
    assert not hasattr(store, "_legacy")


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
    impl = getattr(store, "_impl", store)
    before_legacy = len(getattr(impl, "_data", {}).get("entries", []))
    entry = store.add("fact", "redirected autobiographical fact zeta99")
    assert entry.get("source") == "acm"
    # Legacy JSON body must not grow cognitive writes
    after_legacy = len(getattr(impl, "_data", {}).get("entries", []))
    assert after_legacy == before_legacy
    # Authoritative list projects ACM (may grow)
    assert any(
        "zeta99" in str(e.get("content") or "").lower() or e.get("id") == entry.get("id")
        for e in store.list_entries()
    )


@pytest.mark.m4
def test_m4_tags_only_update_persists_under_primary(tmp_path: Path) -> None:
    from jarvis.modules.memory import create_memory_store

    store = create_memory_store(tmp_path / "legacy.json")
    entry = store.add("fact", "persistent autobiographical fact theta77", tags=["old"])
    assert store.update(entry["id"], tags=["new", "hierarchy"], namespace="profile")

    updated = store.get(entry["id"])
    assert updated is not None
    assert "new" in updated.get("tags", [])
    assert updated.get("namespace") == "profile"

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    restarted = create_memory_store(tmp_path / "legacy.json")
    after_restart = restarted.get(entry["id"])
    assert after_restart is not None
    assert "hierarchy" in after_restart.get("tags", [])
    assert after_restart.get("namespace") == "profile"


@pytest.mark.m4
def test_m4_memory_home_loads_acm_metrics(tmp_path: Path) -> None:
    from jarvis.memory_services import build_memory_home
    from jarvis.modules.memory import create_memory_store

    store = create_memory_store(tmp_path / "legacy.json")
    home = build_memory_home(store)
    assert home["ok"] is True
    assert home["safety"]["primary"] is True
    assert isinstance(home["safety"]["metrics"], dict)


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
