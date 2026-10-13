"""Vision behavior tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.behaviors.vision.engine import VisionActionEngine
from jarvis.handlers.registry import call_action, has_action


def test_vision_actions_registered():
    from jarvis.behaviors import register_behaviors

    register_behaviors()
    assert has_action("describe_image")
    assert has_action("ocr_image")


def test_describe_image_requires_path():
    ctx = MagicMock()
    ctx.session.resolve_image.return_value = ""
    result = VisionActionEngine.describe_image(ctx, {}, "describe")
    assert result.get("ok") is False


def test_ocr_via_registry():
    from jarvis.behaviors import register_behaviors
    from jarvis.handlers.registry import call_action

    register_behaviors()
    assistant = MagicMock()
    assistant._vision_llava_warned = False
    assistant.session.resolve_image.return_value = "/tmp/photo.png"
    with patch(
        "jarvis.vision_product.engine.analyze",
        return_value={"ok": True, "message": "line one", "pipeline": "vision_engine", "warnings": []},
    ):
        result = call_action(assistant, "ocr_image", {}, "ocr")
    assert result.get("ok") is True
    assert "line one" in result.get("message", "")


# --- streamed vision must commit a real result (regression: missing _vision_ok) ---

VISION_STREAM_ACTIONS = [
    "describe_image",
    "analyze_image",
    "ocr_image",
    "ocr_structured_image",
    "image_to_code",
    "analyze_video_frame",
]


@pytest.mark.parametrize("action", VISION_STREAM_ACTIONS)
def test_analyze_from_stream_returns_success(action: str) -> None:
    result = VisionActionEngine.analyze_from_stream(
        MagicMock(), "A red bicycle leaning on a wall.", image_path="/tmp/x.png", action=action
    )
    assert result.get("ok") is True, (action, result)
    assert result.get("module") == "vision"
    assert result.get("action") == action


def test_analyze_from_stream_preserves_the_generated_answer() -> None:
    answer = "A red bicycle leaning on a wall."
    result = VisionActionEngine.analyze_from_stream(MagicMock(), answer, image_path="/tmp/x.png")
    assert result.get("message") == answer


def test_analyze_from_stream_carries_metadata() -> None:
    result = VisionActionEngine.analyze_from_stream(
        MagicMock(), "text", image_path="/tmp/x.png", action="ocr_image", warnings=["w1"]
    )
    assert result.get("image_path") == "/tmp/x.png"
    assert result.get("pipeline") == "vision_engine"
    assert result.get("warnings") == ["w1"]


def test_analyze_from_stream_uses_same_envelope_as_compare() -> None:
    """No second result format for vision."""
    streamed = VisionActionEngine.analyze_from_stream(MagicMock(), "a", image_path="/tmp/x.png")
    compared = VisionActionEngine.compare_from_result(
        MagicMock(), {"answer": "a", "path1": "/tmp/x.png", "path2": "/tmp/y.png"}
    )
    for key in ("ok", "module", "pipeline"):
        assert streamed.get(key) == compared.get(key), key


def test_analyze_from_stream_does_not_swallow_errors() -> None:
    """A genuine vision failure must stay an error, never become success."""
    result = VisionActionEngine.analyze_from_stream(
        MagicMock(), "ERROR: vision model unavailable", image_path="/tmp/x.png"
    )
    assert result.get("ok") is False
    assert "vision model unavailable" in str(result.get("message") or result.get("error"))


def _drive_vision_stream(action: str, tokens: list[str]):
    """Run the real stream branch with a stubbed vision engine."""
    from jarvis.assistant import JarvisAssistant

    a = MagicMock()
    a._stream_lite_ui = False
    a.vision.analyze_stream.return_value = iter(tokens)
    a.session.last_image = "/tmp/x.png"
    a.yield_request_lock = lambda: None
    return list(
        JarvisAssistant._process_stream_unlocked(
            a,
            "look at this",
            None,
            None,
            None,
            "rid-vision",
            False,
            {"action": action, "params": {"path": "/tmp/x.png"}},
        )
    )


@pytest.mark.parametrize("action", ["describe_image", "analyze_image", "ocr_image", "image_to_code"])
def test_vision_stream_terminal_event_carries_the_answer(action: str) -> None:
    """Would have caught the missing _vision_ok: tokens streamed, then AttributeError."""
    events = _drive_vision_stream(action, ["A red ", "bicycle."])
    tokens = [e for e in events if e.get("type") == "token"]
    done = [e for e in events if e.get("type") == "done"]
    assert tokens, f"{action}: no tokens streamed"
    assert len(done) == 1, f"{action}: expected exactly one terminal, got {done}"
    terminal = done[0]
    assert terminal.get("ok") is True, terminal
    assert "A red bicycle." in str(terminal.get("message")), terminal


def test_vision_stream_error_token_still_errors() -> None:
    events = _drive_vision_stream("describe_image", ["ERROR: no vision model"])
    done = [e for e in events if e.get("type") == "done"]
    assert done and done[0].get("ok") is False


def test_vision_stream_yields_the_request_lock() -> None:
    """Concurrency repair must stay intact — vision must not block other turns."""
    from jarvis.assistant import JarvisAssistant

    a = MagicMock()
    a._stream_lite_ui = False
    a.vision.analyze_stream.return_value = iter(["ok"])
    a.session.last_image = "/tmp/x.png"
    calls = {"n": 0}

    def _yield():
        calls["n"] += 1

    a.yield_request_lock = _yield
    list(
        JarvisAssistant._process_stream_unlocked(
            a, "look", None, None, None, "rid-v2", False,
            {"action": "describe_image", "params": {"path": "/tmp/x.png"}},
        )
    )
    assert calls["n"] >= 1, "vision branch stopped releasing the request lock"
