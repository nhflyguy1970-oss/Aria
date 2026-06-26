"""Personality settings and memory store chat helpers."""

from jarvis.config import (
    build_system_prompt,
    load_personality_preset,
    save_personality_preset,
)
from jarvis.modules.memory import MemoryStore


def test_personality_persist_and_build(data_dir):
    save_personality_preset("tutor")
    assert load_personality_preset() == "tutor"
    prompt = build_system_prompt("tutor")
    assert "teacher" in prompt.lower() or "step" in prompt.lower()


def test_memory_similar_exists(data_dir, monkeypatch):
    def fake_embed(text: str):
        if not text:
            return []
        lower = text.lower()
        if "vim" in lower:
            return [1.0, 0.0]
        if "completely different" in lower:
            return [0.0, 1.0]
        return [0.5, 0.5]

    monkeypatch.setattr("jarvis.llm.embed_text", fake_embed)
    store = MemoryStore(path=data_dir / "mem.json")
    store.add("fact", "I use vim keybindings")
    assert store.similar_exists("I use vim keybindings")
    assert store.similar_exists("  i use vim keybindings  ")
    assert not store.similar_exists("completely different fact")


def test_memory_keyword_search_without_embed(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: False)
    store = MemoryStore(path=data_dir / "mem2.json")
    store.add("fact", "Project codename is Phoenix")
    hits = store.search("Phoenix")
    assert len(hits) == 1
