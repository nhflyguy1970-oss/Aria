"""Memory polish: namespace, system prompt, conflicts, auto-memory, checkpoint."""

import pytest
from jarvis.config import (
    build_system_prompt,
    load_auto_memory_mode,
    save_auto_memory_mode,
)
from jarvis.memory_context import (
    build_quick_checkpoint,
    detect_project_namespace,
    filter_extracted_facts,
    find_conflicts,
    should_extract_auto_memory,
    system_prompt_block,
)
from jarvis.modules.memory import MemoryStore
from jarvis.session import SessionContext


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    return MemoryStore(path=data_dir / "memory.json")


@pytest.fixture
def session():
    return SessionContext()


def test_detect_project_namespace():
    ns = detect_project_namespace()
    assert ns
    assert " " not in ns


def test_system_prompt_block_includes_profile(store):
    store.add(
        "fact",
        "User's name is Jeff.",
        tags=["profile", "summary"],
        namespace="profile",
    )
    block = system_prompt_block(store)
    assert "Jeff" in block


def test_build_system_prompt_with_memory(store, monkeypatch):
    monkeypatch.setattr("jarvis.config.load_memory_in_system_prompt", lambda: True)
    store.add("fact", "User's name is Jeff.", namespace="profile", tags=["profile", "summary"])
    prompt = build_system_prompt("default", store)
    assert "Jeff" in prompt


def test_should_extract_auto_memory_modes():
    assert should_extract_auto_memory("remember I use vim", "ok", "explicit")
    assert not should_extract_auto_memory("what is python?", "Python is...", "smart")
    assert should_extract_auto_memory("I prefer dark mode", "Sure", "smart")
    assert not should_extract_auto_memory("hello", "hi", "off")


def test_filter_extracted_facts():
    facts = filter_extracted_facts(
        ["User asked about Python", "User prefers Neovim for editing"],
        "I prefer Neovim",
    )
    assert facts == ["User prefers Neovim for editing"]


def test_find_conflicts_duplicate(store, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0])
    a = store.add("preference", "User prefers dark mode")
    b = store.add("preference", "User prefers dark mode")
    conflicts = find_conflicts(store)
    pair_ids = {conflicts[0]["a"]["id"], conflicts[0]["b"]["id"]}
    assert pair_ids == {a["id"], b["id"]}


def test_build_quick_checkpoint(session):
    session.last_file = "foo.py"
    session.last_module = "coding"
    text = build_quick_checkpoint(session, [{"role": "user", "content": "fix the bug"}])
    assert text and "foo.py" in text


def test_auto_memory_mode_setting(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.config.CHAT_SETTINGS_FILE", data_dir / "chat_settings.json")
    save_auto_memory_mode("explicit")
    assert load_auto_memory_mode() == "explicit"


def test_profile_reset(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.config.CHAT_SETTINGS_FILE", data_dir / "chat_settings.json")
    import jarvis.config as jarvis_config
    monkeypatch.setattr(
        "jarvis.profile_questionnaire._load_chat_settings", jarvis_config._load_chat_settings,
    )
    monkeypatch.setattr(
        "jarvis.profile_questionnaire._write_chat_settings", jarvis_config._write_chat_settings,
    )
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0])
    from jarvis.modules.memory import MemoryStore
    from jarvis.profile_questionnaire import is_completed, reset_profile, save_answers

    store = MemoryStore(path=data_dir / "mem.json")
    save_answers(store, {"name": "Alex", "communication": "brief", "primary_use": "coding"})
    assert is_completed()
    reset_profile(store)
    assert not is_completed()
    assert store.list_entries(namespace="profile") == []


def test_auto_checkpoint_skips_when_disabled(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.config.load_auto_checkpoint", lambda: False)
    result = assistant.auto_checkpoint()
    assert result.get("skipped") is True
