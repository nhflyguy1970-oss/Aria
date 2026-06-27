"""Sunlight scene — adjust lights with sun elevation from HA (home location)."""

from __future__ import annotations

import logging
import os
from typing import Any

from jarvis.ha_light_control import ASTRONOMICAL_TWILIGHT_ELEV

log = logging.getLogger("jarvis.sunlight")

SUNLIGHT_PRESET_ID = "sunlight"


def _scene_state() -> dict[str, Any]:
    try:
        from jarvis.config import _load_chat_settings

        return dict((_load_chat_settings().get("scene_state") or {}))
    except Exception:
        return {}


def _write_scene_state(state: dict[str, Any]) -> None:
    try:
        from jarvis.config import _load_chat_settings, _write_chat_settings

        data = _load_chat_settings()
        data["scene_state"] = state
        _write_chat_settings(data)
    except Exception as exc:
        log.debug("_write_scene_state: %s", exc)


def ensure_scene_state() -> dict[str, Any]:
    """Default sunlight to auto-on daily unless explicitly disabled."""
    state = _scene_state()
    changed = False
    if "sunlight_auto" not in state:
        state["sunlight_auto"] = _env_sunlight_auto_default()
        changed = True
    if changed:
        _write_scene_state(state)
    return state


def _env_sunlight_auto_default() -> bool:
    return os.getenv("JARVIS_SUNLIGHT_AUTO", "1").lower() not in ("0", "false", "no", "off")


def is_sunlight_auto_enabled() -> bool:
    return bool(ensure_scene_state().get("sunlight_auto", True))


def is_sunlight_paused() -> bool:
    return bool(ensure_scene_state().get("sunlight_paused"))


def is_sunlight_active() -> bool:
    state = ensure_scene_state()
    return state.get("active_preset") == SUNLIGHT_PRESET_ID


def should_manage_sunlight() -> bool:
    from jarvis.home_assistant import ha_enabled

    if not ha_enabled():
        return False
    state = ensure_scene_state()
    if state.get("sunlight_paused"):
        return False
    if state.get("sunlight_auto", True):
        return True
    return state.get("active_preset") == SUNLIGHT_PRESET_ID


def set_sunlight_active(active: bool) -> None:
    state = ensure_scene_state()
    if active:
        state["active_preset"] = SUNLIGHT_PRESET_ID
        state.pop("sunlight_paused", None)
    elif state.get("active_preset") == SUNLIGHT_PRESET_ID:
        state.pop("active_preset", None)
    _write_scene_state(state)


def set_sunlight_auto(enabled: bool) -> None:
    state = ensure_scene_state()
    state["sunlight_auto"] = bool(enabled)
    if enabled:
        state.pop("sunlight_paused", None)
    _write_scene_state(state)


def _sunlight_targets(spec: dict[str, Any]) -> list[str]:
    """All available HA lights when all_lights is set; explicit devices list otherwise."""
    if spec.get("all_lights", True):
        return _default_sunlight_targets()
    out: list[str] = []
    for step in spec.get("devices") or []:
        if not isinstance(step, dict):
            continue
        t = (step.get("target") or "").strip()
        if t.startswith("light."):
            out.append(t)
    return out or _default_sunlight_targets()


def _default_sunlight_targets() -> list[str]:
    try:
        from jarvis.home_assistant import entity_is_available, list_states

        return [
            s["entity_id"]
            for s in list_states()
            if (s.get("entity_id") or "").startswith("light.") and entity_is_available(s)
        ]
    except Exception:
        return []


def _sunlight_color_kwargs(levels: dict[str, Any]) -> dict[str, Any]:
    """Same color payload for every light — matches scene preset / set_light behavior."""
    hs = levels.get("hs")
    if hs:
        return {"hs": hs}
    return {"color_temp_kelvin": levels["color_temp_kelvin"]}


def apply_sunlight_levels(
    targets: list[str] | None = None,
    *,
    transition: float = 45.0,
) -> tuple[bool, str]:
    from jarvis.ha_light_control import daylight_levels_from_sun, set_light, set_lights
    from jarvis.home_assistant import get_state

    sun = get_state("sun.sun")
    levels = daylight_levels_from_sun(sun)
    bright = levels["brightness_pct"]
    kelvin = levels["color_temp_kelvin"]
    hs = levels.get("hs")
    tint = levels.get("light_tint", "daylight")
    elev = levels.get("elevation", 0)
    phase = levels.get("phase", "day")
    lights = targets or _default_sunlight_targets()
    if not lights:
        return False, "No available lights for sunlight scene."

    color_kwargs = _sunlight_color_kwargs(levels)
    if bright <= 0:
        ok, detail = set_lights(lights, action="off", transition=transition)
        if not ok:
            ok_count = 0
            errors: list[str] = []
            for eid in lights:
                one_ok, msg = set_light(eid, action="off", transition=transition)
                if one_ok:
                    ok_count += 1
                else:
                    errors.append(msg)
            if ok_count == 0:
                return False, errors[0] if errors else "Sunlight off failed"
            ok = True
            detail = f"updated {ok_count} light(s)"
    else:
        ok, detail = set_lights(
            lights,
            action="on",
            brightness_pct=bright,
            transition=transition,
            **color_kwargs,
        )
        if not ok:
            ok_count = 0
            errors = []
            for eid in lights:
                one_ok, msg = set_light(
                    eid,
                    action="on",
                    brightness_pct=bright,
                    transition=transition,
                    **color_kwargs,
                )
                if one_ok:
                    ok_count += 1
                else:
                    errors.append(msg)
            if ok_count == 0:
                return False, errors[0] if errors else "Sunlight apply failed"
            ok = True
            detail = f"updated {ok_count} light(s)"

    color_note = f"HS {hs}" if hs else f"{kelvin}K"
    msg = (
        f"Sunlight · {phase} · {tint} · elevation {elev}° · {bright}% · {color_note} — "
        f"{detail}"
    )
    return True, msg


def apply_sunlight_night_off(
    targets: list[str] | None = None,
    *,
    transition: float = 60.0,
) -> None:
    from jarvis.ha_light_control import set_light, set_lights

    lights = targets or _default_sunlight_targets()
    if not lights:
        return
    ok, _ = set_lights(lights, action="off", transition=transition)
    if ok:
        return
    for eid in lights:
        try:
            set_light(eid, action="off", transition=transition)
        except Exception:
            pass


def activate_sunlight(spec: dict[str, Any]) -> tuple[bool, str]:
    state = ensure_scene_state()
    state["sunlight_auto"] = True
    state.pop("sunlight_paused", None)
    _write_scene_state(state)
    targets = _sunlight_targets(spec) or None
    ok, msg = apply_sunlight_levels(targets, transition=float(spec.get("transition") or 45))
    if ok:
        set_sunlight_active(True)
    return ok, msg


def deactivate_sunlight_if_other_preset(preset_id: str) -> None:
    if preset_id == SUNLIGHT_PRESET_ID:
        return
    state = ensure_scene_state()
    state["sunlight_paused"] = True
    if state.get("active_preset") == SUNLIGHT_PRESET_ID:
        state.pop("active_preset", None)
    _write_scene_state(state)


def _handle_dawn_transition(state: dict[str, Any], elevation: float) -> dict[str, Any]:
    """Resume daily sunlight at nautical/astronomical dawn."""
    prev = state.get("_last_sun_elevation")
    state["_last_sun_elevation"] = elevation
    crossed_dawn = (
        prev is not None
        and float(prev) < ASTRONOMICAL_TWILIGHT_ELEV
        and elevation >= ASTRONOMICAL_TWILIGHT_ELEV
    )
    if crossed_dawn and state.get("sunlight_auto", True):
        state.pop("sunlight_paused", None)
        ap = state.get("active_preset")
        if ap and ap != SUNLIGHT_PRESET_ID:
            state.pop("active_preset", None)
    return state


def tick_sunlight() -> None:
    try:
        from jarvis.home_assistant import get_state, ha_enabled

        if not ha_enabled():
            return

        sun = get_state("sun.sun") or {}
        attrs = sun.get("attributes") or {}
        elevation = float(attrs.get("elevation") or 0)

        state = ensure_scene_state()
        state = _handle_dawn_transition(state, elevation)
        _write_scene_state(state)

        if not should_manage_sunlight():
            return

        from jarvis.scene_presets import _load

        spec = _load().get(SUNLIGHT_PRESET_ID) or {}
        targets = _sunlight_targets(spec) or None
        transition = float(spec.get("transition") or 60)

        from jarvis.ha_light_control import daylight_levels_from_sun

        levels = daylight_levels_from_sun(sun)
        if levels.get("brightness_pct", 0) <= 0:
            apply_sunlight_night_off(targets, transition=transition)
            if state.get("active_preset") == SUNLIGHT_PRESET_ID:
                state.pop("active_preset", None)
                _write_scene_state(state)
            return

        apply_sunlight_levels(targets, transition=transition)
        if state.get("sunlight_auto", True):
            set_sunlight_active(True)
    except Exception as exc:
        log.debug("sunlight tick: %s", exc)


def bootstrap_sunlight() -> None:
    """Run once at service start — enables daily auto sunlight."""
    ensure_scene_state()
    tick_sunlight()
