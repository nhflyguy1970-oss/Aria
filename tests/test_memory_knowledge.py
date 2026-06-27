"""Environment knowledge sync into memory."""

import pytest

from jarvis.memory_knowledge import (
    ENV_NAMESPACE,
    TAG_MACHINE,
    TAG_USER_PREFERENCE,
    collect_machine_facts,
    collect_preference_facts,
    environment_preferences_payload,
    load_environment_preferences,
    save_environment_preferences_to_memory,
    sync_environment_memory,
)
from jarvis.modules.memory import MemoryStore


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    return MemoryStore(path=data_dir / "memory.json")


def test_machine_facts_exclude_user_preferences():
    facts = collect_machine_facts()
    keys = {f["key"] for f in facts}
    assert "platform" in keys
    assert "pref-linux-commands" not in keys
    assert all(TAG_MACHINE in f["tags"] for f in facts)


def test_preference_facts_from_settings(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.config.CHAT_SETTINGS_FILE", data_dir / "chat_settings.json")
    import jarvis.config as jarvis_config
    import jarvis.memory_knowledge as mk

    monkeypatch.setattr(mk, "_load_chat_settings", jarvis_config._load_chat_settings)
    monkeypatch.setattr(mk, "_write_chat_settings", jarvis_config._write_chat_settings)
    monkeypatch.setattr("jarvis.memory_knowledge._load_chat_settings", jarvis_config._load_chat_settings)
    monkeypatch.setattr("jarvis.memory_knowledge._write_chat_settings", jarvis_config._write_chat_settings)

    prefs = load_environment_preferences()
    prefs["pref-privacy-local"] = "User wants everything offline and self-hosted."
    jarvis_config._write_chat_settings({"environment_preferences": prefs})

    facts = collect_preference_facts()
    assert len(facts) >= 3
    privacy = next(f for f in facts if f["key"] == "pref-privacy-local")
    assert "offline" in privacy["content"]
    assert TAG_USER_PREFERENCE in privacy["tags"]


def test_save_preferences_to_memory(store, data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.config.CHAT_SETTINGS_FILE", data_dir / "chat_settings.json")
    import jarvis.config as jarvis_config
    import jarvis.memory_knowledge as mk

    monkeypatch.setattr("jarvis.memory_knowledge._load_chat_settings", jarvis_config._load_chat_settings)
    monkeypatch.setattr("jarvis.memory_knowledge._write_chat_settings", jarvis_config._write_chat_settings)

    result = save_environment_preferences_to_memory(store, {
        "pref-linux-commands": "User prefers fish shell and ripgrep.",
        "pref-ollama-local": "User runs Ollama with qwen models only.",
        "pref-privacy-local": "No cloud APIs — local only.",
    })
    assert result["ok"] is True
    env = store.list_entries(namespace=ENV_NAMESPACE)
    linux = next(e for e in env if "pref-linux-commands" in (e.get("tags") or []))
    assert "fish" in linux["content"]
    assert "user-preference" in linux["tags"]


def test_environment_preferences_payload():
    payload = environment_preferences_payload()
    assert payload["ok"] is True
    assert len(payload["preferences"]) == 3
    assert payload["preferences"][0]["label"]


def test_sync_environment_memory_idempotent(store, monkeypatch):
    monkeypatch.setattr("jarvis.memory_knowledge._should_sync", lambda: True)
    first = sync_environment_memory(store, force=True)
    assert first["ok"] is True
    assert first["added"] >= 5
    second = sync_environment_memory(store, force=True)
    assert second["added"] == 0
    assert second.get("updated", 0) >= 0


def test_branch_memory_namespace():
    from jarvis.memory_context import branch_memory_namespace

    assert branch_memory_namespace("main") == "branch:main"
    assert branch_memory_namespace("") == "branch:main"
