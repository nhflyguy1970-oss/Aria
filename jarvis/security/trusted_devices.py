"""Trusted LAN device list — skip re-auth on known clients."""

from __future__ import annotations

import json
import time
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.p4_flags import trusted_lan_enabled

STORE = DATA_DIR / "security" / "trusted_devices.json"


def _load() -> dict[str, Any]:
    if not STORE.is_file():
        return {"devices": []}
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
        data.setdefault("devices", [])
        return data
    except (json.JSONDecodeError, OSError):
        return {"devices": []}


def _save(data: dict[str, Any]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_trusted() -> list[dict[str, Any]]:
    return list(_load().get("devices") or [])


def is_trusted(device_id: str | None, *, client_ip: str | None) -> bool:
    import hmac

    if not trusted_lan_enabled():
        return False
    did = (device_id or "").strip()
    ip = (client_ip or "").strip()
    if not did or not ip:
        return False
    for row in list_trusted():
        stored_id = str(row.get("id") or "").strip()
        stored_ip = (row.get("ip") or "").strip()
        if not stored_id or not stored_ip:
            continue
        try:
            id_ok = hmac.compare_digest(stored_id, did)
        except (TypeError, ValueError):
            id_ok = False
        if not id_ok:
            continue
        if stored_ip != ip:
            continue
        return True
    return False


def trust_device(
    device_id: str | None, *, label: str = "", client_ip: str | None
) -> dict[str, Any]:
    did = (device_id or "").strip()
    ip = (client_ip or "").strip()
    if not did:
        raise ValueError("device_id required")
    if not ip:
        raise ValueError("client_ip required")
    data = _load()
    devices = data.setdefault("devices", [])
    for row in devices:
        if row.get("id") == did:
            row.update({"ip": ip, "label": label or row.get("label", ""), "last_seen": time.time()})
            _save(data)
            return row
    row = {
        "id": did,
        "ip": ip,
        "label": label or did,
        "trusted_at": time.time(),
        "last_seen": time.time(),
    }
    devices.append(row)
    _save(data)
    return row


def revoke_device(device_id: str | None) -> bool:
    data = _load()
    devices = data.get("devices") or []
    data["devices"] = [d for d in devices if d.get("id") != device_id]
    changed = len(data["devices"]) < len(devices)
    if changed:
        _save(data)
    return changed
