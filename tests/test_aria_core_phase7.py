"""Phase 7 — Memory owned by Aria Core; organ storage unchanged."""

from __future__ import annotations

from pathlib import Path

import pytest

from aria_core.event_bus import get_bus, recent_events
from aria_core.event_contracts import validate_contracts
from aria_core.memory import (
    commit_memory,
    forget,
    get_memory,
    memory_health,
    memory_history,
    memory_statistics,
    merge_memories,
    mission_control_panel,
    propose_memory,
    remember,
    rollback_memory,
    search_memory,
    update_memory,
)
from aria_core.memory_manager import reset_for_tests
from aria_core.ownership import OWNERSHIP


@pytest.fixture
def isolated_memory(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    path = tmp_path / "memory.json"

    def _store(*_a, **_k):
        from jarvis.modules.memory import MemoryStore

        return MemoryStore(path=path)

    monkeypatch.setattr("aria_core.memory_manager._store", _store)
    reset_for_tests()
    get_bus().reset_for_tests()
    return path


def test_memory_owned_by_core():
    assert OWNERSHIP["memory"]["source_of_truth"] == "aria_core.memory_manager"
    assert "jarvis.modules.memory" in OWNERSHIP["memory"]["implementation"]
    assert "aria_core.memory" in OWNERSHIP["memory"]["allowed_writers"]


def test_remember_search_forget_roundtrip(isolated_memory):
    entry = remember(
        "phase7 heart of aria",
        entry_type="teaching",
        tags=["phase7"],
        namespace="phase7",
    )
    assert isinstance(entry, dict)
    entry_id = entry.get("id")
    assert entry_id
    hits = search_memory("heart of aria", limit=5, namespace="phase7")
    assert any(h.get("id") == entry_id for h in hits)
    got = get_memory(entry_id)
    assert got and got.get("id") == entry_id
    assert update_memory(entry_id, content="phase7 updated") is True
    assert forget(entry_id) is True
    names = {e["name"] for e in recent_events(limit=40)}
    assert "MemoryWritten" in names
    assert "MemoryCreated" in names
    assert "MemoryCommit" in names
    assert "MemorySearch" in names
    assert "MemoryRead" in names
    assert "MemoryUpdated" in names
    assert "MemoryDeleted" in names


def test_propose_commit_and_history_no_contents(isolated_memory):
    p = propose_memory(
        "secret-content-should-not-leak",
        entry_type="teaching",
        namespace="phase7",
    )
    assert p["decision"] == "pending"
    assert "_content" in p
    commit_memory(p)
    hist = memory_history(limit=20)
    assert hist
    blob = str(hist)
    assert "secret-content-should-not-leak" not in blob
    assert all(not str(k).startswith("_") for r in hist for k in r)
    stats = memory_statistics()
    assert stats["owner"] == "aria_core.memory"
    assert stats["counters"]["writes"] >= 1
    assert memory_health().get("ok") is True


def test_merge_and_rollback(isolated_memory):
    a = remember("alpha merge keep", entry_type="teaching", namespace="phase7")
    b = remember("beta merge drop", entry_type="teaching", namespace="phase7")
    merged = merge_memories(a["id"], b["id"])
    assert merged["ok"] is True
    assert get_memory(b["id"]) is None
    names = {e["name"] for e in recent_events(limit=40)}
    assert "MemoryMerged" in names
    c = remember("rollback-me", entry_type="teaching", namespace="phase7")
    out = rollback_memory(entry_id=c["id"])
    assert out["ok"] is True
    assert "MemoryRollback" in {e["name"] for e in recent_events(limit=50)}


def test_cap_bus_remember_uses_core(isolated_memory):
    from aria_core.capability_bus import recall, remember as cap_remember

    entry = cap_remember("via cap bus", entry_type="teaching", namespace="phase7")
    assert entry and entry.get("id")
    hits = recall("via cap bus", namespace="phase7")
    assert any(h.get("id") == entry["id"] for h in hits)


def test_mission_control_panel_hides_contents(isolated_memory):
    remember("do-not-show-this-body", entry_type="teaching", namespace="phase7")
    panel = mission_control_panel(limit=20)
    assert panel["owner"] == "aria_core.memory"
    assert "statistics" in panel
    assert "history" in panel
    assert "health" in panel
    assert "do-not-show-this-body" not in str(panel)


def test_event_contracts_include_memory_lifecycle():
    assert validate_contracts() == []


def test_phase7_docs_exist():
    root = Path(__file__).resolve().parents[1] / "docs" / "aria_core"
    for name in ("PHASE7.md", "MEMORY.md"):
        assert (root / name).is_file(), name
