"""Retired memory adapter regression tests."""

from __future__ import annotations

from pathlib import Path


def test_memory_adapter_store_deleted() -> None:
    root = Path(__file__).resolve().parents[1]
    assert not (root / "jarvis" / "modules" / "memory_adapter_store.py").exists()


def test_create_memory_store_returns_backend_directly(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "0")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "1")

    from aria_core import acm_bridge, memory_manager
    from jarvis.modules.memory import JsonMemoryStore, create_memory_store

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    try:
        store = create_memory_store(tmp_path / "memory.json")
        assert isinstance(store, JsonMemoryStore)
        assert not hasattr(store, "_legacy")
    finally:
        acm_bridge.reset_for_tests()
        memory_manager.reset_for_tests()
