from jarvis.assistant import JarvisAssistant
from jarvis.session import SessionContext


class _Branches:
    active_id = "main"

    def persist(self, *args, **kwargs):
        return None


class _AssistantDouble:
    def __init__(self):
        self.branches = _Branches()
        self.session = SessionContext()
        self.memory = object()

    def switch_branch(self, branch_id: str) -> bool:
        return True

    def _process_unlocked(self, *args, **kwargs):
        raise AssertionError("stream fallback must not route through sync process")

    def sync_project_namespace(self):
        return None

    def yield_request_lock(self):
        return None


def test_stream_non_chat_uses_dispatch_decorate_without_double_route(monkeypatch):
    import jarvis.assistant as assistant_mod
    import jarvis.conversation_pipeline as pipeline

    assistant = _AssistantDouble()
    route_calls = []
    dispatch_calls = []
    decorate_calls = []

    def fake_route(message, session, attachment):
        route_calls.append(message)
        return {"action": "capabilities", "params": {}, "thinking": "test route"}

    def fake_dispatch(obj, action, params, message, *, prefer_queue=True):
        dispatch_calls.append((obj, action, params, message, prefer_queue))
        return {"ok": True, "message": "shared dispatch", "module": "general"}

    def fake_decorate(obj, result, *, intent, action, params, message):
        decorate_calls.append((obj, intent, action, params, message))
        result["decorated"] = True
        result["action"] = action
        return result

    monkeypatch.setattr(assistant_mod, "route", fake_route)
    monkeypatch.setattr(pipeline, "apply_editor_params_if_coding", lambda *args: None)
    monkeypatch.setattr(pipeline, "dispatch_action", fake_dispatch)
    monkeypatch.setattr(pipeline, "decorate_result", fake_decorate)

    events = list(JarvisAssistant._process_stream_unlocked(assistant, "what can you do?"))

    assert route_calls == ["what can you do?"]
    assert len(dispatch_calls) == 1
    assert dispatch_calls[0][1:] == ("capabilities", {}, "what can you do?", True)
    assert len(decorate_calls) == 1
    assert events[-1]["type"] == "done"
    assert events[-1]["message"] == "shared dispatch"
    assert events[-1]["decorated"] is True
    assert events[-1]["action"] == "capabilities"


def test_stream_chat_keeps_conversation_engine_sse_shape(monkeypatch):
    import jarvis.assistant as assistant_mod
    import jarvis.behaviors.conversation as conversation_mod
    import jarvis.conversation_pipeline as pipeline

    assistant = _AssistantDouble()
    route_calls = []

    class Engine:
        def execute_stream(self, message, params, *, request_id=""):
            yield {"type": "token", "content": "hello"}
            yield {"type": "done", "ok": True, "message": "hello", "uncensored": False}

    def fake_route(message, session, attachment):
        route_calls.append(message)
        return {"action": "chat", "params": {"tone": "plain"}, "thinking": "chat"}

    def fail_dispatch(*args, **kwargs):
        raise AssertionError("chat stream should stay on ConversationEngine.execute_stream")

    monkeypatch.setattr(assistant_mod, "route", fake_route)
    monkeypatch.setattr(pipeline, "apply_editor_params_if_coding", lambda *args: None)
    monkeypatch.setattr(pipeline, "dispatch_action", fail_dispatch)
    monkeypatch.setattr(conversation_mod, "ensure_conversation_engine", lambda obj: Engine())

    events = list(
        JarvisAssistant._process_stream_unlocked(assistant, "hello", request_id="req-1")
    )

    assert route_calls == ["hello"]
    assert events[-2:] == [
        {"type": "token", "content": "hello"},
        {"type": "done", "ok": True, "message": "hello", "uncensored": False},
    ]
