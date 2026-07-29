"""Versioned layout snapshot schema — chrome only; never secrets."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

SCHEMA_VERSION = 1

# Fields Layouts may capture. Never capture secrets / auth / chat bodies.
SNAPSHOT_FIELDS = (
    "view",
    "favorites",
    "sidebarCollapsed",
    "sidebarWidth",
    "dockHidden",
    "statusBarHidden",
    "miniChatHidden",
    "dashboardLayout",
    "theme",
    "accent",
    "panelCollapsed",
    "split",
    "module",
    "model",
    "density",
    "role",
)

SENSITIVE_KEYS = (
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "pin",
)


def empty_snapshot(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": SCHEMA_VERSION,
        "view": "chat",
        "favorites": ["chat", "planner", "workstation", "gallery", "maker"],
        "sidebarCollapsed": None,
        "sidebarWidth": 260,
        "dockHidden": False,
        "statusBarHidden": False,
        "miniChatHidden": False,
        "dashboardLayout": None,
        "theme": "dark",
        "accent": "gold",
        "panelCollapsed": {},
        "split": {"enabled": False, "primary": None, "secondary": None, "ratio": 0.55},
        "module": "",
        "model": "",
        "density": "comfortable",
        "role": "default",
    }
    base.update(overrides)
    return base


def make_snapshot(raw: dict[str, Any] | None = None, *, label: str = "", kind: str = "custom") -> dict[str, Any]:
    raw = raw or {}
    snap = empty_snapshot()
    for key in SNAPSHOT_FIELDS:
        if key in raw:
            snap[key] = deepcopy(raw[key])
    # Compat: accept legacy partial presets
    if "label" in raw and not label:
        label = str(raw.get("label") or "")
    snap["schema_version"] = int(raw.get("schema_version") or SCHEMA_VERSION)
    if label:
        snap["label"] = label
    snap["kind"] = kind
    return migrate_snapshot(snap)


def migrate_snapshot(snap: dict[str, Any]) -> dict[str, Any]:
    out = empty_snapshot()
    out.update({k: deepcopy(v) for k, v in (snap or {}).items() if k not in SENSITIVE_KEYS})
    ver = int(out.get("schema_version") or 0)
    if ver < 1:
        out["schema_version"] = 1
    # Normalize split
    split = out.get("split")
    if not isinstance(split, dict):
        out["split"] = {"enabled": False, "primary": None, "secondary": None, "ratio": 0.55}
    else:
        out["split"] = {
            "enabled": bool(split.get("enabled")),
            "primary": split.get("primary"),
            "secondary": split.get("secondary"),
            "ratio": float(split.get("ratio") or 0.55),
        }
    if not isinstance(out.get("favorites"), list):
        out["favorites"] = list(empty_snapshot()["favorites"])
    if not isinstance(out.get("panelCollapsed"), dict):
        out["panelCollapsed"] = {}
    out["schema_version"] = SCHEMA_VERSION
    # Strip sensitive leftovers
    for bad in list(out.keys()):
        low = str(bad).lower()
        if any(s in low for s in SENSITIVE_KEYS):
            out.pop(bad, None)
    return out


def validate_snapshot(snap: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(snap, dict):
        return ["not_an_object"]
    if "view" not in snap or not str(snap.get("view") or "").strip():
        errors.append("missing_view")
    fav = snap.get("favorites")
    if fav is not None and not isinstance(fav, list):
        errors.append("favorites_not_list")
    width = snap.get("sidebarWidth")
    if width is not None:
        try:
            w = int(width)
            if w < 160 or w > 480:
                errors.append("sidebar_width_out_of_range")
        except Exception:
            errors.append("sidebar_width_invalid")
    for key in snap:
        low = str(key).lower()
        if any(s in low for s in SENSITIVE_KEYS):
            errors.append(f"sensitive_field:{key}")
    ver = snap.get("schema_version")
    try:
        if int(ver or 0) > SCHEMA_VERSION:
            errors.append("schema_too_new")
    except Exception:
        errors.append("schema_version_invalid")
    return errors


def diff_snapshots(before: dict[str, Any] | None, after: dict[str, Any] | None) -> list[dict[str, Any]]:
    before = migrate_snapshot(before or {})
    after = migrate_snapshot(after or {})
    changes: list[dict[str, Any]] = []
    for key in SNAPSHOT_FIELDS:
        if before.get(key) != after.get(key):
            changes.append({"field": key, "from": before.get(key), "to": after.get(key)})
    return changes
