"""smarthome extension (stub load)."""
from jarvis.extensibility.base import Extension, ExtensionMeta

class _Ext(Extension):
    meta = ExtensionMeta(name="smarthome", version="1.0.0", description="smarthome extension", module_label="smarthome")

    def load(self) -> None:
        import jarvis.extensions.smarthome.handlers  # noqa: F401

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.smarthome.api import register_routes

        register_routes(app, assistant)

EXTENSION = _Ext()
