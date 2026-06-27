"""Home Assistant light color, brightness, and daylight helpers."""

from __future__ import annotations

import math
import re
from typing import Any

# Sun elevation thresholds (degrees). HA `sun.sun` uses home latitude/longitude.
ASTRONOMICAL_TWILIGHT_ELEV = -18.0
NAUTICAL_TWILIGHT_ELEV = -12.0
NIGHT_OFF_ELEV = NAUTICAL_TWILIGHT_ELEV
CIVIL_SUNRISE_ELEV = 0.0

COLOR_PRESETS: dict[str, dict[str, Any]] = {
    "red": {"rgb_color": [255, 0, 0]},
    "green": {"rgb_color": [0, 255, 0]},
    "blue": {"rgb_color": [0, 0, 255]},
    "cyan": {"rgb_color": [0, 255, 255]},
    "magenta": {"rgb_color": [255, 0, 255]},
    "yellow": {"rgb_color": [255, 255, 0]},
    "orange": {"rgb_color": [255, 140, 0]},
    "purple": {"hs_color": [275, 100]},
    "violet": {"hs_color": [275, 100]},
    "uv": {"hs_color": [275, 100]},
    "funky": {"hs_color": [275, 100]},
    "pink": {"hs_color": [330, 70]},
    "warm": {"color_temp_kelvin": 2700},
    "warm white": {"color_temp_kelvin": 2700},
    "cool": {"color_temp_kelvin": 5000},
    "cool white": {"color_temp_kelvin": 5000},
    "daylight": {"color_temp_kelvin": 4500},
    "movie": {"color_temp_kelvin": 2200, "brightness_pct": 12},
}


def resolve_color_name(name: str | None) -> dict[str, Any]:
    key = (name or "").strip().lower()
    if not key:
        return {}
    return dict(COLOR_PRESETS.get(key, {}))


def _pct_to_brightness(pct: int) -> int:
    return max(1, min(255, int(round(max(0, min(100, pct)) * 255 / 100))))


def build_light_service_data(
    entity_id: str,
    *,
    action: str = "on",
    brightness_pct: int | None = None,
    rgb: list[int] | None = None,
    hs: list[float] | None = None,
    color_temp_kelvin: int | None = None,
    color_name: str | None = None,
    transition: float | None = None,
) -> tuple[str, dict[str, Any]]:
    """Return (service_name, data) for homeassistant light domain."""
    eid = (entity_id or "").strip()
    act = (action or "on").strip().lower()
    if act == "off":
        payload: dict[str, Any] = {"entity_id": eid}
        if transition is not None:
            payload["transition"] = max(0.0, float(transition))
        return "turn_off", payload
    if act == "toggle":
        return "toggle", {"entity_id": eid}

    data: dict[str, Any] = {"entity_id": eid}
    named = resolve_color_name(color_name)
    if rgb:
        data["rgb_color"] = [max(0, min(255, int(x))) for x in rgb[:3]]
    elif hs:
        data["hs_color"] = [float(hs[0]), float(hs[1])]
    elif named.get("rgb_color"):
        data["rgb_color"] = named["rgb_color"]
    elif named.get("hs_color"):
        data["hs_color"] = named["hs_color"]

    ct = color_temp_kelvin or named.get("color_temp_kelvin")
    if ct is not None:
        data["color_temp_kelvin"] = max(2000, min(6500, int(ct)))

    bp = brightness_pct if brightness_pct is not None else named.get("brightness_pct")
    if bp is not None:
        bp = max(1, min(100, int(bp)))
        data["brightness_pct"] = bp
        data["brightness"] = _pct_to_brightness(bp)

    if transition is not None:
        data["transition"] = max(0.0, float(transition))
    return "turn_on", data


def set_lights(
    entity_ids: list[str],
    *,
    action: str = "on",
    brightness_pct: int | None = None,
    rgb: list[int] | None = None,
    hs: list[float] | None = None,
    color_temp_kelvin: int | None = None,
    color_name: str | None = None,
    transition: float | None = None,
) -> tuple[bool, str]:
    """Apply the same light command to many entities in one HA service call."""
    from jarvis.home_assistant import call_service

    ids = [e.strip() for e in entity_ids if (e or "").strip().startswith("light.")]
    if not ids:
        return False, "No light entities"
    service, data = build_light_service_data(
        ids[0],
        action=action,
        brightness_pct=brightness_pct,
        rgb=rgb,
        hs=hs,
        color_temp_kelvin=color_temp_kelvin,
        color_name=color_name,
        transition=transition,
    )
    data["entity_id"] = ids
    try:
        call_service("light", service, data)
    except Exception as exc:
        return False, str(exc)
    return True, f"updated {len(ids)} light(s)"


def set_light(
    entity_id: str,
    *,
    action: str = "on",
    brightness_pct: int | None = None,
    rgb: list[int] | None = None,
    hs: list[float] | None = None,
    color_temp_kelvin: int | None = None,
    color_name: str | None = None,
    transition: float | None = None,
) -> tuple[bool, str]:
    from jarvis.home_assistant import call_service, get_state

    eid = (entity_id or "").strip()
    if not eid.startswith("light."):
        return False, f"{eid} is not a light entity"
    service, data = build_light_service_data(
        eid,
        action=action,
        brightness_pct=brightness_pct,
        rgb=rgb,
        hs=hs,
        color_temp_kelvin=color_temp_kelvin,
        color_name=color_name,
        transition=transition,
    )
    try:
        call_service("light", service, data)
    except Exception as exc:
        return False, str(exc)
    st = get_state(eid) or {}
    name = (st.get("attributes") or {}).get("friendly_name") or eid
    parts = [f"**{name}** (`{eid}`)"]
    if service == "turn_on":
        if data.get("brightness_pct") is not None:
            parts.append(f"{data['brightness_pct']}%")
        if data.get("color_temp_kelvin"):
            parts.append(f"{data['color_temp_kelvin']}K")
        if data.get("rgb_color"):
            parts.append(f"RGB {data['rgb_color']}")
        if data.get("hs_color"):
            parts.append(f"HS {data['hs_color']}")
        if color_name:
            parts.append(str(color_name))
    return True, " — ".join(parts)


def _sun_tint_for_elevation(elevation: float) -> dict[str, Any]:
    if elevation < CIVIL_SUNRISE_ELEV:
        return {"kelvin": 2700, "hs": None, "label": "warm dawn/dusk"}
    if elevation < 20:
        t = elevation / 20.0
        return {"kelvin": int(2700 + t * 800), "hs": None, "label": "morning/evening warm"}
    if elevation < 45:
        t = (elevation - 20) / 25.0
        return {"kelvin": int(3500 + t * 1500), "hs": None, "label": "daylight warm"}
    return {"kelvin": 5000, "hs": None, "label": "daylight"}


def daylight_levels_from_sun(sun_state: dict | None = None) -> dict[str, Any]:
    """Map sun elevation to brightness %, color temp, and phase labels."""
    elevation = 0.0
    rising = True
    if sun_state:
        attrs = sun_state.get("attributes") or {}
        elevation = float(attrs.get("elevation") or 0)
        rising = attrs.get("rising", True) is not False
    else:
        try:
            from jarvis.home_assistant import get_state

            st = get_state("sun.sun")
            if st:
                attrs = st.get("attributes") or {}
                elevation = float(attrs.get("elevation") or 0)
                rising = attrs.get("rising", True) is not False
        except Exception:
            elevation = 30.0

    tint = _sun_tint_for_elevation(elevation)

    if elevation <= ASTRONOMICAL_TWILIGHT_ELEV:
        return {
            "brightness_pct": 0,
            "color_temp_kelvin": 2700,
            "hs": None,
            "light_tint": "night",
            "elevation": round(elevation, 1),
            "phase": "night",
            "in_window": False,
            "rising": rising,
        }

    if elevation <= NAUTICAL_TWILIGHT_ELEV:
        t = (elevation - ASTRONOMICAL_TWILIGHT_ELEV) / (NAUTICAL_TWILIGHT_ELEV - ASTRONOMICAL_TWILIGHT_ELEV)
        bright = int(max(0, min(8, round(t * 8))))
        phase = "astronomical twilight"
    elif elevation <= CIVIL_SUNRISE_ELEV:
        t = (elevation - NAUTICAL_TWILIGHT_ELEV) / (CIVIL_SUNRISE_ELEV - NAUTICAL_TWILIGHT_ELEV)
        bright = int(8 + t * 22)
        phase = "nautical twilight" if elevation < -6 else "civil twilight"
    elif elevation < 45:
        t = elevation / 45.0
        bright = int(30 + t * 65)
        phase = "day"
    else:
        bright = int(90 + min(10, (elevation - 45) / 3))
        phase = "day"

    return {
        "brightness_pct": max(0, min(100, bright)),
        "color_temp_kelvin": tint["kelvin"],
        "hs": tint.get("hs"),
        "light_tint": tint["label"],
        "elevation": round(elevation, 1),
        "phase": phase,
        "in_window": elevation > ASTRONOMICAL_TWILIGHT_ELEV,
        "rising": rising,
    }


_COLOR_WORDS = "|".join(re.escape(k) for k in sorted(COLOR_PRESETS, key=len, reverse=True))


def parse_color_control(message: str) -> dict[str, Any] | None:
    """Parse 'set table lamp to blue', 'dim lamp 30%', 'make family room uv'."""
    text = (message or "").strip()
    if not text:
        return None

    m = re.match(
        rf"^(?:please\s+)?(?:set|make|change)\s+(?:the\s+)?(.+?)\s+to\s+({_COLOR_WORDS})(?:\s+light)?\.?$",
        text,
        re.I,
    )
    if m:
        return {"action": "on", "target": m.group(1).strip(), "color_name": m.group(2).lower()}

    m = re.match(
        r"^(?:please\s+)?(?:set|make|dim)\s+(?:the\s+)?(.+?)\s+(?:to\s+)?(\d{1,3})\s*%\.?$",
        text,
        re.I,
    )
    if m:
        return {
            "action": "on" if int(m.group(2)) > 0 else "off",
            "target": m.group(1).strip(),
            "brightness_pct": int(m.group(2)),
        }

    m = re.match(
        rf"^(?:please\s+)?(?:set|make)\s+(?:the\s+)?(.+?)\s+({_COLOR_WORDS})\.?$",
        text,
        re.I,
    )
    if m:
        return {"action": "on", "target": m.group(1).strip(), "color_name": m.group(2).lower()}

    return None
