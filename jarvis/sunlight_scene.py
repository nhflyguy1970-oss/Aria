# Source Generated with Decompyle++
# File: sunlight_scene.cpython-312.pyc (Python 3.12)

'''Sunlight scene — adjust lights with sun elevation from HA (home location).'''
from __future__ import annotations
import logging
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
from jarvis.ha_light_control import CIVIL_SUNRISE_ELEV, NIGHT_OFF_ELEV
log = logging.getLogger('jarvis.sunlight')
SUNLIGHT_PRESET_ID = 'sunlight'
SUNLIGHT_TICK_INTERVAL_SEC = 30
SUNLIGHT_SKIP_BRIGHTNESS_PCT = 1
SUNLIGHT_SKIP_ELEVATION_DEG = 0.05
_last_sun_elevation_tick: 'float | None' = None

def _scene_state():
    try:
        from jarvis.config import _load_chat_settings
        raw = _load_chat_settings().get("scene_state") or {}
        return dict(raw)
    except Exception:
        return {}


def _write_scene_state(state=None):
    try:
        from jarvis.config import _load_chat_settings, _write_chat_settings
        data = _load_chat_settings()
        data["scene_state"] = state
        _write_chat_settings(data)
    except Exception as exc:
        log.debug("_write_scene_state: %s", exc)


def _norm_label(text=None):
    import re
    if not text:
        return ""
    return re.sub(r"[\s_]+", " ", str(text).lower()).strip()


def _sunlight_exclude_ids(spec=None):
    out = set()
    for raw in spec.get("exclude") or []:
        eid = str(raw).strip()
        if eid.startswith("light."):
            out.add(eid)
    return out


def _sunlight_include_ids(spec=None):
    out = []
    seen = set()
    for raw in spec.get("include") or []:
        eid = str(raw).strip()
        if not eid.startswith("light."):
            continue
        if eid in seen:
            continue
        out.append(eid)
        seen.add(eid)
    return out


def _matches_sunlight_include_name(term=None, friendly=None, eid=None):
    """Match preset include_names like wall, wall1, lamp to HA lights."""
    fn = _norm_label(friendly)
    t = _norm_label(term)
    if t in ("wall1", "wall 1"):
        return "wall 1" in fn or fn == "wall1" or eid == "light.merkury_bw904_smart_bulb_2"
    if t == "wall":
        if "wall 1" in fn or fn == "wall1":
            return False
        if fn == "wall" or fn.startswith("wall "):
            return True
        return "family room" in fn or eid == "light.geeni_bw413_smart_bulb_2"
    if t == "lamp":
        return eid == "light.table_lamp" or fn in ("table lamp", "lamp") or eid in (
            "light.lamp",
            "light.lamp_1",
            "light.geeni_bw413_smart_bulb_3",
        )
    return fn == t or t in fn.split()


def ensure_scene_state():
    '''Default sunlight to auto-on daily unless explicitly disabled.'''
    state = _scene_state()
    changed = False
    if 'sunlight_auto' not in state:
        state['sunlight_auto'] = _env_sunlight_auto_default()
        changed = True
    if changed:
        _write_scene_state(state)
    return state


def _env_sunlight_auto_default():
    return os.getenv('JARVIS_SUNLIGHT_AUTO', '1').lower() not in ('0', 'false', 'no', 'off')


def is_sunlight_auto_enabled():
    return bool(ensure_scene_state().get('sunlight_auto', True))


def is_sunlight_paused():
    return bool(ensure_scene_state().get('sunlight_paused'))


def is_sunlight_active():
    state = ensure_scene_state()
    return state.get('active_preset') == SUNLIGHT_PRESET_ID


def should_manage_sunlight():
    ha_enabled = ha_enabled
    import jarvis.home_assistant
    if not ha_enabled():
        return False
    state = ensure_scene_state()
    if state.get('sunlight_paused'):
        return False
    if state.get('sunlight_auto', True):
        return True
    return state.get('active_preset') == SUNLIGHT_PRESET_ID


def set_sunlight_active(active = None):
    state = ensure_scene_state()
    if active:
        state['active_preset'] = SUNLIGHT_PRESET_ID
        state.pop('sunlight_paused', None)
        state.pop('sunlight_pause_reason', None)
        state.pop('_sunlight_paused_on', None)
    elif state.get('active_preset') == SUNLIGHT_PRESET_ID:
        state.pop('active_preset', None)
    _write_scene_state(state)


def set_sunlight_auto(enabled = None):
    state = ensure_scene_state()
    state['sunlight_auto'] = bool(enabled)
    if enabled:
        state.pop('sunlight_paused', None)
        state.pop('sunlight_pause_reason', None)
        state.pop('_sunlight_paused_on', None)
    _write_scene_state(state)


def _resolve_sunlight_includes(spec=None):
    """Resolve forced sunlight lights — bypass merkury/hidden filters, not bedroom exclude."""
    out = list(_sunlight_include_ids(spec))
    names = spec.get("include_names") or []
    if not names:
        return out
    try:
        from jarvis.home_assistant import entity_is_available, list_states

        seen = set(out)
        for st in list_states():
            eid = st.get("entity_id") or ""
            if not eid.startswith("light."):
                continue
            if not entity_is_available(st):
                continue
            friendly = (st.get("attributes") or {}).get("friendly_name", "")
            for term in names:
                if _matches_sunlight_include_name(term, friendly, eid) and eid not in seen:
                    out.append(eid)
                    seen.add(eid)
                    break
    except Exception:
        log.debug("_resolve_sunlight_includes failed", exc_info=True)
    return out


def _filter_forced_sunlight_includes(entity_ids=None, spec=None):
    """Apply only hard excludes and availability to forced includes."""
    exclude = _sunlight_exclude_ids(spec)
    if not entity_ids:
        return []
    try:
        from jarvis.home_assistant import entity_is_available, get_state
    except Exception:
        return [eid for eid in entity_ids if eid not in exclude]
    out = []
    for eid in entity_ids:
        if eid in exclude:
            continue
        st = get_state(eid)
        if st and entity_is_available(st):
            out.append(eid)
    return out


def _is_bedroom_light(st = None):
    '''Exclude bulbs labeled bedroom in friendly name, entity id, or area.'''
    if not st.get('attributes'):
        st.get('attributes')
    attrs = { }
    if not st.get('entity_id'):
        st.get('entity_id')
    eid = ''.lower()
    if not attrs.get('friendly_name'):
        attrs.get('friendly_name')
    friendly = _norm_label('')
    if not attrs.get('area'):
        attrs.get('area')
        if not attrs.get('area_name'):
            attrs.get('area_name')
    area = _norm_label(str(''))
    hay = f'''{friendly} {_norm_label(eid)} {area}'''
    return 'bedroom' in hay


def _is_merkury_light(st = None):
    """Merkury bulbs don't track CCT well — keep out of sunlight."""
    if not st.get('entity_id'):
        st.get('entity_id')
    eid = ''.lower()
    return 'merkury' in eid


def _filter_sunlight_targets(entity_ids = None, spec = None):
    exclude = _sunlight_exclude_ids(spec)
    if not entity_ids:
        return []
# WARNING: Decompyle incomplete


def _sunlight_spec():
    
    try:
        _load = _load
        import jarvis.scene_presets
        if not _load().get(SUNLIGHT_PRESET_ID):
            _load().get(SUNLIGHT_PRESET_ID)
        return dict({ })
    except Exception:
        return 



def _sunlight_targets(spec = None):
    '''All available HA lights when all_lights is set; explicit devices list otherwise.'''
    if spec.get('all_lights', True):
        raw = _default_sunlight_targets(spec)
    else:
        out = []
        if not spec.get('devices'):
            spec.get('devices')
        for step in []:
            if not isinstance(step, dict):
                continue
            if not step.get('target'):
                step.get('target')
            t = ''.strip()
            if not t.startswith('light.'):
                continue
            out.append(t)
        if not out:
            out
        raw = _default_sunlight_targets(spec)
    forced = _filter_forced_sunlight_includes(_resolve_sunlight_includes(spec), spec)
    merged = []
    seen = set()
    for eid in forced + raw:
        if not eid not in seen:
            continue
        merged.append(eid)
        seen.add(eid)
    return merged


def _default_sunlight_targets(spec = None):
    pass
# WARNING: Decompyle incomplete


def _local_date_str():
    '''Home-local calendar date (for pause/resume across restarts).'''
    
    try:
        get_ha_location = get_ha_location
        import jarvis.home_assistant
        if not get_ha_location().get('time_zone'):
            get_ha_location().get('time_zone')
        tz_name = 'America/New_York'
        return datetime.now(ZoneInfo(tz_name)).date().isoformat()
    except Exception:
        return 



def pause_sunlight_for_manual():
    '''Manual off/toggle pauses auto sunlight until the next dawn.'''
    state = ensure_scene_state()
    if not state.get('sunlight_auto', True):
        return None
    state['sunlight_paused'] = True
    state['sunlight_pause_reason'] = 'manual'
    state['_sunlight_paused_on'] = _local_date_str()
    if state.get('active_preset') == SUNLIGHT_PRESET_ID:
        state.pop('active_preset', None)
    _write_scene_state(state)


def maybe_pause_sunlight_for_light_action(entity_id = None, action = None, *, current_state):
    '''Pause sunlight auto when the user manually turns off a managed light.'''
    if not entity_id:
        entity_id
    eid = ''.strip()
    if not eid.startswith('light.'):
        return None
    if not should_manage_sunlight():
        return None
    if not action:
        action
    act = ''.strip().lower()
    if act == 'off':
        pause_sunlight_for_manual()
        return None
    if act != 'toggle':
        return None
# WARNING: Decompyle incomplete


def get_sunlight_target_lights():
    '''Lights currently managed by the sunlight scene (respects preset spec).'''
    
    try:
        _load = _load
        import jarvis.scene_presets
        if not _load().get(SUNLIGHT_PRESET_ID):
            _load().get(SUNLIGHT_PRESET_ID)
        spec = { }
        if not _sunlight_targets(spec):
            _sunlight_targets(spec)
        return _default_sunlight_targets()
    except Exception:
        return 



def turn_off_sunlight_lights(*, transition):
    '''Pause sunlight auto and turn off all sunlight target lights.'''
    set_light = set_light
    set_lights = set_lights
    import jarvis.ha_light_control
    pause_sunlight_for_manual()
    lights = get_sunlight_target_lights()
    if not lights:
        return (False, 'No lights available to turn off.')
    (ok, detail) = set_lights(lights, action = 'off', transition = transition)
    if not ok:
        ok_count = 0
        errors = []
        for eid in lights:
            (one_ok, msg) = set_light(eid, action = 'off', transition = transition)
            if one_ok:
                ok_count += 1
                continue
            errors.append(msg)
        if ok_count == 0:
            if errors:
                return (False, errors[0])
            return (None, False)
        detail = f'''{ok_count} light(s)'''
    return (True, detail)


def _sunlight_apply_signature(levels = None, bright = None, color_kwargs = None):
    hs = color_kwargs.get('hs')
    elev = levels.get('elevation')
    if not color_kwargs.get('color_temp_kelvin'):
        color_kwargs.get('color_temp_kelvin')
        if not levels.get('color_temp_kelvin'):
            levels.get('color_temp_kelvin')
# WARNING: Decompyle incomplete


def _should_skip_sunlight_apply(state = None, sig = None):
    """Skip HA calls when the sun/weather target hasn't moved enough since last apply."""
    last = state.get('_last_sunlight_apply')
    if not isinstance(last, dict):
        return False
    if abs(int(last.get('bright', -999)) - sig['bright']) >= SUNLIGHT_SKIP_BRIGHTNESS_PCT:
        return False
    if int(last.get('kelvin', -1)) != sig['kelvin']:
        return False
    if last.get('hs') != sig['hs']:
        return False
    if last.get('phase') != sig['phase']:
        return False
    last_elev = last.get('elevation')
    sig_elev = sig.get('elevation')
# WARNING: Decompyle incomplete


def sunlight_status():
    '''Diagnostics for UI / debugging.'''
    state = ensure_scene_state()
    last = state.get('_last_sunlight_apply') if isinstance(state.get('_last_sunlight_apply'), dict) else { }
    targets = get_sunlight_target_lights()
    return {
        'managed': should_manage_sunlight(),
        'target_count': len(targets),
        'targets': targets,
        'last_apply': last,
        'last_tick_at': state.get('_last_sunlight_tick_at'),
        'last_tick_error': state.get('_last_sunlight_tick_error'),
        'last_tick_action': state.get('_last_sunlight_tick_action'),
        'tick_interval_sec': SUNLIGHT_TICK_INTERVAL_SEC }


def _record_sunlight_tick(state = None, *, action, error, apply_sig):
    datetime = datetime
    timezone = timezone
    import datetime
    state['_last_sunlight_tick_at'] = datetime.now(timezone.utc).isoformat()
    state['_last_sunlight_tick_action'] = action
    if error:
        state['_last_sunlight_tick_error'] = error
    else:
        state.pop('_last_sunlight_tick_error', None)
# WARNING: Decompyle incomplete


def _sunlight_color_kwargs(levels = None):
    sunlight_unified_color = sunlight_unified_color
    import jarvis.ha_light_control
    return sunlight_unified_color(levels)


def _any_target_light_off(lights = None, *, states_by_id):
    get_state = get_state
    import jarvis.home_assistant
# WARNING: Decompyle incomplete


def _resolve_sunlight_transition(lights = None, *, base_transition, sunrise_transition, bright, resumed, states_by_id):
    '''Long fade when turning on from off; shorter steps when already lit.'''
    if bright <= 0:
        return base_transition
    if not None:
        if states_by_id or _any_target_light_off(lights, states_by_id = states_by_id):
            pass
        elif _any_target_light_off(lights):
            return max(float(sunrise_transition), float(base_transition))
    return min(float(base_transition), float(SUNLIGHT_TICK_INTERVAL_SEC) * 2)


def apply_sunlight_levels(targets = None, *, transition, sunrise_transition, resumed, states_by_id):
    apply_sunlight_fleet = apply_sunlight_fleet
    daylight_levels_from_sun = daylight_levels_from_sun
    set_light = set_light
    set_lights = set_lights
    sunlight_effective_brightness = sunlight_effective_brightness
    NIGHT_OFF_ELEV = NIGHT_OFF_ELEV
    import jarvis.ha_light_control
    get_state = get_state
    list_states = list_states
    import jarvis.home_assistant
# WARNING: Decompyle incomplete


def apply_sunlight_night_off(targets = None, *, transition):
    set_light = set_light
    set_lights = set_lights
    import jarvis.ha_light_control
    if not targets:
        targets
    lights = _default_sunlight_targets(_sunlight_spec())
    if not lights:
        return None
    (ok, _) = set_lights(lights, action = 'off', transition = transition)
    if ok:
        return None
    for eid in lights:
        set_light(eid, action = 'off', transition = transition)
    return None


def activate_sunlight(spec = None):
    state = ensure_scene_state()
    state['sunlight_auto'] = True
    state.pop('sunlight_paused', None)
    state.pop('sunlight_pause_reason', None)
    state.pop('_sunlight_paused_on', None)
    _write_scene_state(state)
    if not _sunlight_targets(spec):
        _sunlight_targets(spec)
    targets = None
    if not spec.get('transition'):
        spec.get('transition')
    if not spec.get('sunrise_transition'):
        spec.get('sunrise_transition')
    (ok, msg) = apply_sunlight_levels(targets, transition = float(45), sunrise_transition = float(600))
    if ok:
        set_sunlight_active(True)
    return (ok, msg)


def deactivate_sunlight_if_other_preset(preset_id = None):
    if preset_id == SUNLIGHT_PRESET_ID:
        return None
    state = ensure_scene_state()
    state['sunlight_paused'] = True
    state['sunlight_pause_reason'] = 'preset'
    state['_sunlight_paused_on'] = _local_date_str()
    if state.get('active_preset') == SUNLIGHT_PRESET_ID:
        state.pop('active_preset', None)
    _write_scene_state(state)


def _clear_sunlight_pause(state = None):
    state.pop('sunlight_paused', None)
    state.pop('sunlight_pause_reason', None)
    state.pop('_sunlight_paused_on', None)
    ap = state.get('active_preset')
    if ap and ap != SUNLIGHT_PRESET_ID:
        state.pop('active_preset', None)
    return state


def _read_sun_elevation(sun = None):
    '''Return sun elevation from HA state, or None when missing/unreadable.'''
    if not sun.get('attributes'):
        sun.get('attributes')
    attrs = { }
    if 'elevation' not in attrs:
        return None
    
    try:
        return float(attrs['elevation'])
    except (TypeError, ValueError):
        return None



def _should_resume_sunlight(state = None, elevation = None, prev = None, *, rising):
    '''Resume auto sunlight after manual off once the sun is actually up (≥ 0°).

    Astronomical dawn (~-18°) is too early — it was turning lights on around 4 AM.
    '''
    if not state.get('sunlight_paused'):
        return False
    if not state.get('sunlight_auto', True):
        return False
    if elevation < CIVIL_SUNRISE_ELEV:
        return False
    if not rising:
        return False
    if prev is not None:
        prev is not None
        if prev < CIVIL_SUNRISE_ELEV:
            prev < CIVIL_SUNRISE_ELEV
    crossed_sunrise = elevation >= CIVIL_SUNRISE_ELEV
    if crossed_sunrise:
        return True
    paused_on = state.get('_sunlight_paused_on')
# WARNING: Decompyle incomplete


def _handle_dawn_transition(state = None, elevation = None, *, rising):
    '''Resume paused sunlight at astronomical dawn.'''
    prev_raw = state.get('_last_sun_elevation')
# WARNING: Decompyle incomplete


def tick_sunlight():
    state = ensure_scene_state()
# WARNING: Decompyle incomplete


def bootstrap_sunlight():
    '''Run once at service start — enables daily auto sunlight.'''
    ensure_scene_state()
    tick_sunlight()

