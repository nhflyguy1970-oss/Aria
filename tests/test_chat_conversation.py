"""Unit tests for Conversation message list behavior."""

from jarvis.conversation import Conversation


def test_add_and_clear_keeps_system():
    conv = Conversation("You are Jarvis.")
    conv.add_user("hello")
    conv.add_assistant("hi")
    assert len(conv.messages) == 3
    conv.clear()
    assert conv.messages == [{"role": "system", "content": "You are Jarvis."}]


def test_pop_last_user():
    conv = Conversation("sys")
    conv.add_user("one")
    conv.add_assistant("two")
    conv.add_user("three")
    assert conv.pop_last_user()
    assert conv.messages[-1]["role"] == "assistant"
    assert conv.pop_last_user() is False


def test_set_system_content_updates_existing():
    conv = Conversation("old prompt")
    conv.set_system_content("new prompt")
    assert conv.messages[0]["content"] == "new prompt"


def test_set_system_content_inserts_when_missing():
    conv = Conversation()
    conv.messages = [{"role": "user", "content": "hi"}]
    conv.set_system_content("sys")
    assert conv.messages[0]["role"] == "system"
    assert conv.messages[0]["content"] == "sys"
