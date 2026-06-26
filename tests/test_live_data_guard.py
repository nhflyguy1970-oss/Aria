"""Live data guard blocks pytest writes to project data/."""

import pytest
from jarvis.config import PROJECT_ROOT
from jarvis.live_data_guard import assert_live_write_allowed, enable_test_guard
from jarvis.modules.memory import MemoryStore

LIVE_MEMORY_FILE = PROJECT_ROOT / "data" / "memory.json"


def test_guard_blocks_live_memory_path():
    enable_test_guard()
    with pytest.raises(RuntimeError, match="live Jarvis data"):
        assert_live_write_allowed(LIVE_MEMORY_FILE)


def test_guard_allows_temp_path(data_dir):
    enable_test_guard()
    assert_live_write_allowed(data_dir / "memory.json")


def test_store_writes_under_temp(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0])
    store = MemoryStore(path=data_dir / "memory.json")
    store.add("fact", "Safe fact for tests.")
