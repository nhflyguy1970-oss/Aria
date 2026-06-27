"""projects extension (stub load)."""
from jarvis.extensibility.base import Extension, ExtensionMeta

class _Ext(Extension):
    meta = ExtensionMeta(name="projects", version="1.0.0", description="projects extension", module_label="projects")

    def load(self) -> None:
        import jarvis.extensions.projects.handlers  # noqa: F401

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.projects.api import register_routes

        register_routes(app, assistant)

EXTENSION = _Ext()
