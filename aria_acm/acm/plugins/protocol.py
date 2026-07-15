"""Minimal cognitive extension protocol — no host assumptions."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CognitiveExtension(Protocol):
    """Attachable capability that contributes experiences/services — not core cognition."""

    name: str
    version: str

    def on_register(self, engine: Any) -> None:
        """Called once after successful registration."""

    def after_encode(self, event: dict[str, Any]) -> None:
        """Optional hook; default no-op implementations allowed via BaseExtension."""

    def after_remember(self, event: dict[str, Any]) -> None: ...

    def after_sleep(self, event: dict[str, Any]) -> None: ...


class BaseExtension:
    """Convenience base with no-op hooks."""

    name: str = "unnamed"
    version: str = "0.0.0"

    def on_register(self, engine: Any) -> None:
        return None

    def after_encode(self, event: dict[str, Any]) -> None:
        return None

    def after_remember(self, event: dict[str, Any]) -> None:
        return None

    def after_sleep(self, event: dict[str, Any]) -> None:
        return None
