"""browser extension (stub load)."""
from jarvis.extensibility.base import Extension, ExtensionMeta

class _Ext(Extension):
    meta = ExtensionMeta(name="browser", version="1.0.0", description="browser extension", module_label="browser")

    def load(self) -> None:
        import jarvis.extensions.browser.handlers  # noqa: F401

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.browser.api import register_routes

        register_routes(app, assistant)

EXTENSION = _Ext()
