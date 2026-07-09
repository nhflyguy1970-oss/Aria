"""Audio behavior tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from jarvis.behaviors.audio.engine import AudioActionEngine
from jarvis.handlers.registry import call_action, has_action


def test_audio_actions_registered():
    from jarvis.behaviors import register_behaviors

    register_behaviors()
    assert has_action("transcribe")
    assert has_action("generate_audio")
    assert has_action("speak")


def test_transcribe_via_registry():
    from jarvis.behaviors import register_behaviors

    register_behaviors()
    assistant = MagicMock()
    assistant.audio.transcribe.return_value = "hello world"
    assistant.session.resolve_audio.return_value = "/tmp/sample.wav"
    result = call_action(assistant, "transcribe", {}, "transcribe this")
    assert result.get("ok") is True
    assert "hello world" in result.get("message", "")


def test_generate_audio_requires_text():
    ctx = MagicMock()
    result = AudioActionEngine.generate_audio(ctx, {}, "generate audio")
    assert result.get("ok") is False
