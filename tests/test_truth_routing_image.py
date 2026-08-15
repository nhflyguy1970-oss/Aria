"""Outcome-oriented routing: generate-image patterns must beat NLU lies."""

from __future__ import annotations


def test_generate_image_pattern_beats_nlu_web_search():
    from jarvis.router import route
    from jarvis.session import SessionContext

    msg = "generate image: a solid blue circle on white background, flat test"
    intent = route(msg, SessionContext())
    assert intent.get("action") == "generate_image", intent
    assert intent.get("route_reason") == "pattern_over_nlu_image" or (
        intent.get("params") or {}
    ).get("prompt"), intent
    prompt = (intent.get("params") or {}).get("prompt") or ""
    assert "blue" in prompt.lower() or "circle" in prompt.lower()


def test_chat_format_blocks_external_fake_images():
    from pathlib import Path

    src = Path("jarvis/gui/static/chat_format.js").read_text(encoding="utf-8")
    assert "chat-fake-media" in src
    assert "gallery" in src
    assert "blocked external URL" in src
