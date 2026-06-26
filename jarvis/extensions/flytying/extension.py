"""flytying extension (stub load)."""
from jarvis.extensibility.base import Extension, ExtensionMeta

class _Ext(Extension):
    meta = ExtensionMeta(name="flytying", version="1.0.0", description="flytying extension", module_label="flytying")

    def load(self) -> None:
        import jarvis.extensions.flytying.handlers  # noqa: F401

EXTENSION = _Ext()
