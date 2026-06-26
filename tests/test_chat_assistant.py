"""JarvisAssistant chat handlers (mocked LLM)."""

from __future__ import annotations

from jarvis.assistant import display_chat_user_content


def test_display_chat_user_content_strips_injection():
    raw = "Relevant memories:\n- foo\n\nUser: real question"
    assert display_chat_user_content(raw) == "real question"
    assert display_chat_user_content("plain") == "plain"


def test_messages_for_llm_augments_last_user_only(assistant):
    assistant.conversation.messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "ok"},
    ]
    pending = assistant.conversation.messages + [{"role": "user", "content": "new"}]
    out = assistant._messages_for_llm(pending, "CTX")
    assert out[-1]["content"] == "CTX\n\nUser: new"
    assert out[1]["content"] == "old"


def test_prepare_chat_user_message_includes_file(assistant, data_dir, monkeypatch):
    path = data_dir / "note.txt"
    path.write_text("hello file", encoding="utf-8")
    msg = assistant._prepare_chat_user_message("explain", {"file_path": str(path)})
    assert "hello file" in msg
    assert "note.txt" in msg


def test_chat_stores_raw_user_not_context_prefix(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.llm.ask", lambda *a, **k: "Sure thing.")
    monkeypatch.setattr(
        assistant,
        "_chat_context_prefix",
        lambda m: ("Relevant memories:\n- secret\n\n", ["warn"], []),
    )
    result = assistant.process("hello there")
    assert result["ok"] is True
    user_msgs = [m for m in assistant.conversation.messages if m["role"] == "user"]
    assert user_msgs[-1]["content"] == "hello there"
    assert "Relevant memories" not in user_msgs[-1]["content"]


def test_chat_rolls_back_user_on_llm_error(assistant, monkeypatch):
    calls = {"n": 0}

    def ask_side(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            return '{"action": "chat", "params": {}}'
        raise RuntimeError("ollama down")

    monkeypatch.setattr("jarvis.llm.route_with_tools", lambda *a, **k: None)
    monkeypatch.setattr("jarvis.llm.ask", ask_side)

    def fail_usage(*a, **k):
        raise RuntimeError("ollama down")

    monkeypatch.setattr("jarvis.llm.ask_with_usage", fail_usage)
    before = len(assistant.conversation.messages)
    result = assistant.process("unique chat message xyz")
    assert result["ok"] is False
    assert len(assistant.conversation.messages) == before


def test_stream_defers_user_until_first_token(assistant, monkeypatch):
    def stream(*a, **k):
        yield "Hel"
        yield "lo"

    monkeypatch.setattr("jarvis.llm.ask_stream", lambda *a, **k: stream())
    monkeypatch.setattr(assistant, "_chat_context_prefix", lambda m: ("", [], []))
    events = list(assistant.process_stream("stream me"))
    assert events[-1]["ok"] is True
    user_msgs = [m for m in assistant.conversation.messages if m["role"] == "user"]
    assert user_msgs[-1]["content"] == "stream me"


def test_stream_empty_does_not_persist_user(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.llm.ask_stream", lambda *a, **k: iter([]))
    monkeypatch.setattr(assistant, "_chat_context_prefix", lambda m: ("", [], []))
    before = len(assistant.conversation.messages)
    events = list(assistant.process_stream("nothing"))
    assert events[-1]["ok"] is False
    assert len(assistant.conversation.messages) == before


def test_switch_branch_loads_session(assistant, monkeypatch):
    assistant.session.note_file("branch-a.py")
    assistant.branches.save_session(assistant.branches.active_id, assistant.session)
    bid = assistant.create_branch("other")
    assistant.session.note_file("branch-b.py")
    assistant.branches.save_session(bid, assistant.session)
    assert assistant.switch_branch("main")
    assert assistant.session.last_file == "branch-a.py"
    assert assistant.switch_branch(bid)
    assert assistant.session.last_file == "branch-b.py"


def test_remember_single_memory_store(assistant):
    assistant.process("Remember my favorite color is blue")
    facts = assistant.memory.list_entries("fact")
    assert any("blue" in e["content"].lower() for e in facts)
    assert assistant.general.mem is assistant.memory


def test_auto_remember_deduplicates(assistant, monkeypatch):
    assistant.memory.add("auto", "User prefers tabs over spaces", tags=["auto-extracted"])
    monkeypatch.setattr("jarvis.llm.extract_memories", lambda text: ["User prefers tabs over spaces"])
    assistant._auto_remember("hi", "bye")
    auto = assistant.memory.list_entries("auto")
    assert sum(1 for e in auto if "tabs" in e["content"].lower()) == 1


def test_web_search_stream_yields_tokens(assistant, monkeypatch):
    monkeypatch.setattr(
        assistant,
        "_web_search",
        lambda p, m: {"ok": True, "message": "Result one two three", "module": "general"},
    )
    events = list(assistant.process_stream("search the web for cats"))
    types = [e["type"] for e in events]
    assert "status" in types
    assert "token" in types
    assert events[-1]["type"] == "done"
    assert events[-1]["ok"] is True


def test_clear_resets_branch_conversation(assistant, monkeypatch):
    monkeypatch.setattr("jarvis.llm.route_with_tools", lambda *a, **k: None)

    def smart_ask(model, msgs, **k):
        return '{"action": "chat", "params": {}}'

    monkeypatch.setattr("jarvis.llm.ask", lambda *a, **k: "assistant reply")
    assistant.process("unique otter facts please")
    assistant.process("clear")
    roles = [m["role"] for m in assistant.conversation.messages]
    assert "user" not in roles
