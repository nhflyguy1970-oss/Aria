"""Audio behavior — transcription, TTS, VST, and music generation."""

from __future__ import annotations

from typing import Any

from jarvis.behaviors import register_behavior
from jarvis.behaviors.audio.context import AudioContext
from jarvis.behaviors.audio.engine import AudioActionEngine
from jarvis.behaviors.lifecycle import ApplicationBehavior
from jarvis.handlers.registry import register_action

_AUDIO_ACTIONS: dict[str, tuple[Any, bool]] = {
    "record_transcribe": (AudioActionEngine.record_transcribe, False),
    "transcribe": (AudioActionEngine.transcribe, False),
    "analyze_audio": (AudioActionEngine.analyze_audio, False),
    "speak": (AudioActionEngine.speak, False),
    "generate_audio": (AudioActionEngine.generate_audio, False),
    "edit_audio": (AudioActionEngine.edit_audio, False),
    "play_audio": (AudioActionEngine.play_audio, False),
    "process_audio_vst": (AudioActionEngine.process_audio_vst, False),
    "set_vst_live": (AudioActionEngine.set_vst_live, False),
    "generate_music": (AudioActionEngine.generate_music, False),
    "transform_genre": (AudioActionEngine.transform_genre, False),
    "generate_song": (AudioActionEngine.generate_song, False),
    "voice_to_song": (AudioActionEngine.voice_to_song, False),
    "diarize_audio": (AudioActionEngine.diarize_audio, False),
}


@register_behavior
class AudioBehavior(ApplicationBehavior):
    def __init__(self) -> None:
        super().__init__(
            behavior_id="audio",
            name="Audio",
            category="Audio",
            description="Transcription, TTS, VST processing, music, and diarization",
            module_path="jarvis.behaviors.audio",
            test_module="tests.test_behaviors",
            action_names=list(_AUDIO_ACTIONS.keys()),
            dependencies=["capability_registry"],
            stability="stable",
            owner="application",
            version="1.0.0",
        )
        self._context: AudioContext | None = None

    def initialize(self, orchestrator: Any) -> None:
        self._context = AudioContext.from_orchestrator(orchestrator)

    def attach(self) -> list[str]:
        for action, (handler, info) in _AUDIO_ACTIONS.items():
            register_action(
                action,
                info=info,
                module="audio",
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
        spec = _AUDIO_ACTIONS.get(action)
        if spec is None:
            return None
        handler, _info = spec
        self.initialize(orchestrator)
        ctx = self._context or AudioContext.from_orchestrator(orchestrator)
        return handler(ctx, params, message)

    def shutdown(self) -> None:
        self._context = None

    def _bind(self, handler):
        def _entry(orchestrator, params: dict, message: str) -> dict:
            self.initialize(orchestrator)
            ctx = self._context or AudioContext.from_orchestrator(orchestrator)
            return handler(ctx, params, message)

        return _entry
