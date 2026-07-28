"""Chat config / Memory authority — Chat never auto-encodes autobiography."""

from __future__ import annotations

from pathlib import Path


def test_chat_os_does_not_auto_write_memory():
    os_js = Path("jarvis/gui/static/chat_os.js").read_text(encoding="utf-8")
    assert "Stage Memory" in os_js or "Stage this as a Memory candidate" in os_js
    assert "encode" not in os_js.lower() or "do not encode" in os_js.lower()


def test_chat_os_stages_connections_review():
    os_js = Path("jarvis/gui/static/chat_os.js").read_text(encoding="utf-8")
    assert "Connections review" in os_js or "connections" in os_js.lower()


def test_paste_drop_supports_composer(tmp_path=None):
    src = Path("jarvis/gui/static/vision_drop.js").read_text(encoding="utf-8")
    assert "messageInput" in src
    assert "Drop to attach" in src or "isAttachable" in src
    assert "paste" in src.lower()
