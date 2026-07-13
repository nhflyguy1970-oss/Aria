"""Aria Core — Events façade (Phase 4)."""

from __future__ import annotations

from aria_core.event_bus import (
    CoreEvent,
    get_bus,
    mission_control_panel,
    publish,
    publish_name,
    recent_events,
    replay_ring,
    safe_publish,
    subscribe,
    unsubscribe,
)
from aria_core.event_contracts import get_contract, list_contracts, validate_contracts
from aria_core.event_types import ALL_EVENT_TYPES, EVENT_VERSION
from aria_core.ownership import module_ownership

OWNER = module_ownership("events")

__all__ = [
    "ALL_EVENT_TYPES",
    "CoreEvent",
    "EVENT_VERSION",
    "OWNER",
    "get_bus",
    "get_contract",
    "list_contracts",
    "mission_control_panel",
    "publish",
    "publish_name",
    "recent_events",
    "replay_ring",
    "safe_publish",
    "subscribe",
    "unsubscribe",
    "validate_contracts",
]
