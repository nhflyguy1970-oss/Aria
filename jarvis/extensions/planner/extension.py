"""planner extension (stub load)."""
from jarvis.extensibility.base import Extension, ExtensionMeta

class _Ext(Extension):
    meta = ExtensionMeta(name="planner", version="1.0.0", description="planner extension", module_label="planner")

    def load(self) -> None:
        import jarvis.extensions.planner.handlers  # noqa: F401

EXTENSION = _Ext()
