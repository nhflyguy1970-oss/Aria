"""engineering extension (stub load)."""
from jarvis.extensibility.base import Extension, ExtensionMeta

class _Ext(Extension):
    meta = ExtensionMeta(name="engineering", version="1.0.0", description="engineering extension", module_label="engineering")

    def load(self) -> None:
        import jarvis.extensions.engineering.handlers  # noqa: F401

EXTENSION = _Ext()
