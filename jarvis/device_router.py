"""Unified friendly-name routing — Home Assistant entity or Kasa device."""

from __future__ import annotations

from typing import Any

from jarvis.p2_flags import device_router_enabled, kasa_enabled


def _is_ha_entity_id(target: str) -> bool:
    """True for HA entity ids like light.table_lamp — never a Kasa alias/host."""
    if "." not in target or " " in target:
        return False
    domain, _, obj = target.partition(".")
    if not domain or not obj or "." in obj:
        return False
    return domain.replace("_", "").isalnum() and obj.replace("_", "").isalnum()


def control_device(target: str, action: str, **kwargs) -> tuple[bool, str, str]:
    """Returns (ok, message, backend) where backend is ha|kasa|none."""
    target = (target or "").strip()
    action = (action or "on").strip().lower()
    if not target:
        return False, "No device target specified.", "none"

    ha_entity = _is_ha_entity_id(target)

    if not ha_entity and device_router_enabled() and kasa_enabled():
        from jarvis.kasa_devices import _match_device, control_device as kasa_control

        if _match_device(target):
            ok, msg = kasa_control(
                target,
                action,
                brightness=kwargs.get("brightness"),
                hue=kwargs.get("hue"),
                saturation=kwargs.get("saturation"),
            )
            return ok, msg, "kasa"

    from jarvis.home_assistant import control_entity, ha_enabled

    if ha_enabled():
        try:
            ok, msg = control_entity(
                target,
                action,
                brightness_pct=kwargs.get("brightness_pct") or kwargs.get("brightness"),
                color_name=kwargs.get("color_name"),
                rgb=kwargs.get("rgb"),
                hs=kwargs.get("hs"),
                color_temp_kelvin=kwargs.get("color_temp_kelvin"),
                temperature=kwargs.get("temperature"),
                hvac_mode=kwargs.get("hvac_mode"),
            )
        except Exception as exc:
            ok, msg = False, str(exc)
        if ok:
            return ok, msg, "ha"
        if ha_entity or not device_router_enabled() or not kasa_enabled():
            return ok, msg, "ha"

    if not ha_entity and kasa_enabled():
        from jarvis.kasa_devices import control_device as kasa_control

        ok, msg = kasa_control(
            target,
            action,
            brightness=kwargs.get("brightness"),
            hue=kwargs.get("hue"),
            saturation=kwargs.get("saturation"),
        )
        if ok:
            return ok, msg, "kasa"
        return ok, msg, "kasa"

    return False, "No smart home backend configured (HA or Kasa).", "none"


def list_unified_devices() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        from jarvis.home_assistant import ha_enabled, list_entities

        if ha_enabled():
            for ent in list_entities(limit=80):
                out.append(
                    {
                        "name": ent.get("friendly_name") or ent.get("entity_id"),
                        "id": ent.get("entity_id"),
                        "backend": "ha",
                        "state": ent.get("state"),
                    }
                )
    except Exception:
        pass
    if kasa_enabled():
        from jarvis.kasa_devices import list_devices

        for dev in list_devices():
            out.append(
                {
                    "name": dev.get("alias") or dev.get("host"),
                    "id": dev.get("host"),
                    "backend": "kasa",
                    "state": "on" if dev.get("is_on") else "off",
                }
            )
    return out
