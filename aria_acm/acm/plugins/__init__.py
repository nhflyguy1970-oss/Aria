"""Extension points for non-core cognitive capabilities."""

from acm.plugins.protocol import BaseExtension, CognitiveExtension
from acm.plugins.registry import ExtensionError, ExtensionRegistry

__all__ = [
    "BaseExtension",
    "CognitiveExtension",
    "ExtensionError",
    "ExtensionRegistry",
]
