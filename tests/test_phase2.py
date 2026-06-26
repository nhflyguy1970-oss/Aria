"""Phase 2 — presence & abilities tests."""

import pytest


def test_jarvis_mcp_briefing(monkeypatch, assistant):
    from jarvis.assistant_instance import clear_assistant, set_assistant
    from jarvis.jarvis_mcp import handle_jarvis_mcp_tool

    clear_assistant()
    set_assistant(assistant)
    monkeypatch.setattr(
        assistant,
        "_morning_briefing",
        lambda params, msg: {"ok": True, "message": "Good morning", "module": "briefing"},
    )
    out = handle_jarvis_mcp_tool("jarvis_briefing", {})
    assert out["ok"] is True
    assert "Good morning" in out["message"]


def test_jarvis_mcp_unknown_tool():
    from jarvis.jarvis_mcp import handle_jarvis_mcp_tool

    out = handle_jarvis_mcp_tool("jarvis_not_real", {})
    assert out["ok"] is False


def test_storyboard_no_images():
    from jarvis.video_ops import storyboard_ken_burns

    assert storyboard_ken_burns([]).startswith("ERROR:")


def test_storyboard_single_image(monkeypatch, tmp_path):
    from jarvis import video_ops

    img = tmp_path / "a.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")
    monkeypatch.setattr(
        video_ops,
        "image_to_motion_video",
        lambda src, **kw: str(tmp_path / "clip.mp4"),
    )
    (tmp_path / "clip.mp4").write_bytes(b"fake")

    out = video_ops.storyboard_ken_burns([str(img)])
    assert out.endswith("clip.mp4")


def test_proactive_scheduler_start_stop(monkeypatch):
    monkeypatch.setenv("JARVIS_SCHEDULER", "1")
    from jarvis.proactive_scheduler import start, stop

    start()
    stop()


def test_proactive_scheduler_disabled(monkeypatch):
    monkeypatch.setenv("JARVIS_SCHEDULER", "0")
    from jarvis import proactive_scheduler as sched

    sched._thread = None
    sched.start()
    assert sched._thread is None


def test_api_video_storyboard_bad_paths(chat_app):
    res = chat_app.post("/api/video/storyboard", data={"paths": "/no/such/file.png"})
    assert res.status_code == 400
    assert res.json()["ok"] is False


def test_api_ha_scene_route(chat_app, monkeypatch):
    monkeypatch.setattr(
        "jarvis.home_assistant.activate_scene",
        lambda scene: True,
    )
    monkeypatch.setattr("jarvis.home_assistant.ha_enabled", lambda: True)
    res = chat_app.post("/api/homeassistant/scene", json={"entity_id": "scene.movie"})
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_cursor_bridge_domain_mcp_tools():
    from jarvis.cursor_bridge import _DOMAIN_MCP_TOOLS

    assert "jarvis_briefing" in _DOMAIN_MCP_TOOLS
    assert "jarvis_chat" in _DOMAIN_MCP_TOOLS
    assert len(_DOMAIN_MCP_TOOLS) >= 8
