"""Security extension."""

from jarvis.extensibility.base import Extension, ExtensionMeta


class SecurityExtension(Extension):
    meta = ExtensionMeta(name="security", version="1.0.0", description="PIN, face, lock", module_label="security")

    def load(self) -> None:
        import jarvis.extensions.security.handlers  # noqa: F401

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.security.api import register_routes

        register_routes(app, assistant)


EXTENSION = SecurityExtension()
