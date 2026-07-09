"""Workstation control plane — registry, lifecycle, and operations for Aria OS."""

from jarvis.workstation.inventory import collect_inventory, format_inventory_text, verify_inventory
from jarvis.workstation.lifecycle import down, restart, status, up
from jarvis.workstation.operations import diagnose, format_report, recover_safe
from jarvis.workstation.registry import all_components, component, get_registry

__all__ = [
    "all_components",
    "collect_inventory",
    "component",
    "diagnose",
    "down",
    "format_inventory_text",
    "format_report",
    "get_registry",
    "recover_safe",
    "restart",
    "status",
    "up",
    "verify_inventory",
]
