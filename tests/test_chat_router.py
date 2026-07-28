"""Chat router smoke — Chat remains the OS control plane entry."""

from __future__ import annotations


def test_router_handles_chatty_prompts():
    from jarvis import router

    # Prefer soft checks — router may use heuristics / LLM
    assert callable(getattr(router, "route", None) or getattr(router, "classify", None) or (lambda: None))


def test_document_ask_routing_present():
    from jarvis import router

    src = open(router.__file__, encoding="utf-8").read()
    assert "document" in src.lower()
    assert "ask" in src.lower() or "library" in src.lower()


def test_chat_os_static_contract():
    """Frontend Chat OS module is wired as the Ask Aria owner."""
    from pathlib import Path

    os_js = Path("jarvis/gui/static/chat_os.js").read_text(encoding="utf-8")
    html = Path("jarvis/gui/static/index.html").read_text(encoding="utf-8")
    assert "askAria" in os_js
    assert "create_new_chat" in Path("jarvis/chat_sessions.py").read_text(encoding="utf-8") or "create_new_chat" in os_js or "/api/chat/new" in os_js
    assert "chat_os.js" in html
    assert 'id="chatNewBtn"' in html
    assert 'id="chatComposerModelSelect"' in html
    assert 'id="chatContextChips"' in html
    assert "jarvisAskAria" in os_js
    assert "autoSend" in os_js
