"""projects extension — workspace identity layer."""

from jarvis.extensibility.base import Extension, ExtensionMeta


class _Ext(Extension):
    meta = ExtensionMeta(
        name="projects",
        version="2.0.0",
        description="Workspace identity — coding, memory, journal, knowledge, browser",
        module_label="projects",
    )

    def load(self) -> None:
        import jarvis.extensions.projects.handlers  # noqa: F401

    def routes(self):
        from jarvis.extensions.projects.routes import project_routes

        return project_routes()

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.projects.api import register_routes

        register_routes(app, assistant)


EXTENSION = _Ext()
