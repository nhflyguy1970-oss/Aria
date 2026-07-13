"""Aria Core — Operations (Mission Control cockpit; delegates to aiplatform)."""

from __future__ import annotations

from typing import Any

from aria_core._delegate import soft_import
from aria_core.ownership import module_ownership

OWNER = module_ownership("operations")


def mission_control_available() -> bool:
    return soft_import("aiplatform.mission_control.aggregator") is not None


def collect_overview(**kwargs: Any) -> dict[str, Any]:
    """Delegate to Mission Control aggregator overview (unchanged behavior)."""
    mod = soft_import("aiplatform.mission_control.aggregator")
    if mod is None:
        return {
            "ok": False,
            "error": "aiplatform.mission_control unavailable",
            "owner": OWNER["owner"],
        }
    return dict(mod.collect_overview(**kwargs))


def collect_mission_control(**kwargs: Any) -> dict[str, Any]:
    mod = soft_import("aiplatform.mission_control.aggregator")
    if mod is None:
        return {
            "ok": False,
            "error": "aiplatform.mission_control unavailable",
            "owner": OWNER["owner"],
        }
    return dict(mod.collect_mission_control(**kwargs))
