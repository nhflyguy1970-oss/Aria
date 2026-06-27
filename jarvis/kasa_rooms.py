"""Room grouping for Kasa devices (Ada home-automation parity)."""

from __future__ import annotations

from typing import Any

ROOM_KEYWORDS: dict[str, list[str]] = {
    "Office": ["office", "desk", "work", "pc", "monitor"],
    "Living Room": ["living", "lounge", "tv", "sofa"],
    "Kitchen": ["kitchen", "cook", "dining"],
    "Bedroom": ["bed", "sleep", "night"],
    "Bathroom": ["bath", "shower"],
}


def group_devices_by_room(devices: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for dev in devices:
        alias = (dev.get("alias") or dev.get("host") or "").lower()
        matched = False
        for room, keys in ROOM_KEYWORDS.items():
            if any(k in alias for k in keys):
                groups.setdefault(room, []).append(dev)
                matched = True
                break
        if not matched:
            groups.setdefault("Other", []).append(dev)
    return groups


def list_rooms(devices: list[dict[str, Any]] | None = None) -> list[str]:
    if devices is None:
        from jarvis.kasa_devices import list_devices

        devices = list_devices()
    groups = group_devices_by_room(devices)
    return ["All"] + sorted(groups.keys())
