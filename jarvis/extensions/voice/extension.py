"""Voice P1 extension."""

from jarvis.extensibility.base import Extension, ExtensionMeta


class VoiceExtension(Extension):
    meta = ExtensionMeta(
        name="voice",
        version="1.0.0",
        description="Voice routing, smoke test, sessions",
        module_label="audio",
    )

    def load(self) -> None:
        import jarvis.extensions.voice.handlers  # noqa: F401

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.voice.api import register_routes

        register_routes(app, assistant)


EXTENSION = VoiceExtension()
