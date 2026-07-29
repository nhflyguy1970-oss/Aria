"""Vision behavior tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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
