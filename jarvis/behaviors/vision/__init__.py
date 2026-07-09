"""Vision behavior — image analysis, OCR, compare, and batch processing."""

from __future__ import annotations

from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.behaviors.vision.context import VisionContext
from jarvis.behaviors.vision.engine import VisionActionEngine
from jarvis.handlers.registry import register_action

_VISION_ACTIONS: dict[str, tuple[Any, bool]] = {
    "describe_image": (VisionActionEngine.describe_image, False),
    "analyze_image": (VisionActionEngine.analyze_image, False),
    "ocr_image": (VisionActionEngine.ocr_image, False),
    "ocr_structured_image": (VisionActionEngine.ocr_structured_image, False),
    "image_to_code": (VisionActionEngine.image_to_code, False),
    "analyze_region": (VisionActionEngine.analyze_region, False),
    "batch_vision": (VisionActionEngine.batch_vision, False),
    "compare_images": (VisionActionEngine.compare_images, False),
    "analyze_video_frame": (VisionActionEngine.analyze_image, False),
}


@register_behavior
class VisionBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="vision",
            name="Vision",
            category="Vision",
            description="Image analysis, OCR, region inspect, compare, and batch vision",
            module_path="jarvis.behaviors.vision",
            test_module="tests.test_behaviors",
            action_names=list(_VISION_ACTIONS.keys()),
            dependencies=["capability_registry"],
            stability="stable",
            owner="application",
            version="1.0.0",
        )
        self._context: VisionContext | None = None

    def initialize(self, orchestrator: Any) -> None:
        self._context = VisionContext.from_orchestrator(orchestrator)

    def attach(self) -> list[str]:
        for action, (handler, info) in _VISION_ACTIONS.items():
            register_action(
                action,
                info=info,
                module="vision",
                description=action.replace("_", " "),
            )(self._bind(handler))
        return []

    def execute(
        self,
        orchestrator: Any,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        spec = _VISION_ACTIONS.get(action)
        if spec is None:
            return None
        handler, _info = spec
        self.initialize(orchestrator)
        ctx = self._context or VisionContext.from_orchestrator(orchestrator)
        return handler(ctx, params, message)

    def shutdown(self) -> None:
        self._context = None

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            self.initialize(orchestrator)
            ctx = self._context or VisionContext.from_orchestrator(orchestrator)
            return handler(ctx, params, message)

        return _entry
