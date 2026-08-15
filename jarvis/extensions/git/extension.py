"""Git extension."""

from jarvis.extensibility.base import Extension, ExtensionMeta


class GitExtension(Extension):
    meta = ExtensionMeta(
        name="git", version="1.0.0", description="Git status, diff, commit", module_label="coding"
    )

    def load(self) -> None:
        import jarvis.extensions.git.handlers  # noqa: F401

    def routes(self):
        from jarvis.extensions.git.routes import git_routes

        return git_routes()

    def register_api(self, app, assistant) -> None:
        from jarvis.extensions.git.api import register_routes

        register_routes(app, assistant)


EXTENSION = GitExtension()
