"""Security & presence HTTP API."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


def _session_token(request: Request) -> str | None:
    return (request.headers.get("X-Jarvis-Session") or "").strip() or None


def register_routes(app, assistant) -> None:
    @app.get("/api/security/lock/status")
    def security_lock_status(request: Request):
        from jarvis.security.owner import get_owner_security
        from jarvis.security.pin_lock import lock_status

        pin = lock_status(session_token=_session_token(request))
        return get_owner_security().house_lock_status(
            session_token=_session_token(request),
            pin_status=pin,
        )

    @app.post("/api/security/lock")
    async def security_lock(request: Request):
        from jarvis.p4_flags import pin_lock_enabled
        from jarvis.security.owner import get_owner_security
        from jarvis.security.pin_lock import pin_configured, revoke_all_sessions

        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        owner = get_owner_security()
        if owner.vault.exists():
            hard = bool(body.get("hard", True))
            return owner.lock(hard=hard)
        if not pin_lock_enabled():
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "locked": False,
                    "message": "PIN lock is off — set JARVIS_PIN_LOCK=1 before locking.",
                },
            )
        if not pin_configured():
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "locked": False,
                    "message": "Set a PIN before locking Aria.",
                },
            )
        revoked = revoke_all_sessions()
        return {"ok": True, "locked": True, "revoked_sessions": revoked}

    @app.post("/api/security/unlock")
    async def security_unlock(request: Request):
        from jarvis.auth import client_ip
        from jarvis.security.owner import get_owner_security
        from jarvis.security.pin_lock import create_session, verify_pin
        from jarvis.security.trusted_devices import trust_device

        body = await request.json()
        owner = get_owner_security()
        if owner.vault.exists():
            master = str(body.get("master_password") or body.get("password") or "").strip()
            pin = str(body.get("pin") or "").strip()
            if master:
                out = owner.unlock(master)
                if not out.get("ok"):
                    return JSONResponse(status_code=403, content=out)
                return out
            if pin:
                out = owner.soft_unlock_with_pin(pin)
                if not out.get("ok"):
                    return JSONResponse(status_code=403, content=out)
                return out
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": "Enter your Aria Master Password"},
            )
        pin = str(body.get("pin") or "").strip()
        if not verify_pin(pin):
            return JSONResponse(status_code=403, content={"ok": False, "message": "Invalid PIN"})
        device_id = str(body.get("device_id") or "").strip()
        token = create_session(device_id=device_id)
        if body.get("trust_device") and device_id:
            trust_device(
                device_id, client_ip=client_ip(request), label=str(body.get("label") or "")
            )
        return {"ok": True, "session_token": token}

    @app.post("/api/security/pin/setup")
    async def security_pin_setup(request: Request):
        from jarvis.auth import api_key_enabled, check_key
        from jarvis.security.pin_lock import pin_configured, set_pin, verify_pin

        if api_key_enabled() and not check_key(request):
            return JSONResponse(
                status_code=401, content={"ok": False, "message": "API key required"}
            )
        body = await request.json()
        pin = str(body.get("pin") or "")
        # First-time setup: require API key when LAN key is configured (checked above).
        # Re-setup / overwrite: require current PIN.
        if pin_configured():
            current = str(body.get("current_pin") or body.get("old_pin") or "")
            if not verify_pin(current):
                return JSONResponse(
                    status_code=403,
                    content={"ok": False, "message": "current_pin required to change PIN"},
                )
        try:
            return set_pin(pin)
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})

    @app.post("/api/security/session/touch")
    def security_session_touch(request: Request):
        from jarvis.security.pin_lock import touch_session

        token = _session_token(request)
        return {"ok": touch_session(token)}

    @app.get("/api/security/tools/status")
    def security_tools_status():
        from jarvis.security.tools_status import tools_status

        return {"ok": True, "tools": tools_status()}

    @app.get("/api/security/brain-mode")
    def security_brain_mode():
        from jarvis.security.brain_mode import brain_mode_status

        return {"ok": True, **brain_mode_status()}

    @app.get("/api/security/trusted-devices")
    def security_trusted_devices():
        from jarvis.security.trusted_devices import list_trusted

        return {"ok": True, "devices": list_trusted()}

    @app.post("/api/security/trusted-devices/{device_id}/revoke")
    def security_trusted_revoke(device_id: str):
        from jarvis.security.trusted_devices import revoke_device

        return {"ok": revoke_device(device_id)}

    @app.get("/api/security/desktop-shells")
    def security_desktop_shells():
        try:
            from jarvis.electron_shell import status as electron_status
        except Exception:
            electron_status = lambda: {"available": False}
        try:
            from jarvis.gui_launcher import gui_mode
        except Exception:
            gui_mode = lambda: "web"
        try:
            from jarvis.pyside_shell import status as pyside_status
        except Exception:
            pyside_status = lambda: {"available": False}
        return {
            "ok": True,
            "mode": gui_mode(),
            "electron": electron_status(),
            "pyside": pyside_status(),
        }

    @app.get("/api/security/cloud-live")
    def security_cloud_live():
        from jarvis.cloud_live_voice import cloud_live_status

        return {"ok": True, **cloud_live_status()}

    @app.get("/api/security/gestures/status")
    def security_gestures_status():
        import json
        import os

        from jarvis.config import DATA_DIR
        from jarvis.p4_flags import floating_panels_enabled, gestures_enabled
        from jarvis.p5_flags import cpu_gestures_enabled

        path = DATA_DIR / "security" / "gestures.json"
        saved = {"mode": "off", "calibration": {}}
        if path.is_file():
            try:
                saved = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        default_mode = "pinch" if gestures_enabled() else "off"
        return {
            "ok": True,
            "gestures_enabled": gestures_enabled(),
            "floating_panels": floating_panels_enabled(),
            "cpu_gestures": cpu_gestures_enabled(),
            "mode": saved.get("mode") or default_mode,
            "calibration": saved.get("calibration") or {},
            "sensitivity": float(os.getenv("JARVIS_GESTURE_SENSITIVITY", "1.35")),
        }

    @app.get("/api/security/gestures/settings")
    def security_gestures_settings_get():
        import json

        from jarvis.config import DATA_DIR

        path = DATA_DIR / "security" / "gestures.json"
        if not path.is_file():
            return {"ok": True, "mode": "off", "calibration": {}}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {"ok": True, **data}
        except (json.JSONDecodeError, OSError):
            return {"ok": True, "mode": "off", "calibration": {}}

    @app.post("/api/security/gestures/settings")
    async def security_gestures_settings_set(request: Request):
        import json

        from jarvis.config import DATA_DIR

        body = await request.json()
        path = DATA_DIR / "security" / "gestures.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body, indent=2), encoding="utf-8")
        return {"ok": True}

    @app.get("/api/security/face/status")
    def security_face_status():
        from jarvis.security.face_auth import face_status

        return {"ok": True, **face_status()}

    @app.post("/api/security/face/enroll")
    async def security_face_enroll(request: Request):
        from jarvis.security.face_auth import enroll_face

        body = await request.json()
        image = body.get("image") or body.get("image_b64") or body.get("data")
        return enroll_face(str(image or ""))

    @app.post("/api/security/face/verify")
    async def security_face_verify(request: Request):
        from jarvis.security.face_auth import verify_face

        body = await request.json()
        image = body.get("image") or body.get("image_b64") or body.get("data")
        threshold = float(body.get("threshold") or 0.75)
        return verify_face(str(image or ""), threshold=threshold)

    @app.get("/api/presence/status")
    @app.get("/api/presence")
    def presence_status():
        """Presence/gesture backend status (camera + MediaPipe run client-side)."""
        from jarvis.p4_flags import floating_panels_enabled, gestures_enabled
        from jarvis.p5_flags import cpu_gestures_enabled
        from jarvis.security.face_auth import face_status

        face = face_status()
        return {
            "ok": True,
            "gestures_enabled": gestures_enabled(),
            "floating_panels": floating_panels_enabled(),
            "cpu_gestures": cpu_gestures_enabled(),
            "face_auth": face,
            "camera_required": True,
            "backend": "client",
        }

    # --- Owner Security Vault (M1 foundation) ---

    @app.get("/api/owner-security/status")
    def owner_security_status(request: Request):
        from jarvis.security.owner import get_owner_security

        return get_owner_security().status(session_token=_session_token(request))

    @app.get("/api/owner-security/capabilities")
    def owner_security_capabilities():
        from jarvis.security.owner import get_owner_security

        return {"ok": True, "capabilities": get_owner_security().catalog()}

    @app.post("/api/owner-security/setup")
    async def owner_security_setup(request: Request):
        from jarvis.security.owner import get_owner_security

        body = await request.json()
        return get_owner_security().setup(
            str(body.get("master_password") or ""),
            confirm_password=body.get("confirm_password"),
        )

    @app.post("/api/owner-security/recovery/acknowledge")
    async def owner_security_recovery_ack(request: Request):
        from jarvis.security.owner import get_owner_security

        body = await request.json()
        return get_owner_security().acknowledge_recovery(stored=bool(body.get("stored")))

    @app.post("/api/owner-security/unlock")
    async def owner_security_unlock(request: Request):
        from jarvis.security.owner import get_owner_security

        body = await request.json()
        return get_owner_security().unlock(str(body.get("master_password") or ""))

    @app.post("/api/owner-security/unlock/pin")
    async def owner_security_unlock_pin(request: Request):
        from jarvis.security.owner import get_owner_security

        body = await request.json()
        return get_owner_security().soft_unlock_with_pin(str(body.get("pin") or ""))

    @app.post("/api/owner-security/lock")
    async def owner_security_lock(request: Request):
        from jarvis.security.owner import get_owner_security

        body = {}
        try:
            body = await request.json()
        except Exception:
            body = {}
        hard = bool(body.get("hard", True))
        return get_owner_security().lock(hard=hard)

    @app.post("/api/owner-security/recover")
    async def owner_security_recover(request: Request):
        from jarvis.security.owner import get_owner_security

        body = await request.json()
        return get_owner_security().recover(
            str(body.get("recovery_key") or ""),
            str(body.get("new_master_password") or ""),
        )

    @app.post("/api/owner-security/password/change")
    async def owner_security_password_change(request: Request):
        from jarvis.security.owner import get_owner_security

        body = await request.json()
        return get_owner_security().change_master_password(
            str(body.get("current_password") or ""),
            str(body.get("new_password") or ""),
        )

    @app.post("/api/owner-security/step-up")
    async def owner_security_step_up(request: Request):
        from jarvis.security.owner import get_owner_security

        body = await request.json()
        return get_owner_security().step_up(
            master_password=str(body.get("master_password") or ""),
            pin=str(body.get("pin") or ""),
        )

    @app.post("/api/owner-security/authorize")
    async def owner_security_authorize(request: Request):
        from jarvis.security.owner import get_owner_security

        body = await request.json()
        return get_owner_security().authorize(
            str(body.get("capability") or ""),
            room=(str(body.get("room") or "").strip() or None),
            session_token=_session_token(request),
        )

    @app.get("/api/owner-security/vault/meta")
    def owner_security_vault_meta(request: Request):
        from jarvis.security.owner import get_owner_security

        return get_owner_security().vault_meta()

    @app.get("/api/owner-security/timings")
    def owner_security_timings():
        from jarvis.security.owner import get_owner_security

        return {"ok": True, "timings": get_owner_security().timings()}

    @app.get("/api/owner-security/migration/status")
    def owner_security_migration_status(request: Request):
        from jarvis.security.owner import get_owner_security

        return get_owner_security().provider_migration_status()

    @app.post("/api/owner-security/migrate-provider")
    async def owner_security_migrate_provider(request: Request):
        """Copy one env provider credential into the vault. Never accepts or returns the secret."""
        from jarvis.security.owner import get_owner_security

        body = await request.json()
        field = str(body.get("field") or body.get("env") or "").strip()
        return get_owner_security().migrate_provider_credential(field)
