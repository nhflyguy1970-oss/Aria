"""Chat stream cancellation tokens."""

from jarvis.chat_cancel import begin, cancel, finish, is_cancelled


def test_chat_cancel_lifecycle():
    rid = "test-req-1"
    begin(rid)
    assert not is_cancelled(rid)
    cancel(rid)
    assert is_cancelled(rid)
    finish(rid)
    assert not is_cancelled(rid)
