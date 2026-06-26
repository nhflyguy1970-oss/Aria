"""Learn-about knowledge pipeline tests."""

from pathlib import Path

import pytest

from jarvis.knowledge import (
    KNOWLEDGE_DIR,
    context_for_query,
    extract_key_points,
    is_learn_command,
    learn_topic,
    load_brief,
    parse_learn_topic,
    remember_key_points,
    save_brief,
    slugify,
)


def test_is_learn_command():
    assert is_learn_command("learn about: edge TPUs")
    assert is_learn_command("learn about Movidius VPU")
    assert not is_learn_command("what is python")


def test_parse_learn_topic():
    assert parse_learn_topic("learn about: ROCm on AMD") == "ROCm on AMD"
    assert "movidius" in parse_learn_topic("go learn about movidius vpu").lower()


def test_slugify():
    assert slugify("Movidius VPU!") == "movidius-vpu"


def test_save_and_load_brief(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.knowledge.KNOWLEDGE_DIR", data_dir / "knowledge")
    body = "# Edge AI\n\n## Key points\n- Low power\n- On-device inference\n"
    saved = save_brief("Edge AI", body, [{"title": "T", "url": "http://x", "snippet": "s"}])
    brief = load_brief(saved["slug"])
    assert brief is not None
    assert brief["topic"] == "Edge AI"
    assert "Low power" in brief["key_points"][0]


def test_extract_key_points():
    text = "## Key points\n- One\n- Two\n\n## Details\nMore"
    assert extract_key_points(text) == ["One", "Two"]


def test_learn_topic_mocked(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.knowledge.KNOWLEDGE_DIR", data_dir / "knowledge")
    monkeypatch.setattr(
        "jarvis.knowledge.collect_search_results",
        lambda topic: [{"title": "A", "url": "http://a", "snippet": "fact a"}],
    )
    monkeypatch.setattr(
        "jarvis.knowledge.build_brief",
        lambda topic, results: f"# {topic}\n\n## Key points\n- Fact one\n",
    )
    result = learn_topic("Test Topic")
    assert result["ok"] is True
    assert result["slug"] == "test-topic"
    assert (data_dir / "knowledge" / "test-topic.md").is_file()


def test_context_for_query(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.knowledge.KNOWLEDGE_DIR", data_dir / "knowledge")
    save_brief(
        "Movidius VPU",
        "# Movidius VPU\n\n## Overview\nIntel vision processing unit for cameras.\n",
        [],
    )
    ctx, _ = context_for_query("tell me about movidius vpu chips")
    assert "Movidius VPU" in ctx
    assert "vision processing" in ctx.lower()


def test_remember_key_points(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.knowledge.KNOWLEDGE_DIR", data_dir / "knowledge")
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(path=data_dir / "memory.json")
    save_brief(
        "Edge AI",
        "## Key points\n- Runs on device\n- Saves bandwidth\n",
        [],
    )
    stored = remember_key_points(store, "Edge AI", slug="edge-ai")
    assert len(stored) == 2
    entries = store.list_entries()
    assert any("knowledge" in (e.get("tags") or []) for e in entries)


def test_router_learn_about():
    from jarvis.router import route
    from jarvis.session import SessionContext

    intent = route("learn about: home battery backup", SessionContext())
    assert intent["action"] == "learn_about"
    assert "battery" in intent["params"]["topic"].lower()
