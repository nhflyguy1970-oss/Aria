"""Trust layer: failure/strategy memory, artifact filter, memory correction."""

import pytest
from jarvis.modules.memory import MemoryStore
from jarvis.router import route
from jarvis.session import SessionContext
from jarvis.trust_memory import (
    correct_memory,
    filter_trusted_content,
    is_test_artifact,
    parse_memory_correct,
    record_failure,
    record_strategy,
    scrub_store,
    seed_default_strategies,
    trust_context_for_chat,
)


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    return MemoryStore(path=data_dir / "memory.json")


def test_is_test_artifact():
    assert is_test_artifact("debug until tests pass for broken_calc.py")
    assert is_test_artifact("buy milk")
    assert not is_test_artifact("Mom's birthday is June 9.")


def test_filter_trusted_content_drops_checkpoint_test_task():
    cp = "Auto-saved on exit — task `debug until tests pass for data/scripts/broken_calc.py`"
    assert filter_trusted_content(cp) is None


def test_record_strategy(store):
    entry = record_strategy(store, "Never pollute live journal during tests.")
    assert entry["type"] == "strategy"
    assert store.list_entries(entry_type="strategy")


def test_record_failure(store):
    entry = record_failure(store, path="foo.py", error="AssertionError: 2 != 3", task="fix foo")
    assert entry and entry["type"] == "failure"


def test_correct_memory_replaces_birthday(store):
    store.add("fact", "Today is mom's birthday.")
    removed, entry, strategy_created = correct_memory(store, "Mom's birthday is June 9.", search_hint="")
    assert removed >= 1
    assert "June 9" in entry["content"]
    assert strategy_created is False


def test_correct_memory_creates_strategy_for_preference(store):
    removed, entry, strategy_created = correct_memory(store, "Prefer shorter answers without disclaimers.", search_hint="")
    assert entry["type"] == "preference"
    assert strategy_created is True
    assert store.list_entries(entry_type="strategy")


def test_parse_memory_correct():
    parsed = parse_memory_correct("correct that mom's birthday is June 9")
    assert parsed and parsed[1] == "mom's birthday is June 9"


def test_trust_context_includes_strategies(store):
    record_strategy(store, "Always be concise in general chat.")
    ctx = trust_context_for_chat(store, "hello")
    assert "Behavior rules" in ctx
    assert "concise" in ctx


def test_memory_correct_route():
    intent = route("correct that mom's birthday is June 9", SessionContext())
    assert intent["action"] == "memory_correct"
    assert "June 9" in intent["params"]["new_fact"]


def test_seed_default_strategies(store):
    added = seed_default_strategies(store)
    assert added >= 1
    assert len(store.list_entries(entry_type="strategy")) >= 1


def test_scrub_store_removes_artifacts(store):
    store._data["entries"].append({
        "id": "artifact1",
        "type": "fact",
        "content": "buy milk",
        "tags": [],
        "namespace": "default",
        "timestamp": "2026-06-01T00:00:00+00:00",
        "access_count": 0,
        "relevance": 1.0,
        "embedding": [1.0],
    })
    store.add("fact", "Real user preference: dark mode")
    result = scrub_store(store)
    assert result["removed"] == 1
    remaining = [e["content"] for e in store.list_entries()]
    assert "buy milk" not in remaining
    assert any("dark mode" in c for c in remaining)


def test_memory_rejects_test_artifact(store):
    import pytest as pt

    with pt.raises(ValueError, match="test-artifact"):
        store.add("fact", "buy milk")
