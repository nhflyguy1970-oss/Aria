"""C6: MCP domain tools must not construct a standalone assistant."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from jarvis.assistant_instance import clear_assistant
from jarvis.jarvis_mcp import handle_jarvis_mcp_tool


@pytest.fixture(autouse=True)
def _no_shared_assistant():
    clear_assistant()
    yield
    clear_assistant()


def test_mcp_environment_no_assistant_required():
    with patch("jarvis.environment.snapshot", return_value={"profile": "test"}):
        out = handle_jarvis_mcp_tool("jarvis_environment", {})
    assert out.get("ok") is True
    assert out.get("profile") == "test"


def test_mcp_chat_proxies_http_when_no_shared_assistant():
    with patch(
        "jarvis.jarvis_mcp._http_json",
        return_value={"ok": True, "message": "pong", "action": "chat"},
    ) as http:
        out = handle_jarvis_mcp_tool("jarvis_chat", {"message": "ping"})
    assert out.get("ok") is True
    assert out.get("message") == "pong"
    http.assert_called_once()
    assert http.call_args.args[:2] == ("POST", "/api/chat")


def test_mcp_chat_refuses_standalone_construct():
    """Regression: get_assistant() must not be called for domain tools."""
    with (
        patch("jarvis.assistant_instance.get_assistant") as ga,
        patch(
            "jarvis.jarvis_mcp._http_json",
            return_value={"ok": True, "message": "via-http"},
        ),
    ):
        out = handle_jarvis_mcp_tool("jarvis_chat", {"message": "hi"})
    ga.assert_not_called()
    assert out.get("message") == "via-http"


def test_cutover_mode_never_reports_dual_write(tmp_path, monkeypatch):
    from jarvis import platform_cutover as pc

    cut = tmp_path / "cutover.json"
    cut.write_text('{"version":1,"mode":"dual_write"}', encoding="utf-8")
    monkeypatch.setattr(pc, "_CUTOVER_FILE", cut)
    state = pc._load()
    assert state["mode"] == "acm_authoritative"
    assert state["cognitive_memory"]["authority"] == "acm"
