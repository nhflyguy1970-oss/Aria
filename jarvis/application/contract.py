"""Local application contract types — used when AI Platform is not installed."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ApplicationCapabilities:
    id: str
    label: str
    version: str = ""
    namespaces: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)


@dataclass
class ApplicationRegistration:
    app_id: str
    install_path: str = ""
    component_ids: list[str] = field(default_factory=list)
    probe_ids: list[str] = field(default_factory=list)
    acceptance_ids: list[str] = field(default_factory=list)
