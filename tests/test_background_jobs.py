"""Background job dispatch (learn_about, document_summarize)."""

from types import SimpleNamespace
from unittest.mock import MagicMock


class _FakeAssistant:
    def __init__(self):
        self.learn_calls = []

    def _learn_about(self, params, message):
        self.learn_calls.append((dict(params), message))
        return {"ok": True, "type": "knowledge_learned", "message": "Learned"}


def test_submit_action_learn_about_uses_assistant_handler(monkeypatch):
    from jarvis import background_jobs

    monkeypatch.setattr(
        "jarvis.handlers.registry.get_spec",
        lambda action: SimpleNamespace(handler=None) if action == "learn_about" else None,
    )

    def fake_submit(label, fn):
        assert label == "Learn topic"
        return fn()

    monkeypatch.setattr("jarvis.coding_jobs.submit", fake_submit)
    assistant = _FakeAssistant()
    result = background_jobs._submit_action_impl(
        assistant, "learn_about", {"topic": "rust"}, "learn about rust"
    )
    assert result == {"ok": True, "type": "knowledge_learned", "message": "Learned"}
    assert assistant.learn_calls[0][0]["topic"] == "rust"


def test_submit_action_uses_registry_handler_when_present(monkeypatch):
    from jarvis import background_jobs

    calls = []

    def registry_handler(assistant, params, message):
        calls.append((params, message))
        return {"ok": True, "message": "from registry"}

    monkeypatch.setattr(
        "jarvis.handlers.registry.get_spec",
        lambda action: SimpleNamespace(handler=registry_handler)
        if action == "fake_bg_action"
        else None,
    )

    def fake_submit(label, fn):
        return fn()

    monkeypatch.setattr("jarvis.coding_jobs.submit", fake_submit)
    assistant = MagicMock()
    result = background_jobs._submit_action_impl(
        assistant, "fake_bg_action", {"q": "1"}, "go"
    )
    assert result == {"ok": True, "message": "from registry"}
    assert calls[0][0]["q"] == "1"
    assert "_cancel_check" in calls[0][0]
