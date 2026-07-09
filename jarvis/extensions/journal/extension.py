"""Journal extension."""

from jarvis.extensibility.base import Extension, ExtensionMeta


class JournalExtension(Extension):
    meta = ExtensionMeta(name="journal", version="1.0.0", description="Daily journal pages", module_label="journal")

    def load(self) -> None:
        import jarvis.extensions.journal.handlers  # noqa: F401
        import jarvis.extensions.journal.project_handlers  # noqa: F401


EXTENSION = JournalExtension()
