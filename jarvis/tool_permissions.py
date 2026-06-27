"""Per-tool confirmation settings (always | ask | never)."""

from __future__ import annotations

import json
import uuid
from typing import Any, Literal

from jarvis.config import DATA_DIR
from jarvis.feature_flags import tool_permissions_enabled

Permission = Literal["always", "ask", "never"]

PERM_FILE = DATA_DIR / "tool_permissions.json"
PENDING_FILE = DATA_DIR / "pending_tool_confirms.json"

DEFAULTS: dict[str, Permission] = {
    "write_file": "ask",
    "shell": "ask",
    "web_agent": "ask",
    "cad": "ask",
    "ha_control": "never",
    "upgrade_apply": "ask",
}


def _load_raw() -> dict[str, Any]:
    if not PERM_FILE.exists():
        return {}
    try:
        return json.loads(PERM_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_raw(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PERM_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_permissions() -> dict[str, str]:
    raw = _load_raw()
    out = dict(DEFAULTS)
    tools = raw.get("tools") or {}
    for key, val in tools.items():
        if val in ("always", "ask", "never"):
            out[key] = val
    return out


def set_permission(tool: str, mode: str) -> dict[str, str]:
    tool = (tool or "").strip()
    mode = (mode or "").strip().lower()
    if mode not in ("always", "ask", "never"):
        raise ValueError("mode must be always, ask, or never")
    raw = _load_raw()
    tools = dict(raw.get("tools") or {})
    tools[tool] = mode
    raw["tools"] = tools
    _save_raw(raw)
    return get_permissions()


def permission_for(tool: str) -> Permission:
    if not tool_permissions_enabled():
        return "always"
    return get_permissions().get(tool, DEFAULTS.get(tool, "ask"))  # type: ignore[return-value]


def needs_confirmation(tool: str) -> bool:
    return permission_for(tool) == "ask"


def _load_pending() -> dict[str, Any]:
    if not PENDING_FILE.exists():
        return {}
    try:
        return json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_pending(data: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PENDING_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_pending(tool: str, action: str, params: dict, message: str) -> str:
    confirm_id = uuid.uuid4().hex[:12]
    pending = _load_pending()
    pending[confirm_id] = {
        "tool": tool,
        "action": action,
        "params": params,
        "message": message[:500],
    }
    _save_pending(pending)
    return confirm_id


def pop_pending(confirm_id: str) -> dict[str, Any] | None:
    pending = _load_pending()
    row = pending.pop(confirm_id, None)
    _save_pending(pending)
    return row


def list_pending() -> list[dict[str, Any]]:
    return [{"id": k, **v} for k, v in _load_pending().items()]
