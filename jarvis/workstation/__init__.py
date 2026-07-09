"""Workstation control plane — registry, lifecycle, and operations for Aria OS."""

from jarvis.workstation.lifecycle import down, restart, status, up
from jarvis.workstation.operations import diagnose, format_report, recover_safe
from jarvis.workstation.registry import all_components, component, get_registry

__all__ = [
    "all_components",
    "component",
    "diagnose",
    "down",
    "format_report",
    "get_registry",
    "recover_safe",
    "restart",
    "status",
    "up",
]
