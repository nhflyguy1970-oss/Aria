"""Tests for reflection_loop module."""

from __future__ import annotations

import pytest


def test_reflection_disabled(monkeypatch):
    monkeypatch.setenv("JARVIS_REFLECTION_DAILY", "0")
    monkeypatch.setenv("JARVIS_BRAIN_MODE", "0")
    from jarvis.reflection_loop import reflection_enabled, run_reflection

    assert reflection_enabled() is False
    out = run_reflection(force=False)
    assert out.get("skipped")


def test_reflection_status(monkeypatch):
    monkeypatch.setenv("JARVIS_REFLECTION_DAILY", "1")
    monkeypatch.setenv("JARVIS_REFLECTION_HOUR", "22")
    from jarvis.reflection_loop import reflection_hour, reflection_status

    assert reflection_hour() == 22
    st = reflection_status()
    assert st["enabled"] is True
    assert st["hour"] == 22


def test_store_strategies(data_dir, monkeypatch):
    monkeypatch.delenv("JARVIS_VECTOR_BACKEND", raising=False)
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: False)
    from jarvis.modules.memory import MemoryStore
    from jarvis.reflection_loop import STRATEGIES_NAMESPACE, _store_strategies

    store = MemoryStore(path=data_dir / "memory.json")
    n = _store_strategies(store, ["Prefer pytest before merge.", "Prefer pytest before merge."])
    assert n == 1
    rows = store.list_entries(entry_type="strategy", namespace=STRATEGIES_NAMESPACE)
    assert len(rows) == 1
    assert "reflection" in (rows[0].get("tags") or [])


def test_run_reflection_no_activity(data_dir, monkeypatch, assistant):
    monkeypatch.setenv("JARVIS_REFLECTION_DAILY", "1")
    from jarvis.reflection_loop import run_reflection

    out = run_reflection(memory_store=assistant.memory, journal=assistant.journal, force=True)
    assert out.get("ok")
    assert out.get("skipped") or out.get("strategies", 0) >= 0
