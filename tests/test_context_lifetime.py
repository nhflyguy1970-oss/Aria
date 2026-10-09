"""Policy A — active implicit artifact context expires on unrelated turns.

Implicit deictics ("What is this?", "What does it say?") bind only while
last_module is vision/document. Successful chat / runtime_* / web_search
deactivate that active context via decorate_result, but last_image and
last_document_path stay for explicit / path-only references.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.conversation_pipeline import decorate_result
from jarvis.handlers import ensure_handlers_loaded
from jarvis.router import _follow_up_route, route
from jarvis.session import SessionContext

ensure_handlers_loaded()


class _Branches:
    def persist(self, *args, **kwargs):
        return None


class _Memory:
    def similar_exists(self, content: str) -> bool:
        return False

    def add(self, *args, **kwargs):
        return None


class _Assistant:
    def __init__(self, session: SessionContext):
        self.session = session
        self.branches = _Branches()
        self.memory = _Memory()

    def sync_project_namespace(self):
        return None


def _decorate(session: SessionContext, action: str, *, ok: bool = True, module=None) -> SessionContext:
    assistant = _Assistant(session)
    result: dict = {"ok": ok, "message": "ok"}
    if module is not None:
        result["module"] = module
    with patch("jarvis.trust_memory.record_tool_outcome", return_value=None):
        decorate_result(
            assistant,
            result,
            intent={"action": action, "thinking": "test"},
            action=action,
            params={},
            message="test",
        )
    return session


def vision_active(path: str = "/tmp/imgA.png") -> SessionContext:
    s = SessionContext()
    s.last_image = path
    s.last_module = "vision"
    return s


def document_active(path: str = "/tmp/docA.pdf") -> SessionContext:
    s = SessionContext()
    s.last_document_path = path
    s.last_module = "document"
    return s


def _route(message: str, session: SessionContext) -> dict:
    with patch("jarvis.runtime_introspection.get_runtime_client", return_value=MagicMock()):
        return route(message, session, None)


def _action(message: str, session: SessionContext) -> str | None:
    return _route(message, session).get("action")


def _follow(message: str, session: SessionContext) -> str | None:
    return (_follow_up_route(message, session) or {}).get("action")


# --- vision lifetime -------------------------------------------------------


def test_immediate_what_is_this_uses_active_image() -> None:
    s = vision_active()
    intent = _route("What is this?", s)
    assert intent.get("action") == "analyze_image"
    assert intent.get("params", {}).get("path") == "/tmp/imgA.png"


def test_immediate_visual_deictic_uses_active_image() -> None:
    assert _action("What color is this?", vision_active()) == "analyze_image"


def test_unrelated_chat_deactivates_implicit_vision() -> None:
    s = vision_active()
    _decorate(s, "chat", ok=True, module=None)
    assert s.last_image == "/tmp/imgA.png"
    assert s.last_module != "vision"
    assert _action("What is this?", s) != "analyze_image"


def test_runtime_gpu_deactivates_implicit_vision() -> None:
    s = vision_active()
    _decorate(s, "runtime_gpu", ok=True, module=None)
    assert s.last_image == "/tmp/imgA.png"
    assert s.last_module != "vision"
    assert _action("What is this?", s) != "analyze_image"


def test_web_search_deactivates_implicit_vision() -> None:
    s = vision_active()
    _decorate(s, "web_search", ok=True, module="general")
    assert s.last_image == "/tmp/imgA.png"
    assert s.last_module == "general"
    assert _action("What is this?", s) != "analyze_image"


def test_several_unrelated_chats_keep_vision_inactive() -> None:
    s = vision_active()
    for _ in range(4):
        _decorate(s, "chat", ok=True, module=None)
    assert s.last_image == "/tmp/imgA.png"
    assert _action("What is this?", s) != "analyze_image"


def test_explicit_describe_image_survives_deactivation() -> None:
    s = vision_active()
    _decorate(s, "chat", ok=True, module=None)
    assert _follow("Describe the image.", s) == "describe_image"
    assert _follow("Describe this image.", s) == "describe_image"
    assert _follow("What does the image show?", s) == "analyze_image"


def test_newer_image_becomes_active_implicit_context() -> None:
    s = vision_active("/tmp/imgA.png")
    s.note_image("/tmp/imgB.png")
    s.note_module("vision")
    intent = _route("What is this?", s)
    assert intent.get("action") == "analyze_image"
    assert intent.get("params", {}).get("path") == "/tmp/imgB.png"


# --- document lifetime -----------------------------------------------------


def test_immediate_document_deictic_uses_active_document() -> None:
    s = document_active()
    intent = _route("What does it say?", s)
    assert intent.get("action") == "document_query"
    assert intent.get("params", {}).get("path") == "/tmp/docA.pdf"


def test_unrelated_chat_deactivates_implicit_document() -> None:
    s = document_active()
    _decorate(s, "chat", ok=True, module=None)
    assert s.last_document_path == "/tmp/docA.pdf"
    assert s.last_module != "document"
    assert _action("What does it say?", s) != "document_query"


def test_runtime_gpu_deactivates_implicit_document() -> None:
    s = document_active()
    _decorate(s, "runtime_gpu", ok=True, module=None)
    assert s.last_document_path == "/tmp/docA.pdf"
    assert _action("What does it say?", s) != "document_query"


def test_web_search_deactivates_implicit_document() -> None:
    s = document_active()
    _decorate(s, "web_search", ok=True, module="general")
    assert _action("What does it say?", s) != "document_query"


def test_explicit_document_refs_survive_deactivation() -> None:
    s = document_active()
    _decorate(s, "chat", ok=True, module=None)
    assert _follow("What does the document say?", s) == "document_query"
    assert _follow("What does the PDF say?", s) == "document_query"
    assert _follow("Summarize the document.", s) == "document_summarize"
    assert _follow("What does the contract say?", s) == "document_query"


def test_newer_document_becomes_active_implicit_context() -> None:
    s = document_active("/tmp/docA.pdf")
    s.note_document("/tmp/docB.pdf")
    s.note_module("document")
    intent = _route("What does it say?", s)
    assert intent.get("action") == "document_query"
    assert intent.get("params", {}).get("path") == "/tmp/docB.pdf"


# --- mixed precedence ------------------------------------------------------


def test_image_then_document_this_say_uses_document() -> None:
    s = vision_active("/tmp/imgA.png")
    s.note_document("/tmp/docB.pdf")
    s.note_module("document")
    intent = _route("What does this say?", s)
    assert intent.get("action") == "document_query"
    assert intent.get("params", {}).get("path") == "/tmp/docB.pdf"


def test_document_then_image_what_is_this_uses_vision() -> None:
    s = document_active("/tmp/docA.pdf")
    s.note_image("/tmp/imgB.png")
    s.note_module("vision")
    intent = _route("What is this?", s)
    assert intent.get("action") == "analyze_image"
    assert intent.get("params", {}).get("path") == "/tmp/imgB.png"


def test_image_then_document_what_is_this_not_stale_vision() -> None:
    """Document becomes active; implicit vision deictic must not fire."""
    s = vision_active("/tmp/imgA.png")
    s.note_document("/tmp/docB.pdf")
    s.note_module("document")
    assert _action("What is this?", s) != "analyze_image"


# --- clear() hygiene -------------------------------------------------------


def test_clear_drops_vision_active_context() -> None:
    s = vision_active()
    s.clear()
    assert s.last_image == ""
    assert s.last_module == "general"
    assert s.last_module not in ("vision", "document")
    assert _action("What is this?", s) != "analyze_image"


def test_clear_drops_document_active_context() -> None:
    s = document_active()
    s.clear()
    assert s.last_document_path == ""
    assert s.last_module == "general"
    assert _action("What does it say?", s) != "document_query"


# --- module transitions preserve paths -------------------------------------


@pytest.mark.parametrize(
    "action,module",
    [("chat", None), ("runtime_gpu", None), ("web_search", "general")],
)
def test_unrelated_success_retains_image_path_but_ends_active_vision(
    action: str, module
) -> None:
    s = vision_active()
    _decorate(s, action, ok=True, module=module)
    assert s.last_image == "/tmp/imgA.png"
    assert s.last_module not in ("vision", "document")
    assert _follow("What is this?", s) is None


@pytest.mark.parametrize(
    "action,module",
    [("chat", None), ("runtime_gpu", None), ("web_search", "general")],
)
def test_unrelated_success_retains_document_path_but_ends_active_document(
    action: str, module
) -> None:
    s = document_active()
    _decorate(s, action, ok=True, module=module)
    assert s.last_document_path == "/tmp/docA.pdf"
    assert s.last_module not in ("vision", "document")
    assert _follow("What does it say?", s) is None


def test_failed_chat_does_not_deactivate_vision() -> None:
    s = vision_active()
    _decorate(s, "chat", ok=False, module=None)
    assert s.last_module == "vision"
    assert _action("What is this?", s) == "analyze_image"


def test_chat_does_not_rewrite_briefing_module() -> None:
    """Policy A must not steal briefing follow-up state when chat omits module."""
    s = SessionContext()
    s.last_module = "briefing"
    _decorate(s, "chat", ok=True, module=None)
    assert s.last_module == "briefing"
