"""Home Assistant integration — read state, call services, scenes, automation webhooks."""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

log = logging.getLogger("jarvis")

_USER_AGENT = "Jarvis/3.2 HomeAssistant"


def _normalize_ha_text(message: str) -> str:
    """Lowercase and normalize casual typing / STT (missing apostrophes, trailing punctuation)."""
    text = (message or "").lower().strip()
    text = re.sub(r"[?.!,;]+$", "", text)
    text = re.sub(r"\bwhats\b", "what's", text)
    text = re.sub(r"\bhows\b", "how's", text)
    text = re.sub(r"\bwhat s\b", "what's", text)
    text = re.sub(r"\bhow s\b", "how's", text)
    return text


def ha_enabled() -> bool:
    flag = os.getenv("JARVIS_HA_ENABLED", "").lower()
    if flag in ("0", "false", "no", "off"):
        return False
    if flag in ("1", "true", "yes", "on"):
        return bool(ha_url() and ha_token())
    return bool(ha_url() and ha_token())


def ha_url() -> str:
    return (os.getenv("JARVIS_HA_URL", "") or os.getenv("HOME_ASSISTANT_URL", "")).strip().rstrip("/")


def ha_token() -> str:
    return normalize_ha_token(
        os.getenv("JARVIS_HA_TOKEN", "") or os.getenv("HOME_ASSISTANT_TOKEN", "")
    )


def normalize_ha_token(raw: str | None) -> str:
    """Clean pasted tokens — strip whitespace, quotes, accidental Bearer prefix."""
    token = (raw or "").strip()
    if not token:
        return ""
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
        token = token[1:-1].strip()
    return token.replace("\r", "").replace("\n", "").replace(" ", "")


def ha_feature_on() -> bool:
    flag = os.getenv("JARVIS_HA_ENABLED", "").lower().strip()
    if flag in ("0", "false", "no", "off"):
        return False
    return True


def _friendly_ha_error(exc: Exception) -> str:
    msg = str(exc)
    if "HTTP 401" in msg or "Unauthorized" in msg:
        return (
            "Invalid Home Assistant token (401). In HA: Profile → Security → "
            "Long-lived access tokens → Create token. Copy the entire token and paste again."
        )
    if "HTTP 403" in msg:
        return "Home Assistant rejected the token (403). Create a new long-lived token."
    return msg


def automation_secret() -> str:
    return os.getenv("JARVIS_AUTOMATION_SECRET", "").strip()


def leave_scene() -> str:
    return os.getenv("JARVIS_HA_SCENE_LEAVE", "").strip()


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {ha_token()}",
        "Content-Type": "application/json",
        "User-Agent": _USER_AGENT,
    }


def _request(method: str, path: str, body: dict | None = None, *, timeout: float = 15) -> Any:
    if not ha_url() or not ha_token():
        raise RuntimeError("Home Assistant not configured — set JARVIS_HA_URL and JARVIS_HA_TOKEN.")
    url = f"{ha_url()}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(), method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            if not raw:
                return {}
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"Home Assistant HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Home Assistant unreachable at {ha_url()}: {exc.reason}") from exc


def check_connection() -> dict[str, Any]:
    from jarvis.env_loader import load_jarvis_env

    load_jarvis_env()
    url = ha_url()
    token = ha_token()
    if ha_feature_on() and url and not token:
        return {
            "ok": False,
            "enabled": True,
            "url": url,
            "message": "No token saved yet — paste a long-lived access token from Home Assistant → Profile → Security.",
        }
    if not ha_enabled():
        return {
            "ok": False,
            "enabled": ha_feature_on(),
            "url": url,
            "message": "Home Assistant is off — set JARVIS_HA_URL + JARVIS_HA_TOKEN in data/jarvis.env.",
        }
    try:
        info = _request("GET", "/api/")
        return {
            "ok": True,
            "enabled": True,
            "url": url,
            "message": info.get("message", "API running."),
            "version": info.get("version"),
        }
    except Exception as exc:
        return {"ok": False, "enabled": True, "url": url, "message": _friendly_ha_error(exc)}


def list_states(*, refresh: bool = True) -> list[dict]:
    del refresh
    states = _request("GET", "/api/states")
    return states if isinstance(states, list) else []


def get_state(entity_id: str) -> dict | None:
    eid = (entity_id or "").strip()
    if not eid:
        return None
    try:
        state = _request("GET", f"/api/states/{urllib.parse.quote(eid)}")
        return state if isinstance(state, dict) else None
    except RuntimeError:
        return None


def _norm(s: str) -> str:
    return re.sub(r"[\s_]+", " ", (s or "").lower()).strip()


def find_entities(query: str, *, domain: str | None = None, limit: int = 8) -> list[dict]:
    q = _norm(query)
    if not q:
        return []
    words = [w for w in q.split() if len(w) > 1]
    scored: list[tuple[float, dict]] = []
    for st in list_states():
        eid = st.get("entity_id") or ""
        if domain and not eid.startswith(f"{domain}."):
            continue
        attrs = st.get("attributes") or {}
        friendly = _norm(attrs.get("friendly_name") or "")
        hay = _norm(f"{eid} {friendly}")
        score = 0.0
        if q in hay or q.replace(" ", "_") in eid:
            score += 10
        for w in words:
            if w in hay or w in eid:
                score += 2
        if eid.endswith(q.replace(" ", "_")):
            score += 3
        if score > 0:
            scored.append((score, st))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [st for _, st in scored[:limit]]


def call_service(domain: str, service: str, data: dict | None = None) -> dict:
    payload = dict(data or {})
    result = _request("POST", f"/api/services/{domain}/{service}", payload)
    return {"domain": domain, "service": service, "data": payload, "result": result}


def _entity_line(st: dict) -> str:
    eid = st.get("entity_id", "")
    attrs = st.get("attributes") or {}
    name = attrs.get("friendly_name") or eid
    state = st.get("state", "?")
    unit = attrs.get("unit_of_measurement") or ""
    suffix = f" {unit}" if unit else ""
    return f"- **{name}** (`{eid}`): {state}{suffix}"


def format_entity(st: dict) -> str:
    return _entity_line(st).replace("- **", "**").replace("** (`", "** (`", 1)


def activate_scene(scene: str) -> tuple[bool, str]:
    scene = (scene or "").strip()
    if not scene:
        return False, "Which scene?"
    if not scene.startswith("scene."):
        matches = find_entities(scene, domain="scene", limit=3)
        if len(matches) == 1:
            scene = matches[0]["entity_id"]
        elif matches:
            lines = "\n".join(_entity_line(m) for m in matches)
            return False, f"Multiple scenes match — be specific:\n{lines}"
        else:
            scene = f"scene.{scene.replace(' ', '_').lower()}"
    try:
        call_service("scene", "turn_on", {"entity_id": scene})
        st = get_state(scene)
        name = (st or {}).get("attributes", {}).get("friendly_name") or scene
        return True, f"Activated scene **{name}** (`{scene}`)."
    except Exception as exc:
        return False, str(exc)


def control_entity(target: str, action: str) -> tuple[bool, str]:
    action = (action or "").strip().lower()
    if action not in ("on", "off", "toggle"):
        return False, f"Unknown action `{action}` — use on, off, or toggle."

    target = (target or "").strip()
    if not target:
        return False, "Which device?"

    matches = find_entities(target, limit=5)
    if not matches:
        if "." in target:
            matches = [{"entity_id": target, "attributes": {"friendly_name": target}, "state": "?"}]
        else:
            return False, f"No Home Assistant entity matched `{target}`."

    if len(matches) > 1 and "." not in target:
        lines = "\n".join(_entity_line(m) for m in matches[:5])
        return False, f"Multiple matches — be more specific:\n{lines}"

    st = matches[0]
    eid = st.get("entity_id") or target
    domain = eid.split(".")[0] if "." in eid else "homeassistant"
    service = {"on": "turn_on", "off": "turn_off", "toggle": "toggle"}.get(action, "turn_on")
    try:
        call_service(domain, service, {"entity_id": eid})
        name = (st.get("attributes") or {}).get("friendly_name") or eid
        return True, f"Turned **{action}** — **{name}** (`{eid}`)."
    except Exception as exc:
        return False, str(exc)


def query_entity(question: str) -> tuple[bool, str]:
    q = (question or "").strip()
    matches = find_entities(q, limit=5)
    if not matches and re.search(r"^(sensor|light|switch|climate|binary_sensor)\.", q.replace(" ", "_")):
        st = get_state(q.replace(" ", "_"))
        if st:
            matches = [st]
    if not matches:
        return False, f"I couldn't find a Home Assistant entity for `{q}`."
    if len(matches) > 1:
        lines = "\n".join(_entity_line(m) for m in matches[:6])
        return True, f"Matches:\n{lines}"
    return True, _entity_line(matches[0]).lstrip("- ")


def home_summary(*, limit: int = 10) -> tuple[bool, str]:
    try:
        states = list_states()
    except Exception as exc:
        return False, str(exc)

    interesting: list[str] = []
    for st in states:
        eid = st.get("entity_id") or ""
        state = (st.get("state") or "").lower()
        domain = eid.split(".")[0] if "." in eid else ""
        if domain in ("person", "device_tracker") and state not in ("home", "unknown", "unavailable"):
            interesting.append(_entity_line(st))
        elif domain == "climate" and state not in ("off", "unavailable", "unknown"):
            interesting.append(_entity_line(st))
        elif domain in ("light", "switch") and state == "on":
            interesting.append(_entity_line(st))
        elif domain == "binary_sensor" and state == "on":
            interesting.append(_entity_line(st))
        if len(interesting) >= limit:
            break

    people = [
        _entity_line(st) for st in states
        if (st.get("entity_id") or "").startswith("person.")
        and (st.get("state") or "") not in ("unavailable", "unknown")
    ][:4]

    parts = ["**Home Assistant snapshot**"]
    if people:
        parts.append("People:\n" + "\n".join(people))
    if interesting:
        parts.append("Notable:\n" + "\n".join(interesting[:limit]))
    if len(parts) == 1:
        parts.append("All quiet — no notable device states.")
    return True, "\n\n".join(parts)


def parse_scene(message: str) -> str | None:
    text = (message or "").strip()
    for pat in (
        r"^(?:activate|run|trigger|start)\s+(?:the\s+)?scene[:\s]+(.+)$",
        r"^scene[:\s]+(.+)$",
        r"^(?:activate|run)\s+(.+)\s+scene$",
    ):
        m = re.match(pat, text, re.I)
        if m:
            return m.group(1).strip()
    lower = text.lower()
    if re.search(r"\b(i'?m leaving|heading out|goodbye house|good night house)\b", lower):
        preset = leave_scene()
        if preset:
            return preset
        if "good night" in lower or "goodnight" in lower:
            return "goodnight"
        return "leaving"
    return None


def parse_control(message: str) -> dict | None:
    text = (message or "").strip()
    m = re.match(
        r"^(?:please\s+)?(turn|switch)\s+(on|off|toggle)\s+(?:the\s+)?(.+)$",
        text,
        re.I,
    )
    if m:
        return {"action": m.group(2).lower(), "target": m.group(3).strip()}
    m = re.match(r"^(?:please\s+)?(turn|switch)\s+(?:the\s+)?(.+?)\s+(on|off)$", text, re.I)
    if m:
        return {"action": m.group(3).lower(), "target": m.group(2).strip()}
    return None


def is_ha_status_query(message: str) -> bool:
    lower = _normalize_ha_text(message)
    if re.search(
        r"\b("
        r"home assistant status|ha status|house status|home status|"
        r"smart home status|home overview|home snapshot|"
        r"what(?:'?s| is| are) on at (?:home|the house|my house|my home)|"
        r"how(?:'?s| is) (?:the )?house|"
        r"(?:anything|something) (?:on|going on|running) (?:at )?(?:home|the house|my house)"
        r")\b",
        lower,
    ):
        return True
    if re.search(r"\bstatus (?:of )?(?:my |the )?home\b", lower):
        return True
    if re.search(
        r"\b(check|show|get|tell me|what(?:'?s| is| are)|which|status of|state of)\b",
        lower,
    ) and re.search(
        r"\b(home assistant|smart home|(?:my |the )?home|my house|the house|at home)\b",
        lower,
    ):
        return True
    if re.search(
        r"\b(check|show|get|tell me|what(?:'?s| is| are)|which|status of|state of)\b",
        lower,
    ) and re.search(r"\b(lights?|switches?|thermostat|doors?|garage|living room|bedroom|kitchen)\b", lower):
        return True
    if re.search(r"\b(which|what) lights? (?:are )?(?:on|off)\b", lower):
        return True
    if re.search(r"\b(lights?|switches?) (?:that are )?(?:on|off)\b", lower):
        return True
    return False


def is_ha_state_query(message: str) -> bool:
    lower = _normalize_ha_text(message)
    return bool(
        re.search(
            r"\b(what(?:'?s| is) the (?:temperature|temp|humidity)|"
            r"is the .+ (?:on|off|open|closed)|"
            r"state of (?:the )?.+)\b",
            lower,
        )
        and re.search(r"\b(light|switch|sensor|thermostat|door|garage|room|living|bedroom|office)\b", lower)
    )


def quick_route_home_assistant(message: str) -> dict | None:
    """Return HA action dict for smart-home phrasing (works even before token is saved)."""
    scene = parse_scene(message)
    if scene:
        return {"action": "ha_scene", "params": {"scene": scene}}
    control = parse_control(message)
    if control:
        return {"action": "ha_control", "params": control}
    if is_ha_status_query(message):
        return {"action": "ha_status", "params": {}}
    if is_ha_state_query(message):
        return {"action": "ha_query", "params": {"query": message}}
    return None


def status_payload() -> dict[str, Any]:
    from jarvis.env_loader import load_jarvis_env

    load_jarvis_env()
    conn = check_connection()
    secret = automation_secret()
    webhook_url = ""
    if secret:
        try:
            from jarvis.lan import client_base_url

            webhook_url = f"{client_base_url()}/api/automation/inbound?secret={secret}"
        except Exception:
            webhook_url = f"/api/automation/inbound?secret={secret}"
    return {
        "enabled": ha_feature_on(),
        "feature_on": ha_feature_on(),
        "configured": bool(ha_url() and ha_token()),
        "connected": bool(conn.get("ok")),
        "token_set": bool(ha_token()),
        "url": ha_url(),
        "leave_scene": leave_scene(),
        "automation_secret_set": bool(secret),
        "automation_webhook": "/api/automation/inbound",
        "automation_webhook_url": webhook_url,
        "connection": conn,
    }


def save_config(
    *,
    url: str | None = None,
    token: str | None = None,
    leave_scene: str | None = None,
    enabled: bool | None = None,
    ensure_automation_secret: bool = True,
) -> dict[str, Any]:
    from jarvis.env_loader import load_jarvis_env, upsert_env_vars
    from jarvis.lan import generate_api_key

    updates: dict[str, str] = {}
    if enabled is not None:
        updates["JARVIS_HA_ENABLED"] = "1" if enabled else "0"
    elif ha_url() or ha_token():
        updates.setdefault("JARVIS_HA_ENABLED", "1")
    if url is not None and url.strip():
        updates["JARVIS_HA_URL"] = url.strip().rstrip("/")
    if token is not None:
        cleaned = normalize_ha_token(token)
        if cleaned:
            updates["JARVIS_HA_TOKEN"] = cleaned
    if leave_scene is not None:
        updates["JARVIS_HA_SCENE_LEAVE"] = leave_scene.strip()
    if ensure_automation_secret and not automation_secret():
        updates["JARVIS_AUTOMATION_SECRET"] = generate_api_key()

    changed = upsert_env_vars(updates) if updates else []
    load_jarvis_env(force=True)
    payload = status_payload()
    payload["changed"] = changed
    return payload


def test_connection(url: str | None = None, token: str | None = None) -> dict[str, Any]:
    """Probe HA without persisting config."""
    probe_url = (url or ha_url()).strip().rstrip("/")
    probe_token = normalize_ha_token(token or ha_token())
    if not probe_url:
        return {"ok": False, "message": "Home Assistant URL is required."}
    if not probe_token:
        return {"ok": False, "message": "Paste your long-lived access token first."}
    old_url, old_token = os.environ.get("JARVIS_HA_URL"), os.environ.get("JARVIS_HA_TOKEN")
    try:
        os.environ["JARVIS_HA_URL"] = probe_url
        os.environ["JARVIS_HA_TOKEN"] = probe_token
        return check_connection()
    finally:
        if old_url is None:
            os.environ.pop("JARVIS_HA_URL", None)
        else:
            os.environ["JARVIS_HA_URL"] = old_url
        if old_token is None:
            os.environ.pop("JARVIS_HA_TOKEN", None)
        else:
            os.environ["JARVIS_HA_TOKEN"] = old_token


def briefing_home_lines(*, limit: int = 6) -> list[str]:
    if not ha_enabled():
        return []
    ok, text = home_summary(limit=limit)
    if not ok or not text.strip():
        return []
    return [text]


def parse_ha_token_message(message: str) -> str | None:
    text = (message or "").strip()
    for pat in (
        r"^(?:set\s+)?(?:home assistant|ha)\s+token[:\s]+(.+)$",
        r"^paste(?:\s+(?:ha|home assistant))?\s+token[:\s]+(.+)$",
    ):
        m = re.match(pat, text, re.I | re.S)
        if m:
            token = m.group(1).strip()
            return token or None
    if re.fullmatch(r"eyJ[A-Za-z0-9._-]+", text) and len(text) >= 30:
        return text
    return None


def verify_automation_secret(header_value: str | None, query_value: str | None = None) -> bool:
    secret = automation_secret()
    if not secret:
        return False
    supplied = (header_value or query_value or "").strip()
    return supplied == secret
