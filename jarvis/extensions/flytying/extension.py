"""flytying extension."""

from jarvis.extensibility.base import Extension, ExtensionMeta


class _Ext(Extension):
    meta = ExtensionMeta(name="flytying", version="1.0.0", description="flytying extension", module_label="flytying")

    def load(self) -> None:
        import jarvis.extensions.flytying.handlers  # noqa: F401

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.flytying.api import register_routes

        register_routes(app, assistant)


EXTENSION = _Ext()
