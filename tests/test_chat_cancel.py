"""Chat cancel / stream recovery behaviors (conversation helpers)."""

from __future__ import annotations


def test_conversation_truncate_on_cancel():
    from jarvis.conversation import Conversation

    c = Conversation("You are Aria.")
    c.add_user("long task")
    c.add_assistant("partial stream " * 40)
    assert c.truncate_last_assistant() is True
    last = c.messages[-1]["content"]
    assert "interrupted" in last.lower()
    assert len(last) < len("partial stream " * 40)
    assert c.messages[-1]["role"] == "assistant"
    assert c.truncate_last_assistant() is True  # still last assistant


def test_conversation_truncate_noop_without_assistant():
    from jarvis.conversation import Conversation

    c = Conversation("sys")
    c.add_user("hello")
    assert c.truncate_last_assistant() is False


def test_conversation_add_roles():
    from jarvis.conversation import Conversation

    c = Conversation("sys")
    c.add_user("hello")
    c.add_assistant("hi")
    assert len(c.messages) >= 3  # system + user + assistant
    roles = [m["role"] for m in c.messages]
    assert "user" in roles and "assistant" in roles
