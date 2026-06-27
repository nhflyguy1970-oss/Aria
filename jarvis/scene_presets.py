"""Named scene bundles — movie mode, etc. (HA scene + device overrides)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.p2_flags import scene_presets_enabled

PRESETS_FILE = DATA_DIR / "scene_presets.json"

DEFAULT_PRESETS: dict[str, Any] = {
    "focus mode": {
        "label": "Focus mode",
        "description": "Turn off all lights — minimize distractions",
        "kasa_all": "off",
        "ha_scene": "",
        "devices": [
            {"target": "light.table_lamp", "action": "off"},
            {"target": "light.geeni_bw413_smart_bulb", "action": "off"},
            {"target": "light.geeni_bw413_smart_bulb_2", "action": "off"},
            {"target": "light.geeni_bw413_smart_bulb_3", "action": "off"},
            {"target": "light.geeni_bw413_smart_bulb_4", "action": "off"},
            {"target": "light.geeni_bw413_smart_bulb_5", "action": "off"},
            {"target": "light.merkury_bw904_smart_bulb", "action": "off"},
            {"target": "light.merkury_bw904_smart_bulb_2", "action": "off"},
        ],
    },
    "relax": {
        "label": "Relax",
        "description": "Dim table lamp to 40%",
        "kasa_all": "dim",
        "kasa_brightness": 40,
        "ha_scene": "",
        "devices": [{"target": "light.table_lamp", "action": "on", "brightness": 40}],
    },
    "movie mode": {
        "label": "Movie mode",
        "ha_scene": "",
        "devices": [{"target": "light.table_lamp", "action": "on", "brightness": 25}],
        "description": "Dim table lamp for movie time — set ha_scene to your HA scene entity if you have one",
    },
    "work mode": {
        "label": "Work mode",
        "ha_scene": "",
        "devices": [
            {"target": "light.table_lamp", "action": "on"},
            {"target": "light.geeni_bw413_smart_bulb", "action": "on"},
            {"target": "light.merkury_bw904_smart_bulb", "action": "on"},
        ],
    },
    "sunlight": {
        "label": "Sunlight",
        "description": "Track sun elevation — gradual dim at dusk, brighten at dawn (all HA lights)",
        "sunlight": True,
        "all_lights": True,
        "transition": 60,
        "ha_scene": "",
        "devices": [],
    },
}


def _load() -> dict[str, Any]:
    if not PRESETS_FILE.is_file():
        return dict(DEFAULT_PRESETS)
    try:
        data = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
        merged = dict(DEFAULT_PRESETS)
        if isinstance(data, dict):
            merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_PRESETS)


def list_presets() -> list[dict[str, Any]]:
    presets = _load()
    out: list[dict[str, Any]] = []
    for key, spec in presets.items():
        if not isinstance(spec, dict):
            continue
        out.append({"id": key, **spec})
    return out


def activate_preset(name: str) -> tuple[bool, str]:
    if not scene_presets_enabled():
        return False, "Scene presets disabled (JARVIS_SCENE_PRESETS=0)"
    key = (name or "").strip().lower()
    presets = _load()
    spec = presets.get(key)
    if not spec:
        for k, v in presets.items():
            if key in k.lower() or k.lower() in key:
                spec = v
                key = k
                break
    if not spec or not isinstance(spec, dict):
        return False, f"Unknown scene preset: {name}"

    if spec.get("sunlight") or key == "sunlight":
        from jarvis.sunlight_scene import activate_sunlight

        return activate_sunlight(spec)

    from jarvis.sunlight_scene import deactivate_sunlight_if_other_preset

    deactivate_sunlight_if_other_preset(key)

    messages: list[str] = []
    failures: list[str] = []
    had_steps = False

    scene = (spec.get("ha_scene") or "").strip()
    if scene:
        had_steps = True
        from jarvis.home_assistant import activate_scene, ha_enabled

        if ha_enabled():
            ok, msg = activate_scene(scene)
            if ok:
                messages.append(msg)
            else:
                failures.append(f"Scene: {msg}")
        else:
            failures.append("Scene: Home Assistant not configured")

    from jarvis.device_router import control_device

    for step in spec.get("devices") or []:
        if not isinstance(step, dict):
            continue
        target = (step.get("target") or "").strip()
        action = (step.get("action") or "on").strip()
        if not target:
            continue
        had_steps = True
        ok, msg, backend = control_device(target, action, brightness=step.get("brightness"))
        if ok:
            messages.append(f"[{backend}] {msg}")
        else:
            failures.append(f"[{backend or 'none'}] {target}: {msg}")

    label = spec.get("label") or key
    kasa_all = (spec.get("kasa_all") or "").strip().lower()
    if kasa_all:
        had_steps = True
        from jarvis.kasa_devices import control_all

        if kasa_all == "off":
            ok, msg = control_all("off")
            if ok:
                messages.append(msg)
            else:
                failures.append(f"Kasa: {msg}")
        elif kasa_all in ("dim", "on"):
            bright = int(spec.get("kasa_brightness") or 40)
            ok, msg = control_all("on", brightness=bright)
            if ok:
                messages.append(msg)
            else:
                failures.append(f"Kasa: {msg}")

    if not had_steps:
        return True, f"Activated **{label}** (no device steps configured yet)."
    if not messages:
        detail = "; ".join(failures) if failures else "All steps failed"
        return False, f"**{label}** failed: {detail}"
    result = f"**{label}:** " + " ".join(messages)
    if failures:
        result += f" Failed: {'; '.join(failures)}"
    return True, result
