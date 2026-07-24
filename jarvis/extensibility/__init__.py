"""Internal extension framework (Phase 1)."""

from jarvis.extensibility.base import Extension, ExtensionMeta
from jarvis.extensibility.loader import (
    extension_routes,
    list_extensions,
    load_extensions,
    register_extension_api,
)

__all__ = [
    "Extension",
    "ExtensionMeta",
    "extension_routes",
    "list_extensions",
    "load_extensions",
    "register_extension_api",
]
