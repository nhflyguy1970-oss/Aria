"""Extension protocol for domain modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import FastAPI

    from jarvis.assistant import JarvisAssistant
    from jarvis.router_table import RouteRule


@dataclass(frozen=True)
class ExtensionMeta:
    name: str
    version: str = "1.0.0"
    description: str = ""
    module_label: str = ""


class Extension:
    """Hook surface for a domain extension (actions, routes, optional API)."""

    meta: ExtensionMeta

    def load(self) -> None:
        """Import handler modules so @register_action side effects run."""

    def routes(self) -> list[RouteRule]:
        return []

    def register_api(self, app: FastAPI, assistant: JarvisAssistant) -> None:
        pass

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.meta.name,
            "version": self.meta.version,
            "description": self.meta.description,
            "module_label": self.meta.module_label,
        }
