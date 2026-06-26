"""browser extension (stub load)."""
from jarvis.extensibility.base import Extension, ExtensionMeta

class _Ext(Extension):
    meta = ExtensionMeta(name="browser", version="1.0.0", description="browser extension", module_label="browser")

    def load(self) -> None:
        import jarvis.extensions.browser.handlers  # noqa: F401

EXTENSION = _Ext()
