"""engineering extension (stub load)."""
from jarvis.extensibility.base import Extension, ExtensionMeta

class _Ext(Extension):
    meta = ExtensionMeta(name="engineering", version="1.0.0", description="engineering extension", module_label="engineering")

    def load(self) -> None:
        import jarvis.extensions.engineering.handlers  # noqa: F401

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.engineering.api import register_routes

        register_routes(app, assistant)

EXTENSION = _Ext()
