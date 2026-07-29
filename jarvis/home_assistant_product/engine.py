"""One Smart Home engine — wraps jarvis.home_assistant (never duplicate HA/Lovelace)."""

from __future__ import annotations

from typing import Any

from jarvis.home_assistant_product.terminology import BOUNDARIES, TERMINOLOGY


def product_status() -> dict[str, Any]:
    from jarvis.home_assistant import status_payload
    from jarvis.home_assistant_product.history import list_history
    from jarvis.home_assistant_product.profiles import active_profile_id, list_profiles
    from jarvis.home_assistant_product.settings import load_settings
    from jarvis.home_assistant_product.status_bus import get_smarthome_state

    ha: dict[str, Any] = {}
    try:
        ha = status_payload()
    except Exception as exc:
        ha = {"ok": False, "error": str(exc)}
    recovery = recovery_status()
    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "boundaries": BOUNDARIES,
        "state": get_smarthome_state(),
        "settings": load_settings(),
        "profiles": {"active": active_profile_id(), "count": len(list_profiles())},
        "ha": ha,
        "recovery": recovery,
        "history_recent": list_history(limit=5),
        "pipeline": [
            "chat",
            "voice",
            "mission_control",
            "planner",
            "calendar",
            "automation",
            "browser",
            "mcp",
            "smarthome_engine",
            "permissions",
            "entity_resolution",
            "execution",
            "status_bus",
            "activity",
            "completion",
        ],
    }


def recovery_status() -> dict[str, Any]:
    """Guided Home Assistant connect steps — operator-friendly, not CLI-first."""
    from jarvis.home_assistant import (
        check_connection,
        ha_feature_on,
        ha_token,
        ha_url,
        status_payload,
    )

    url = ha_url()
    token = bool(ha_token())
    feature = ha_feature_on()
    conn: dict[str, Any] = {}
    try:
        conn = check_connection() if (url and token) else {
            "ok": False,
            "message": "URL and token required",
        }
    except Exception as exc:
        conn = {"ok": False, "message": str(exc)}

    steps: list[dict[str, Any]] = []
    steps.append(
        {
            "id": "enable",
            "label": "Smart Home feature on",
            "done": feature,
            "detail": "JARVIS_HA_ENABLED is on" if feature else "Turn on Home Assistant in Smart Home setup",
        }
    )
    steps.append(
        {
            "id": "url",
            "label": "Home Assistant URL",
            "done": bool(url),
            "detail": url or "Paste your HA URL (e.g. http://homeassistant.local:8123)",
        }
    )
    steps.append(
        {
            "id": "token",
            "label": "Long-lived access token",
            "done": token,
            "detail": (
                "Token saved"
                if token
                else "In HA: Profile → Security → Long-lived access tokens → Create token"
            ),
        }
    )
    connected = bool(conn.get("ok"))
    steps.append(
        {
            "id": "test",
            "label": "Test connection",
            "done": connected,
            "detail": conn.get("message") or ("API reachable" if connected else "Run Test after saving URL + token"),
        }
    )
    steps.append(
        {
            "id": "open_ha",
            "label": "Open Home Assistant",
            "done": bool(url),
            "detail": url or "Available after URL is saved",
            "action": "open_url",
        }
    )

    ready = feature and bool(url) and token and connected
    status = {}
    try:
        status = status_payload()
    except Exception:
        status = {}

    return {
        "ok": True,
        "ready": ready,
        "guided": True,
        "connection": conn,
        "status": status,
        "steps": steps,
        "hint": (
            "Ready — control devices from Smart Home Home"
            if ready
            else "Follow guided connect steps: URL → Token → Test → Save"
        ),
        "deep_links": {
            "home": "/api/smarthome/product/home",
            "status": "/api/smarthome/product",
            "recovery": "/api/smarthome/product/recovery",
            "ui": "#smarthome",
            "ha_ui": url or "",
        },
    }


def home_payload() -> dict[str, Any]:
    """Smart Home Home — control-first overview (favorites, rooms, scenes, recent, health)."""
    from jarvis.home_assistant_product.favorites import favorites_payload
    from jarvis.home_assistant_product.history import list_history
    from jarvis.home_assistant_product.profiles import active_profile_id
    from jarvis.home_assistant_product.rooms import list_rooms
    from jarvis.home_assistant_product.settings import load_settings

    recovery = recovery_status()
    fav = favorites_payload()
    rooms = []
    try:
        rooms = list_rooms()
    except Exception:
        rooms = []

    scenes: list[dict[str, Any]] = []
    try:
        from jarvis.scene_presets import list_presets

        scenes = list_presets()
    except Exception:
        scenes = []

    recent = list_history(limit=12)
    health = {
        "ready": recovery.get("ready"),
        "hint": recovery.get("hint"),
        "connected": bool((recovery.get("connection") or {}).get("ok")),
        "url": (recovery.get("status") or {}).get("url") or "",
    }

    suggestions: list[str] = []
    if not recovery.get("ready"):
        suggestions.append("Connect Home Assistant — open guided recovery")
    else:
        suggestions.append("Pin favorites for one-tap control")
        if not rooms:
            suggestions.append("Add room cards for kitchen, office, workshop")
        if scenes:
            suggestions.append("Activate a scene preset from Home")

    return {
        "ok": True,
        "product": TERMINOLOGY["product"],
        "control_first": bool(load_settings().get("control_first", True)),
        "favorites": fav,
        "rooms": rooms,
        "scenes": scenes,
        "recent": recent,
        "health": health,
        "recovery": recovery,
        "suggestions": suggestions,
        "active_profile": active_profile_id(),
        "pipeline": TERMINOLOGY["pipeline"],
    }


def house_status(*, limit: int = 10) -> dict[str, Any]:
    """Wrap home_assistant.home_summary — one status path."""
    from jarvis.config import is_uncensored
    from jarvis.home_assistant import home_summary
    from jarvis.home_assistant_product.history import add_entry
    from jarvis.home_assistant_product.status_bus import set_smarthome_state

    set_smarthome_state("searching", detail="house_status", task="status")
    try:
        ok, text = home_summary(limit=limit)
        entry = add_entry(
            {
                "kind": "status",
                "summary": "House status",
                "detail": text[:4000],
                "source": "engine",
                "uncensored_origin": bool(is_uncensored()),
            }
        )
        return {
            "ok": ok,
            "message": text,
            "history_id": entry.get("id"),
            "pipeline": "smarthome_engine",
        }
    finally:
        set_smarthome_state("idle", detail="status_done")


def control_device(
    target: str,
    action: str = "toggle",
    *,
    brightness: int | None = None,
    color_name: str | None = None,
    rgb: list[int] | None = None,
    hs: list[float] | None = None,
    color_temp_kelvin: int | None = None,
    transition: float | None = None,
    source: str = "api",
) -> dict[str, Any]:
    """
    Control a device via entity resolve + ha_light_control / home_assistant.
    Never duplicates Lovelace — executes against HA REST services only.
    """
    from jarvis.config import is_uncensored
    from jarvis.home_assistant import call_service, control_entity, ha_enabled
    from jarvis.home_assistant_product.entities import resolve
    from jarvis.home_assistant_product.history import add_entry
    from jarvis.home_assistant_product.status_bus import set_smarthome_state

    if not ha_enabled():
        return {"ok": False, "message": "Home Assistant not enabled"}

    act = (action or "toggle").strip().lower()
    if act in ("turn_on", "turnon"):
        act = "on"
    elif act in ("turn_off", "turnoff"):
        act = "off"

    set_smarthome_state("controlling", detail=f"{act} {target}", task="control", entity_id=target)
    try:
        resolved = resolve(target, limit=5)
        entity_ids = list(resolved.get("entity_ids") or [])
        if not entity_ids and "." in (target or ""):
            entity_ids = [target.strip()]
        if not entity_ids:
            return {"ok": False, "message": resolved.get("message") or f"No entity matched `{target}`", "resolve": resolved}

        if len(entity_ids) > 1 and "." not in (target or "").strip():
            return {
                "ok": False,
                "message": "Multiple matches — be more specific",
                "matches": resolved.get("matches") or [],
                "resolve": resolved,
            }

        eid = entity_ids[0]
        domain = eid.split(".", 1)[0] if "." in eid else "homeassistant"
        lightish = domain == "light" or (
            brightness is not None
            or color_name
            or rgb
            or hs
            or color_temp_kelvin is not None
        )

        if lightish and domain == "light" and act in ("on", "off", "toggle", "brightness", "color", "dim", "brighten"):
            from jarvis.ha_light_control import set_lights

            light_action = act
            bp = brightness
            if act in ("brightness", "color", "dim", "brighten"):
                light_action = "on"
            if act == "dim" and bp is None:
                bp = 30
            if act == "brighten" and bp is None:
                bp = 90
            ok, msg = set_lights(
                [eid],
                action="off" if act == "off" else ("toggle" if act == "toggle" else "on"),
                brightness_pct=bp,
                rgb=rgb,
                hs=hs,
                color_temp_kelvin=color_temp_kelvin,
                color_name=color_name,
                transition=transition,
            )
            entry = add_entry(
                {
                    "kind": "control",
                    "entity_id": eid,
                    "action": act,
                    "summary": msg,
                    "detail": msg,
                    "source": source,
                    "uncensored_origin": bool(is_uncensored()),
                    "meta": {
                        "brightness": bp,
                        "color_name": color_name,
                        "rgb": rgb,
                        "color_temp_kelvin": color_temp_kelvin,
                    },
                }
            )
            return {
                "ok": ok,
                "message": msg,
                "entity_id": eid,
                "action": act,
                "history_id": entry.get("id"),
                "pipeline": "smarthome_engine",
            }

        if act in ("on", "off", "toggle"):
            ok, msg = control_entity(eid, act)
        else:
            # Fallback: generic domain service
            svc = {"on": "turn_on", "off": "turn_off", "toggle": "toggle"}.get(act, act)
            try:
                call_service(domain, svc, {"entity_id": eid})
                ok, msg = True, f"Called {domain}.{svc} on {eid}"
            except Exception as exc:
                ok, msg = False, str(exc)

        entry = add_entry(
            {
                "kind": "control",
                "entity_id": eid,
                "action": act,
                "summary": msg,
                "detail": msg,
                "source": source,
                "uncensored_origin": bool(is_uncensored()),
            }
        )
        return {
            "ok": ok,
            "message": msg,
            "entity_id": eid,
            "action": act,
            "history_id": entry.get("id"),
            "pipeline": "smarthome_engine",
        }
    finally:
        set_smarthome_state("idle", detail="control_done")


def activate_scene(scene: str, *, source: str = "api") -> dict[str, Any]:
    """Activate HA scene or named scene_presets entry — wraps existing modules."""
    from jarvis.config import is_uncensored
    from jarvis.home_assistant import activate_scene as ha_activate_scene, ha_enabled
    from jarvis.home_assistant_product.history import add_entry
    from jarvis.home_assistant_product.status_bus import set_smarthome_state

    name = (scene or "").strip()
    if not name:
        return {"ok": False, "message": "Which scene?"}

    set_smarthome_state("scene", detail=name, task="scene", scene=name)
    try:
        # Prefer scene_presets for friendly names (movie mode, focus, sunlight, …)
        try:
            from jarvis.scene_presets import activate_preset, list_presets

            presets = {str(p.get("id") or "").lower(): p for p in list_presets()}
            presets.update({str(p.get("label") or "").lower(): p for p in list_presets()})
            key = name.lower()
            if key in presets or any(key in k for k in presets):
                ok_flag, msg = activate_preset(name)
                entry = add_entry(
                    {
                        "kind": "scene",
                        "scene": name,
                        "summary": msg,
                        "detail": msg,
                        "source": source,
                        "uncensored_origin": bool(is_uncensored()),
                        "meta": {"via": "scene_presets"},
                    }
                )
                return {
                    "ok": ok_flag,
                    "message": msg,
                    "scene": name,
                    "history_id": entry.get("id"),
                    "pipeline": "smarthome_engine",
                    "via": "scene_presets",
                }
        except Exception:
            pass

        if not ha_enabled():
            return {"ok": False, "message": "Home Assistant not enabled"}

        ok, msg = ha_activate_scene(name)
        entry = add_entry(
            {
                "kind": "scene",
                "scene": name,
                "summary": msg,
                "detail": msg,
                "source": source,
                "uncensored_origin": bool(is_uncensored()),
                "meta": {"via": "home_assistant"},
            }
        )
        return {
            "ok": ok,
            "message": msg,
            "scene": name,
            "history_id": entry.get("id"),
            "pipeline": "smarthome_engine",
            "via": "home_assistant",
        }
    finally:
        set_smarthome_state("idle", detail="scene_done")
