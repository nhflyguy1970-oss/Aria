"""flytying extension."""

from jarvis.extensibility.base import Extension, ExtensionMeta


class _Ext(Extension):
    meta = ExtensionMeta(
        name="flytying",
        version="2.0.0",
        description="Fly Tying — patterns, inventory, sessions, RAG",
        module_label="flytying",
    )

    def load(self) -> None:
        import jarvis.extensions.flytying.handlers  # noqa: F401

    def routes(self):
        from jarvis.extensions.flytying.routes import flytying_routes

        return flytying_routes()

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.flytying.api import register_routes

        register_routes(app, assistant)
        try:
            from jarvis.flytying_product.api import register_product_routes

            register_product_routes(app, assistant)
        except Exception:
            pass


EXTENSION = _Ext()
