"""Media behavior — GPU image, video, meme generation, and prompt enhancement."""

from __future__ import annotations

from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action, register_queue
from jarvis.media_jobs import ACTION_LABELS, QUEUED_ACTIONS

_MEDIA_QUEUED = tuple(sorted(QUEUED_ACTIONS))
_MEDIA_SYNC = ("enhance_prompt",)


@register_behavior
class MediaBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="media",
            name="Media",
            category="Media",
            description="GPU image, video, meme generation, upscale, inpaint, and edit",
            module_path="jarvis.behaviors.media",
            test_module="tests.test_behaviors",
            action_names=[*_MEDIA_QUEUED, *_MEDIA_SYNC],
            dependencies=["capability_registry"],
            stability="stable",
            owner="application",
            version="1.0.0",
        )

    def initialize(self, orchestrator: Any) -> None:
        return None

    def attach(self) -> list[str]:
        from jarvis.handlers.media import MediaHandler

        for action in _MEDIA_QUEUED:
            module = "video" if action == "generate_video" else "meme" if action == "generate_meme" else "image"
            register_queue(
                action,
                "media",
                module=module,
                description=ACTION_LABELS.get(action, action),
            )

        register_action("enhance_prompt", module="image", description="Enhance image prompt")(
            self._enhance_prompt_entry(MediaHandler)
        )
        return []

    def execute(
        self,
        orchestrator: Any,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        if action != "enhance_prompt":
            return None
        from jarvis.handlers.media import MediaHandler

        return MediaHandler(orchestrator).enhance_prompt(params, message)

    def shutdown(self) -> None:
        return None

    def _enhance_prompt_entry(self, media_handler_cls):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            return media_handler_cls(orchestrator).enhance_prompt(params, message)

        return _entry
