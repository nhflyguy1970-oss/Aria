"""smarthome extension (stub load)."""
from jarvis.extensibility.base import Extension, ExtensionMeta

class _Ext(Extension):
    meta = ExtensionMeta(name="smarthome", version="1.0.0", description="smarthome extension", module_label="smarthome")

    def load(self) -> None:
        import jarvis.extensions.smarthome.handlers  # noqa: F401

EXTENSION = _Ext()
