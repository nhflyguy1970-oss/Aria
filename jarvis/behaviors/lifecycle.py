"""Behavior lifecycle protocol for extracted JarvisAssistant behaviors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant


@dataclass
class ApplicationBehavior:
    """A discoverable, testable behavior unit with a standard lifecycle."""

    behavior_id: str
    name: str
    category: str
    description: str
    module_path: str
    test_module: str = ""
    action_names: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def initialize(self, assistant: JarvisAssistant) -> None:
        """Bind this behavior to a running assistant instance."""

    def attach(self) -> list[str]:
        """Register handlers, platform metadata, and runtime hooks."""
        return []

    def validate(self) -> list[str]:
        """Validate declared dependencies and readiness."""
        return []

    def execute(
        self,
        assistant: JarvisAssistant,
        action: str,
        params: dict,
        message: str,
    ) -> dict | None:
        """Execute a behavior action when routed through the behavior layer."""
        return None

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "behavior_id": self.behavior_id,
            "dependencies": list(self.dependencies),
        }

    def shutdown(self) -> None:
        """Release behavior resources for an assistant shutdown."""

    def register(self) -> None:
        """Backward-compatible hook; prefer attach()."""
        self.attach()

    def descriptor(self, application_id: str) -> dict[str, Any]:
        return {
            "behavior_id": self.behavior_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "module_path": self.module_path,
            "test_module": self.test_module,
            "actions": list(self.action_names),
            "dependencies": list(self.dependencies),
            "extracted": True,
            "application_id": application_id,
        }
