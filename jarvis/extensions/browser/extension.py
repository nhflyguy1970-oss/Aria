"""browser extension."""
from jarvis.extensibility.base import Extension, ExtensionMeta


class _Ext(Extension):
    meta = ExtensionMeta(
        name="browser",
        version="2.0.0",
        description="Browser agent — live Playwright web interaction",
        module_label="browser",
    )

    def load(self) -> None:
        import jarvis.extensions.browser.handlers  # noqa: F401

    def routes(self):
        from jarvis.extensions.browser.routes import browser_routes

        return browser_routes()

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.browser.api import register_routes

        register_routes(app, assistant)


EXTENSION = _Ext()
