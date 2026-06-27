"""planner extension."""

from jarvis.extensibility.base import Extension, ExtensionMeta


class _Ext(Extension):
    meta = ExtensionMeta(name="planner", version="1.0.0", description="planner extension", module_label="planner")

    def load(self) -> None:
        import jarvis.extensions.planner.handlers  # noqa: F401

    def routes(self):
        from jarvis.extensions.planner.routes import planner_routes

        return planner_routes()

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.planner.api import register_routes

        register_routes(app, assistant)


EXTENSION = _Ext()
