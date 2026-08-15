"""C3: under PRIMARY, ACM read failures must not serve legacy vault poison."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def primary_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "cog.db"))
    from aria_core import acm_bridge, memory_manager

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    acm_bridge.reset_for_tests()
    memory_manager.reset_for_tests()


def _poison(store) -> None:
    store._data["entries"] = [
        {
            "id": "legacy-poison",
            "type": "fact",
            "content": "LEGACY_POISON_SHOULD_NOT_SURFACE",
            "tags": ["poison"],
            "namespace": "default",
            "timestamp": "2099-01-01T00:00:00+00:00",
            "access_count": 0,
            "relevance": 1.0,
        }
    ]


def test_list_entries_refuses_legacy_on_acm_error(primary_env, tmp_path, monkeypatch):
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(tmp_path / "m.json")
    _poison(store)

    def boom(*_a, **_k):
        raise RuntimeError("acm_down")

    monkeypatch.setattr("aria_core.acm_store_facade.acm_list_entries", boom)
    with pytest.raises(RuntimeError, match="ACM authoritative"):
        store.list_entries()


def test_search_refuses_legacy_on_acm_error(primary_env, tmp_path, monkeypatch):
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(tmp_path / "m.json")
    _poison(store)

    def boom(*_a, **_k):
        raise RuntimeError("acm_down")

    monkeypatch.setattr("aria_core.acm_store_facade.acm_search", boom)
    with pytest.raises(RuntimeError, match="ACM authoritative"):
        store.search("poison")


def test_get_refuses_legacy_on_acm_error(primary_env, tmp_path, monkeypatch):
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(tmp_path / "m.json")
    _poison(store)

    def boom(*_a, **_k):
        raise RuntimeError("acm_down")

    monkeypatch.setattr("aria_core.acm_store_facade.acm_get", boom)
    with pytest.raises(RuntimeError, match="ACM authoritative"):
        store.get("legacy-poison")


def test_legacy_fallback_flag_allows_vault_with_counter(primary_env, tmp_path, monkeypatch):
    monkeypatch.setenv("ARIA_ACM_LEGACY_READ_FALLBACK", "1")
    from aria_core import acm_bridge
    from jarvis.modules.memory import MemoryStore

    before = (acm_bridge.panel_observables() or {}).get("legacy_fallback_reads") or 0
    store = MemoryStore(tmp_path / "m.json")
    _poison(store)

    def boom(*_a, **_k):
        raise RuntimeError("acm_down")

    monkeypatch.setattr("aria_core.acm_store_facade.acm_list_entries", boom)
    rows = store.list_entries()
    assert any("LEGACY_POISON" in (r.get("content") or "") for r in rows)
    after = (acm_bridge.panel_observables() or {}).get("legacy_fallback_reads") or 0
    assert after >= before + 1
