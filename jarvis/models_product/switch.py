"""Authoritative model change API — one truth for defaults, chat override, and ops."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from jarvis.model_store import (
    CANONICAL_ROLES,
    LEGACY_ROLE_ALIASES,
    ROLE_LABELS,
    canonical_role,
    get_all_settings,
    update_models,
)


# Scopes the change applies to
SCOPE_ROLE_DEFAULT = "role_default"  # persists in model_settings.json
SCOPE_CHAT_OVERRIDE = "chat_override"  # session only
SCOPE_OPS_TEMPORARY = "ops_temporary"  # warm/hint only — does NOT change registry
SCOPE_MAKE_DEFAULT = "make_default"  # chat model → conversation role default


@dataclass
class ModelChangeRequest:
    scope: str
    model: str = ""
    role: str = "conversation"
    roles: dict[str, str] = field(default_factory=dict)
    mode: str = ""  # standard | uncensored | ""
    actor: str = "operator"
    confirmed: bool = True
    reason: str = ""


def apply_model_change(req: ModelChangeRequest | dict[str, Any]) -> dict[str, Any]:
    """
    Single authoritative entry point for model configuration changes.

    Mission Control warm/unload remain health ops and must NOT call this for
    temporary runtime mutations. MC "switch" must use scope=role_default
    (or chat_override) so state never diverges into preferred_model.txt.
    """
    if isinstance(req, dict):
        req = ModelChangeRequest(
            scope=str(req.get("scope") or SCOPE_ROLE_DEFAULT),
            model=str(req.get("model") or ""),
            role=str(req.get("role") or "conversation"),
            roles=dict(req.get("roles") or {}),
            mode=str(req.get("mode") or ""),
            actor=str(req.get("actor") or "operator"),
            confirmed=bool(req.get("confirmed", True)),
            reason=str(req.get("reason") or ""),
        )

    scope = (req.scope or SCOPE_ROLE_DEFAULT).strip().lower()
    if scope == SCOPE_OPS_TEMPORARY:
        return {
            "ok": False,
            "error": "ops_temporary_not_for_registry",
            "message": (
                "Operational temporary actions (warm/unload) belong to Mission Control "
                "and do not change the Models registry. Use role_default or chat_override."
            ),
            "scope": scope,
        }

    from jarvis.models_product.policy import check_permission

    perm = check_permission("switch_models" if scope != SCOPE_MAKE_DEFAULT else "edit_defaults", actor=req.actor)
    if not perm.get("ok"):
        return {"ok": False, "error": "permission_denied", "message": perm.get("reason"), "policy": perm}

    try:
        if scope == SCOPE_CHAT_OVERRIDE:
            out = _set_chat_override(req.model)
        elif scope == SCOPE_MAKE_DEFAULT:
            out = _make_default(req.model, mode=req.mode)
        elif scope == SCOPE_ROLE_DEFAULT:
            if req.roles:
                out = _set_roles(req.roles, mode=req.mode)
            else:
                out = _set_role(req.role, req.model, mode=req.mode)
        else:
            return {"ok": False, "error": f"unknown_scope:{scope}", "allowed": [
                SCOPE_ROLE_DEFAULT, SCOPE_CHAT_OVERRIDE, SCOPE_MAKE_DEFAULT
            ]}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "scope": scope}

    out["scope"] = scope
    out["actor"] = req.actor
    out["ts"] = time.time()
    out["terminology"] = {
        "model": "A specific runnable weights tag (e.g. qwen2.5:7b)",
        "role": "A job Aria assigns a model to (conversation, coding, …)",
        "provider": "The runtime that serves models (Ollama, LiteLLM, cloud)",
        "gateway": "Routing layer choosing Ollama vs LiteLLM",
        "registry": "Persistent role→model map (Models Home)",
        "profile": "standard vs uncensored model bank",
    }
    try:
        from jarvis.models_product.activity_bridge import emit_model_event

        emit_model_event(
            "model_switched" if scope != SCOPE_MAKE_DEFAULT else "role_changed",
            message=out.get("message") or f"{scope}: {req.model or req.roles}",
            detail=out,
        )
    except Exception:
        pass
    return out


def _set_chat_override(model: str) -> dict[str, Any]:
    name = (model or "").strip()
    try:
        from jarvis.gui import server as gui_server

        assistant = getattr(gui_server, "assistant", None)
        if assistant is not None and hasattr(assistant, "session"):
            assistant.session.note_chat_model(name)
            return {
                "ok": True,
                "executed": True,
                "chat_model": name,
                "effective": name or getattr(assistant.session, "effective_chat_model", lambda: "")(),
                "message": f"Chat override: {name or 'default'}",
                "persistent": False,
            }
    except Exception:
        pass
    # Persist soft override file for non-GUI contexts (still not role registry)
    from jarvis.config import DATA_DIR

    path = DATA_DIR / "models_product" / "chat_override.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    if name:
        path.write_text(name + "\n", encoding="utf-8")
    elif path.is_file():
        path.unlink()
    return {
        "ok": True,
        "executed": True,
        "chat_model": name,
        "message": f"Chat override stored: {name or 'cleared'}",
        "persistent": False,
        "note": "Session override when GUI assistant unavailable",
    }


def _set_role(role: str, model: str, *, mode: str = "") -> dict[str, Any]:
    model = (model or "").strip()
    if not model:
        raise ValueError("model required for role_default")
    role_key = canonical_role(role)
    if role_key not in CANONICAL_ROLES and role_key not in LEGACY_ROLE_ALIASES:
        # allow legacy keys
        if role not in LEGACY_ROLE_ALIASES and role not in CANONICAL_ROLES:
            raise ValueError(f"unknown role: {role}")
    mode_key = mode or ""
    if not mode_key:
        from jarvis.config import is_uncensored

        mode_key = "uncensored" if is_uncensored() else "standard"
    settings = update_models(mode_key, {role_key: model, role: model})
    label = ROLE_LABELS.get(role_key, role_key)
    return {
        "ok": True,
        "executed": True,
        "role": role_key,
        "model": model,
        "mode": mode_key,
        "settings": {"active": settings.get("active"), "mode": settings.get("mode")},
        "message": f"Default for {label} → {model}",
        "persistent": True,
        "changed": {role_key: model},
    }


def _set_roles(roles: dict[str, str], *, mode: str = "") -> dict[str, Any]:
    cleaned = {canonical_role(k): str(v).strip() for k, v in roles.items() if v}
    if not cleaned:
        raise ValueError("roles required")
    mode_key = mode or ""
    if not mode_key:
        from jarvis.config import is_uncensored

        mode_key = "uncensored" if is_uncensored() else "standard"
    settings = update_models(mode_key, cleaned)
    return {
        "ok": True,
        "executed": True,
        "mode": mode_key,
        "changed": cleaned,
        "settings": {"active": settings.get("active"), "mode": settings.get("mode")},
        "message": f"Updated {len(cleaned)} role assignment(s)",
        "persistent": True,
    }


def _make_default(model: str, *, mode: str = "") -> dict[str, Any]:
    model = (model or "").strip()
    if not model:
        raise ValueError("model required")
    # Clear chat override so default takes effect cleanly
    _set_chat_override("")
    out = _set_role("conversation", model, mode=mode)
    out["message"] = f"Made {model} the default Chat (conversation) model"
    out["make_default"] = True
    return out


def describe_switch_contract() -> dict[str, Any]:
    return {
        "product": "models",
        "authoritative_api": "POST /api/models/switch",
        "scopes": {
            SCOPE_ROLE_DEFAULT: "Persists role→model in registry (Models owns)",
            SCOPE_CHAT_OVERRIDE: "Session-only chat model (Chat uses; Models records)",
            SCOPE_MAKE_DEFAULT: "Promote chat model to conversation default",
            SCOPE_OPS_TEMPORARY: "Rejected here — use Mission Control warm/unload",
        },
        "mission_control": {
            "warm_model": "Health op — does not change registry",
            "unload_model": "Health op — does not change registry",
            "switch_model": "Must call /api/models/switch with role_default",
        },
    }
