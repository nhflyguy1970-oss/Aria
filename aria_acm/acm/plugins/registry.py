"""In-process extension registry — intentionally small."""

from __future__ import annotations

from typing import Any

from acm.plugins.protocol import BaseExtension, CognitiveExtension


class ExtensionError(ValueError):
    pass


class ExtensionRegistry:
    def __init__(self, *, core_version: str) -> None:
        self.core_version = core_version
        self._extensions: dict[str, CognitiveExtension] = {}
        self._engine: Any | None = None

    def bind_engine(self, engine: Any) -> None:
        self._engine = engine

    def register(self, extension: CognitiveExtension) -> None:
        if not getattr(extension, "name", None):
            raise ExtensionError("extension.name is required")
        if not getattr(extension, "version", None):
            raise ExtensionError("extension.version is required")
        name = extension.name
        if name in self._extensions:
            raise ExtensionError(f"extension already registered: {name}")
        self._assert_version_compat(extension.version)
        self._extensions[name] = extension
        if self._engine is not None:
            extension.on_register(self._engine)

    def unregister(self, name: str) -> None:
        self._extensions.pop(name, None)

    def get(self, name: str) -> CognitiveExtension | None:
        return self._extensions.get(name)

    def names(self) -> list[str]:
        return sorted(self._extensions)

    def emit(self, hook: str, event: dict[str, Any]) -> None:
        for ext in self._extensions.values():
            fn = getattr(ext, hook, None)
            if callable(fn):
                fn(event)

    def _assert_version_compat(self, extension_version: str) -> None:
        # Extensions may declare any 0.x during pre-1.0; major must match when both >= 1.
        try:
            core_major = int(self.core_version.split(".")[0])
            ext_major = int(str(extension_version).split(".")[0])
        except (TypeError, ValueError) as exc:
            raise ExtensionError(f"invalid extension version: {extension_version}") from exc
        if core_major >= 1 and ext_major != core_major:
            raise ExtensionError(
                f"extension major {ext_major} incompatible with core {self.core_version}"
            )


__all__ = ["BaseExtension", "CognitiveExtension", "ExtensionError", "ExtensionRegistry"]
