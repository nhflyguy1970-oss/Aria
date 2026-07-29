"""Persistent enable/disable, lazy, quarantine, and trust overrides."""

from __future__ import annotations

import json
import time
from typing import Any

from jarvis.config import DATA_DIR

POLICY_FILE = DATA_DIR / "capabilities_product" / "policy.json"

DEFAULT_POLICY: dict[str, Any] = {
    "version": 1,
    "entries": {},  # id -> {enabled, trust_override, lazy, quarantined, fail_count, acknowledged_at}
    "third_party_default_enabled": False,
    "built_in_default_enabled": True,
    "quarantine_threshold": 3,
}


def _ensure_dir() -> None:
    POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_policy() -> dict[str, Any]:
    data = dict(DEFAULT_POLICY)
    data["entries"] = {}
    if POLICY_FILE.is_file():
        try:
            raw = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data.update({k: v for k, v in raw.items() if k != "entries" and v is not None})
                entries = raw.get("entries") or {}
                if isinstance(entries, dict):
                    data["entries"] = {str(k): dict(v) for k, v in entries.items() if isinstance(v, dict)}
        except (json.JSONDecodeError, OSError):
            pass
    data.setdefault("entries", {})
    data["third_party_default_enabled"] = bool(data.get("third_party_default_enabled", False))
    data["built_in_default_enabled"] = bool(data.get("built_in_default_enabled", True))
    try:
        data["quarantine_threshold"] = max(1, int(data.get("quarantine_threshold") or 3))
    except (TypeError, ValueError):
        data["quarantine_threshold"] = 3
    return data


def save_policy(policy: dict[str, Any] | None = None) -> dict[str, Any]:
    data = load_policy() if policy is None else policy
    _ensure_dir()
    POLICY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def _entry(cap_id: str) -> dict[str, Any]:
    policy = load_policy()
    return dict(policy.get("entries", {}).get(cap_id) or {})


def _set_entry(cap_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    policy = load_policy()
    entries = dict(policy.get("entries") or {})
    cur = dict(entries.get(cap_id) or {})
    cur.update({k: v for k, v in patch.items() if v is not None})
    cur["updated_at"] = time.time()
    entries[cap_id] = cur
    policy["entries"] = entries
    save_policy(policy)
    return cur


def default_enabled_for_trust(trust: str) -> bool:
    policy = load_policy()
    if trust in ("built_in", "first_party"):
        return bool(policy.get("built_in_default_enabled", True))
    return bool(policy.get("third_party_default_enabled", False))


def is_enabled(cap_id: str, *, trust: str = "unknown", default: bool | None = None) -> bool:
    entry = _entry(cap_id)
    if entry.get("quarantined"):
        return False
    if "enabled" in entry:
        return bool(entry["enabled"])
    if default is not None:
        return bool(default)
    return default_enabled_for_trust(trust)


def set_enabled(cap_id: str, enabled: bool) -> dict[str, Any]:
    return _set_entry(cap_id, {"enabled": bool(enabled), "quarantined": False if enabled else None})


def is_lazy(cap_id: str, default: bool = False) -> bool:
    entry = _entry(cap_id)
    if "lazy" in entry:
        return bool(entry["lazy"])
    return default


def set_lazy(cap_id: str, lazy: bool) -> dict[str, Any]:
    return _set_entry(cap_id, {"lazy": bool(lazy)})


def trust_override(cap_id: str) -> str | None:
    entry = _entry(cap_id)
    t = entry.get("trust_override")
    return str(t) if t else None


def set_trust_override(cap_id: str, trust: str | None) -> dict[str, Any]:
    return _set_entry(cap_id, {"trust_override": trust})


def is_quarantined(cap_id: str) -> bool:
    return bool(_entry(cap_id).get("quarantined"))


def record_failure(cap_id: str, error: str = "") -> dict[str, Any]:
    policy = load_policy()
    entries = dict(policy.get("entries") or {})
    cur = dict(entries.get(cap_id) or {})
    count = int(cur.get("fail_count") or 0) + 1
    cur["fail_count"] = count
    cur["last_error"] = (error or "")[:500]
    cur["last_fail_at"] = time.time()
    threshold = int(policy.get("quarantine_threshold") or 3)
    if count >= threshold:
        cur["quarantined"] = True
        cur["enabled"] = False
    entries[cap_id] = cur
    policy["entries"] = entries
    save_policy(policy)
    return cur


def acknowledge_quarantine(cap_id: str, *, reenable: bool = False) -> dict[str, Any]:
    patch: dict[str, Any] = {
        "quarantined": False,
        "fail_count": 0,
        "acknowledged_at": time.time(),
        "last_error": "",
    }
    if reenable:
        patch["enabled"] = True
    return _set_entry(cap_id, patch)


def get_entry(cap_id: str) -> dict[str, Any]:
    return _entry(cap_id)


def export_policy() -> dict[str, Any]:
    return load_policy()


def import_policy(data: dict[str, Any], *, merge: bool = True) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("policy must be an object")
    if merge:
        cur = load_policy()
        entries = dict(cur.get("entries") or {})
        incoming = data.get("entries") or {}
        if isinstance(incoming, dict):
            for k, v in incoming.items():
                if isinstance(v, dict):
                    entries[str(k)] = {**(entries.get(str(k)) or {}), **v}
        cur["entries"] = entries
        for key in ("third_party_default_enabled", "built_in_default_enabled", "quarantine_threshold"):
            if key in data:
                cur[key] = data[key]
        return save_policy(cur)
    return save_policy({**DEFAULT_POLICY, **data, "entries": data.get("entries") or {}})
