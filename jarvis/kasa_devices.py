"""TP-Link Kasa smart plug/bulb control (optional python-kasa)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.p2_flags import kasa_enabled

log = logging.getLogger("jarvis.kasa")
STORE = DATA_DIR / "kasa_devices.json"


def _available() -> bool:
    if not kasa_enabled():
        return False
    try:
        import kasa  # noqa: F401

        return True
    except ImportError:
        return False


def _load_store() -> dict[str, Any]:
    if not STORE.is_file():
        return {"devices": []}
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
        data.setdefault("devices", [])
        return data
    except (json.JSONDecodeError, OSError):
        return {"devices": []}


def _save_store(data: dict[str, Any]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_devices() -> list[dict[str, Any]]:
    return list(_load_store().get("devices") or [])


def _run(coro):
    return asyncio.run(coro)


async def _discover_async(timeout: float = 5.0) -> list[dict[str, Any]]:
    from kasa import Discover

    found = await Discover.discover(timeout=timeout)
    devices: list[dict[str, Any]] = []
    for addr, dev in found.items():
        try:
            await dev.update()
            devices.append(
                {
                    "host": addr,
                    "alias": dev.alias or addr,
                    "model": getattr(dev, "model", "") or "",
                    "is_on": bool(dev.is_on),
                }
            )
        except Exception as exc:
            log.debug("Kasa update failed for %s: %s", addr, exc)
    return devices


def discover(*, timeout: float = 5.0) -> dict[str, Any]:
    if not _available():
        return {
            "ok": False,
            "error": "Kasa disabled or python-kasa not installed (pip install python-kasa)",
        }
    try:
        devices = _run(_discover_async(timeout))
        _save_store({"devices": devices, "discovered": True})
        return {"ok": True, "devices": devices, "count": len(devices)}
    except Exception as exc:
        log.warning("Kasa discover failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def _match_device(target: str) -> dict[str, Any] | None:
    needle = (target or "").strip().lower()
    if not needle:
        return None
    for dev in list_devices():
        alias = (dev.get("alias") or "").lower()
        host = (dev.get("host") or "").lower()
        if needle in alias or alias in needle or needle == host:
            return dev
    return None


async def _control_async(
    host: str,
    action: str,
    *,
    brightness: int | None = None,
    hue: int | None = None,
    saturation: int | None = None,
) -> tuple[bool, str]:
    from kasa import Discover

    dev = await Discover.discover_single(host)
    await dev.update()
    action = (action or "toggle").strip().lower()
    if action == "toggle":
        if dev.is_on:
            await dev.turn_off()
            return True, f"Turned off {dev.alias or host}"
        await dev.turn_on()
        return True, f"Turned on {dev.alias or host}"
    if action == "off":
        await dev.turn_off()
        return True, f"Turned off {dev.alias or host}"
    if action == "on":
        await dev.turn_on()
        if brightness is not None and hasattr(dev, "set_brightness"):
            await dev.set_brightness(int(brightness))
        return True, f"Turned on {dev.alias or host}"
    return False, f"Unknown action: {action}"


def control_device(
    target: str,
    action: str,
    *,
    brightness: int | None = None,
    hue: int | None = None,
    saturation: int | None = None,
) -> tuple[bool, str]:
    if not _available():
        return False, "Kasa not available"
    dev = _match_device(target)
    if not dev:
        return False, f"No Kasa device matches '{target}'"
    try:
        return _run(
            _control_async(
                dev["host"],
                action,
                brightness=brightness,
                hue=hue,
                saturation=saturation,
            )
        )
    except Exception as exc:
        return False, str(exc)


def control_all(action: str, *, brightness: int | None = None) -> tuple[bool, str]:
    if not _available():
        return False, "Kasa not available"
    devices = list_devices()
    if not devices:
        return False, "No Kasa devices — run Discover first"
    ok_count = 0
    errors: list[str] = []
    for dev in devices:
        ok, msg = control_device(dev.get("alias") or dev.get("host") or "", action, brightness=brightness)
        if ok:
            ok_count += 1
        else:
            errors.append(msg)
    if ok_count:
        return True, f"Kasa {action}: {ok_count}/{len(devices)} device(s)"
    return False, errors[0] if errors else "All Kasa controls failed"


def status() -> dict[str, Any]:
    devices = list_devices()
    online = sum(1 for d in devices if d.get("is_on"))
    return {
        "enabled": kasa_enabled(),
        "available": _available(),
        "devices": devices,
        "count": len(devices),
        "online_count": online,
    }
