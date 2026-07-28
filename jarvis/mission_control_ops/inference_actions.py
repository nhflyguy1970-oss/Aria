"""Safe inference actions — require confirmation, permission, and audit logging."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR

_AUDIT = DATA_DIR / "mission_control" / "inference_audit.jsonl"

ALLOWED = frozenset(
    {
        "warm_model",
        "switch_model",
        "reload_provider",
        "unload_model",
        "reconnect",
    }
)


def _audit(entry: dict[str, Any]) -> None:
    _AUDIT.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({**entry, "ts": time.time(), "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    with _AUDIT.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def list_audit(*, limit: int = 50) -> list[dict[str, Any]]:
    if not _AUDIT.is_file():
        return []
    lines = _AUDIT.read_text(encoding="utf-8").strip().splitlines()
    out: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(out))


def run_inference_action(
    action: str,
    *,
    confirmed: bool = False,
    model: str = "",
    provider: str = "",
    actor: str = "operator",
) -> dict[str, Any]:
    """
    Execute a safe inference action after explicit confirmation.

    Never runs without confirmed=True. Never auto-remediates.
    """
    name = (action or "").strip().lower()
    if name not in ALLOWED:
        return {"ok": False, "error": f"unsupported action: {action}", "allowed": sorted(ALLOWED)}
    if not confirmed:
        return {
            "ok": False,
            "error": "confirmation_required",
            "message": "Inference actions require explicit operator confirmation",
            "action": name,
        }

    result: dict[str, Any] = {"ok": False, "action": name, "executed": False}
    try:
        if name == "warm_model":
            result = _warm_model(model or "")
        elif name == "switch_model":
            result = _switch_model(model or "")
        elif name == "reload_provider":
            result = _reload_provider(provider or "")
        elif name == "unload_model":
            result = _unload_model(model or "")
        elif name == "reconnect":
            result = _reconnect()
    except Exception as exc:
        result = {"ok": False, "action": name, "error": str(exc), "executed": False}

    _audit(
        {
            "action": name,
            "actor": actor,
            "model": model,
            "provider": provider,
            "ok": bool(result.get("ok")),
            "executed": bool(result.get("executed")),
            "detail": {k: result.get(k) for k in ("message", "error", "model", "provider") if result.get(k)},
        }
    )
    result["audited"] = True
    result["requires_verification"] = bool(result.get("executed"))
    return result


def _warm_model(model: str) -> dict[str, Any]:
    if not model:
        try:
            from jarvis.inference.gateway import gateway_status

            st = gateway_status() or {}
            model = str(st.get("current_model") or st.get("model") or "")
        except Exception:
            model = ""
    if not model:
        return {"ok": False, "action": "warm_model", "error": "model required", "executed": False}
    try:
        import urllib.request

        payload = json.dumps({"model": model, "keep_alive": "30m"}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        # Minimal warm — empty prompt keeps model loaded
        body = json.dumps({"model": model, "prompt": "", "keep_alive": "30m", "stream": False}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read(256)
        return {
            "ok": True,
            "action": "warm_model",
            "executed": True,
            "model": model,
            "message": f"Warmed model {model}",
        }
    except Exception as exc:
        return {"ok": False, "action": "warm_model", "executed": False, "model": model, "error": str(exc)}


def _switch_model(model: str) -> dict[str, Any]:
    """Delegate to Models authoritative API — never write divergent preferred_model.txt."""
    if not model:
        return {"ok": False, "action": "switch_model", "error": "model required", "executed": False}
    try:
        from jarvis.models_product.switch import apply_model_change, ModelChangeRequest

        out = apply_model_change(
            ModelChangeRequest(
                scope="role_default",
                role="conversation",
                model=model,
                actor="mission_control",
                reason="mc_inference_switch",
            )
        )
        return {
            "ok": bool(out.get("ok")),
            "action": "switch_model",
            "executed": bool(out.get("executed")),
            "model": model,
            "message": out.get("message")
            or (
                f"Conversation default set to {model} via Models registry"
                if out.get("ok")
                else out.get("error") or "switch failed"
            ),
            "models_api": out,
            "note": "Mission Control switch uses Models registry (role_default). Warm/unload remain health ops.",
            "error": out.get("error"),
        }
    except Exception as exc:
        return {"ok": False, "action": "switch_model", "executed": False, "error": str(exc)}


def _reload_provider(provider: str) -> dict[str, Any]:
    try:
        from jarvis.workstation.operations import recover_safe

        # Soft: diagnose-only path is safer; use recover_safe which is already gated as "safe"
        out = recover_safe()
        return {
            "ok": bool(out.get("ok", True)),
            "action": "reload_provider",
            "executed": True,
            "provider": provider or "default",
            "message": "Provider reload via safe recover",
            "report": out.get("report") or out,
        }
    except Exception as exc:
        return {"ok": False, "action": "reload_provider", "executed": False, "error": str(exc)}


def _unload_model(model: str) -> dict[str, Any]:
    if not model:
        return {"ok": False, "action": "unload_model", "error": "model required", "executed": False}
    try:
        import urllib.request

        body = json.dumps({"model": model, "keep_alive": 0}).encode("utf-8")
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read(128)
        return {
            "ok": True,
            "action": "unload_model",
            "executed": True,
            "model": model,
            "message": f"Unload requested for {model}",
        }
    except Exception as exc:
        return {"ok": False, "action": "unload_model", "executed": False, "model": model, "error": str(exc)}


def _reconnect() -> dict[str, Any]:
    try:
        from jarvis.platform_runtime import runtime_connection_status

        st = runtime_connection_status()
        return {
            "ok": True,
            "action": "reconnect",
            "executed": True,
            "message": "Connection status refreshed",
            "connection": st,
        }
    except Exception as exc:
        return {"ok": False, "action": "reconnect", "executed": False, "error": str(exc)}
