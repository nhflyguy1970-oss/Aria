"""Memory store, routing, and assistant handler tests."""


import pytest
from jarvis.modules.memory import MemoryStore
from jarvis.router import route
from jarvis.session import SessionContext


@pytest.fixture
def session():
    return SessionContext()


@pytest.fixture
def store(data_dir, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    return MemoryStore(path=data_dir / "memory.json")


def test_parse_remember_namespace_and_type():
    content, etype, ns = MemoryStore.parse_remember("remember for project phoenix the codename is Alpha")
    assert ns == "phoenix"
    assert etype == "project"


def test_parse_remember_strips_these_facts():
    content, etype, _ns = MemoryStore.parse_remember(
        "these facts:\n\nBob owns a fly shop.\nSarah owns a bakery."
    )
    assert "these facts" not in content.lower()
    assert "Bob owns a fly shop" in content


def test_split_remember_facts_multiline():
    facts = MemoryStore.split_remember_facts(
        "Bob owns a fly shop.\nSarah owns a bakery.\nMike owns a hardware store.\n"
        "Do not summarize. Just reply \"Stored.\""
    )
    assert len(facts) == 3
    assert facts[0].startswith("Bob")


def test_remember_multiline_facts(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0, 0.0] if t else [])
    monkeypatch.setattr(assistant.memory, "similar_exists", lambda _c, **_kw: False)
    msg = (
        "Remember these facts:\n\n"
        "Bob owns a fly shop.\n"
        "Sarah owns a bakery.\n"
        "Mike owns a hardware store."
    )
    result = assistant.process(msg)
    assert result["ok"] is True
    assert result.get("remembered_count", 1) >= 3
    contents = [e["content"] for e in assistant.memory.list_entries()]
    assert any("Bob owns a fly shop" in c for c in contents)
    assert any("Sarah owns a bakery" in c for c in contents)


def test_add_list_delete_id(store):
    e = store.add("fact", "I prefer dark mode", tags=["ui"], namespace="personal")
    assert e["id"]
    listed = store.list_entries()
    assert len(listed) == 1
    assert listed[0]["namespace"] == "personal"
    assert store.delete_id(e["id"])
    assert store.list_entries() == []


def test_import_merge(store):
    store.add("fact", "existing fact")
    payload = {
        "entries": [
            {"content": "existing fact", "type": "fact"},
            {"content": "imported fact", "type": "note", "namespace": "work"},
        ]
    }
    added = store.import_data(payload, merge=True)
    assert added == 1
    assert len(store.list_entries()) == 2


def test_prune_auto(store, monkeypatch):
    monkeypatch.setattr("jarvis.modules.memory._utc_now", lambda: "2020-01-01T00:00:00+00:00")
    store.add("auto", "old auto fact", tags=["auto-extracted"])
    store._data["entries"][0]["timestamp"] = "2020-01-01T00:00:00+00:00"
    store._data["entries"][0]["access_count"] = 0
    store.add("fact", "keep me")
    removed = store.prune(max_age_days=30, min_score=0.99)
    assert removed == 1
    assert len(store.list_entries()) == 1


def test_memory_search_route(session):
    intent = route("search my memory for vim", session)
    assert intent["action"] == "memory_search"


def test_memory_forget_route(session):
    intent = route("forget about vim keybindings", session)
    assert intent["action"] == "memory_forget"


def test_memory_summarize_route(session):
    intent = route("summarize this conversation to memory", session)
    assert intent["action"] == "memory_summarize"


def test_checkpoint_upsert(store):
    store.upsert_checkpoint("First state", namespace="jarvis")
    store.upsert_checkpoint("Second state", namespace="jarvis")
    listed = store.list_entries(namespace="jarvis", include_embedding=True)
    checkpoints = [e for e in listed if "checkpoint" in (e.get("tags") or [])]
    assert len(checkpoints) == 1
    assert "Second" in checkpoints[0]["content"]
    pub = store.latest_checkpoint("jarvis")
    assert pub and "Second" in pub["content"]


def test_project_resume_route(session):
    intent = route("where did I leave off?", session)
    assert intent["action"] == "project_resume"


def test_memory_about_user_route(session):
    intent = route("tell me something I like to do", session)
    assert intent["action"] == "memory_about_user"


def test_memory_about_user_handler(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0])
    assistant.memory.add(
        "fact",
        "User often works on: hiking, fly fishing, reading.",
        tags=["profile", "onboarding", "interests"],
        namespace="profile",
    )
    assistant.memory.add(
        "fact",
        "User's name is Alex.",
        tags=["profile", "onboarding", "name"],
        namespace="profile",
    )
    result = assistant.process("tell me something I like to do")
    assert result["ok"] is True
    assert any(w in result["message"].lower() for w in ("hiking", "fly fishing", "reading"))


def test_remember_handler(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0])
    result = assistant.process("Remember that I use Neovim")
    assert result["ok"] is True
    assert result["module"] == "memory"
    assert assistant.memory.list_entries()


def test_profile_questionnaire_once(data_dir, monkeypatch):
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
    from jarvis.profile_questionnaire import is_completed, save_answers

    store = MemoryStore(path=data_dir / "mem.json")
    assert not is_completed()
    stored = save_answers(store, {
        "name": "Alex",
        "communication": "brief",
        "primary_use": "coding",
    })
    assert len(stored) >= 2
    assert is_completed()
    profile = store.list_entries(namespace="profile")
    assert any("Alex" in p["content"] for p in profile)


def test_memory_search_handler(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.llm.embed_text", lambda t: [1.0])
    monkeypatch.setattr("jarvis.llm.embed_available", lambda: False)
    assistant.memory.add("preference", "I like tabs not spaces", namespace="default")
    result = assistant.process("search my memory for tabs")
    assert result["ok"] is True
    assert "tabs" in result["message"].lower()
