"""Optional policy packs for model operations (future multi-user ready)."""

from __future__ import annotations

import json
from typing import Any

from jarvis.config import DATA_DIR

_POLICY_FILE = DATA_DIR / "models_product" / "policy.json"

DEFAULT_POLICY = {
    "enabled": False,
    "allow": {
        "switch_models": ["operator", "admin", "*"],
        "edit_defaults": ["operator", "admin", "*"],
        "pull_models": ["operator", "admin", "*"],
        "unload_models": ["operator", "admin", "*"],
    },
}


def load_policy() -> dict[str, Any]:
    try:
        if _POLICY_FILE.is_file():
            data = json.loads(_POLICY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {**DEFAULT_POLICY, **data, "allow": {**DEFAULT_POLICY["allow"], **(data.get("allow") or {})}}
    except Exception:
        pass
    return dict(DEFAULT_POLICY)


def save_policy(policy: dict[str, Any]) -> dict[str, Any]:
    _POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
    merged = {**DEFAULT_POLICY, **(policy or {})}
    _POLICY_FILE.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged


def check_permission(action: str, *, actor: str = "operator") -> dict[str, Any]:
    policy = load_policy()
    if not policy.get("enabled"):
        return {"ok": True, "action": action, "actor": actor, "enforced": False}
    allow = (policy.get("allow") or {}).get(action) or []
    actor_l = (actor or "operator").lower()
    if "*" in allow or actor_l in [str(a).lower() for a in allow]:
        return {"ok": True, "action": action, "actor": actor, "enforced": True}
    return {
        "ok": False,
        "action": action,
        "actor": actor,
        "enforced": True,
        "reason": f"Policy pack denies {action} for {actor}",
    }
