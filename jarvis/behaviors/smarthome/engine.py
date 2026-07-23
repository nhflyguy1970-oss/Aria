"""Smart home action implementations — Home Assistant control and status."""

from __future__ import annotations

from jarvis.behaviors.smarthome.context import SmartHomeContext
from jarvis.response import err, ok


class SmartHomeEngine:
    @staticmethod
    def _not_configured() -> dict:
        return err(
            "**Home Assistant isn't connected yet.**\n\n"
            "1. In HA (`http://127.0.0.1:8123`): **Profile → Security → Long-lived access tokens → Create token**\n"
            "2. In ARIA sidebar → **Smart home** → paste token → **Test connection** → **Save**\n"
            "3. Or run: `./scripts/set-ha-token.sh`\n\n"
            "Then ask **house status** again.",
            module="automation",
            type="ha_setup",
        )

    @classmethod
    def ha_status(cls, ctx: SmartHomeContext, params: dict, message: str) -> dict:
        from jarvis.home_assistant import ha_enabled, home_summary, status_payload

        if not ha_enabled():
            return cls._not_configured()
        payload = status_payload()
        conn = payload.get("connection") or {}
        if not conn.get("ok"):
            return err(conn.get("message", "Home Assistant unreachable."), module="automation")
        success, summary = home_summary()
        if not success:
            return err(summary, module="automation")
        header = "**Home Assistant** connected"
        if conn.get("version"):
            header += f" (v{conn['version']})"
        header += ".\n\n"
        ctx.session.note_module("automation")
        return ok(
            header + summary,
            module="automation",
            type="ha_status",
            homeassistant=payload,
        )

    @classmethod
    def ha_control(cls, ctx: SmartHomeContext, params: dict, message: str) -> dict:
        from jarvis.home_assistant import control_entity, ha_enabled, parse_control
        from jarvis.tool_permissions import create_pending, permission_for

        if not ha_enabled():
            return cls._not_configured()
        perm = permission_for("ha_control")
        if perm == "never":
            return err("Home Assistant control is blocked by tool permissions.", module="automation")
        confirmed = str(params.get("confirmed", "")).lower() in ("1", "true", "yes")
        if perm == "ask" and not confirmed:
            confirm_id = create_pending("ha_control", "ha_control", dict(params or {}), message)
            return {
                "ok": False,
                "confirm_required": True,
                "confirm_id": confirm_id,
                "message": "Confirm Home Assistant control?",
                "module": "automation",
                "type": "confirm_required",
            }
        spec = parse_control(message) or params
        target = (spec.get("target") or "").strip()
        action = (spec.get("action") or "on").strip().lower()
        success, msg = control_entity(target, action)
        ctx.session.note_module("automation")
        if not success:
            return err(msg, module="automation")
        return ok(msg, module="automation", type="ha_control")

    @classmethod
    def ha_scene(cls, ctx: SmartHomeContext, params: dict, message: str) -> dict:
        from jarvis.home_assistant import activate_scene, ha_enabled, parse_scene

        if not ha_enabled():
            return cls._not_configured()
        scene = (params.get("scene") or parse_scene(message) or "").strip()
        success, msg = activate_scene(scene)
        ctx.session.note_module("automation")
        if not success:
            return err(msg, module="automation")
        return ok(msg, module="automation", type="ha_scene")

    @classmethod
    def ha_query(cls, ctx: SmartHomeContext, params: dict, message: str) -> dict:
        from jarvis.home_assistant import ha_enabled, query_entity

        if not ha_enabled():
            return cls._not_configured()
        query = (params.get("query") or message or "").strip()
        success, msg = query_entity(query)
        ctx.session.note_module("automation")
        if not success:
            return err(msg, module="automation")
        return ok(msg, module="automation", type="ha_query")

    @classmethod
    def ha_set_token(cls, ctx: SmartHomeContext, params: dict, message: str) -> dict:
        from jarvis.home_assistant import parse_ha_token_message, save_config, status_payload

        token = (params.get("token") or parse_ha_token_message(message) or "").strip()
        if not token:
            return err(
                "Paste your Home Assistant token here, or say "
                "`set home assistant token: …` · Sidebar → **Smart home** also has a paste box.",
                module="automation",
            )
        result = save_config(token=token, ensure_automation_secret=True)
        conn = result.get("connection") or {}
        if not conn.get("ok"):
            return err(
                conn.get("message", "Token saved but connection failed — check URL in Smart home panel."),
                module="automation",
            )
        ctx.session.note_module("automation")
        version = f" (v{conn['version']})" if conn.get("version") else ""
        return ok(
            f"Home Assistant connected{version}. "
            "Try **house status** or **turn off the living room lights**.",
            module="automation",
            type="ha_connected",
            homeassistant=status_payload(),
        )
