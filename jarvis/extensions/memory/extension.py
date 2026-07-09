"""Memory extension — facts, profile, cheatsheets, checkpoints."""

from jarvis.extensibility.base import Extension, ExtensionMeta


class MemoryExtension(Extension):
    meta = ExtensionMeta(
        name="memory",
        version="1.0.0",
        description="Long-term memory, cheatsheets, profile, and project checkpoints",
        module_label="memory",
    )

    def load(self) -> None:
        import jarvis.extensions.memory.correction_learning_handlers  # noqa: F401
        import jarvis.extensions.memory.document_learning_handlers  # noqa: F401
        import jarvis.extensions.memory.handlers  # noqa: F401
        import jarvis.extensions.memory.observation_learning_handlers  # noqa: F401

    def routes(self):
        from jarvis.extensions.memory.routes import memory_routes

        return memory_routes()

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.memory.api import register_routes

        register_routes(app, assistant)


EXTENSION = MemoryExtension()
