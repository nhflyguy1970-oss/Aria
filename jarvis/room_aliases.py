"""Room alias map — one friendly name controls multiple devices."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

ALIASES_FILE = DATA_DIR / "room_aliases.json"


def _load() -> dict[str, list[str]]:
    if not ALIASES_FILE.is_file():
        return {}
    try:
        data = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
        raw = data.get("aliases") or {}
        return {str(k).lower(): [str(t) for t in v] for k, v in raw.items()}
    except (json.JSONDecodeError, OSError):
        return {}


def list_aliases() -> dict[str, list[str]]:
    return dict(_load())


def resolve_targets(target: str) -> list[str]:
    """Return device targets for a room alias, or [target] if not an alias."""
    t = (target or "").strip()
    if not t:
        return []
    key = t.lower()
    aliases = _load()
    if key in aliases:
        return list(aliases[key])
    for alias, devices in aliases.items():
        if alias in key or key in alias:
            return list(devices)
    return [t]


def control_alias(target: str, action: str, **kwargs) -> tuple[bool, str, str]:
    """Control all devices in a room alias. Returns aggregate result."""
    from jarvis.device_router import control_device

    targets = resolve_targets(target)
    if len(targets) <= 1:
        return control_device(targets[0] if targets else target, action, **kwargs)

    ok_count = 0
    msgs: list[str] = []
    backend = "none"
    for dev in targets:
        ok, msg, be = control_device(dev, action, **kwargs)
        if ok:
            ok_count += 1
        msgs.append(f"{dev}: {msg}")
        if be != "none":
            backend = be
    summary = f"Room **{target}** — {ok_count}/{len(targets)} ok\n" + "\n".join(f"- {m}" for m in msgs)
    return ok_count > 0, summary, backend
