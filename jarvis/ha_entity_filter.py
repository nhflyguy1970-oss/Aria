"""Hide removed or unwanted Home Assistant entities from Jarvis."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any

from jarvis.config import DATA_DIR

_HIDDEN_FILE = DATA_DIR / "ha_hidden_entities.json"


def _norm(text: str) -> str:
    return re.sub(r"[\s_]+", " ", (text or "").lower()).strip()


@lru_cache(maxsize=1)
def _hidden_config() -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "entity_ids": [],
        "name_keywords": ["bathroom", "bath", "shower"],
        "hide_unavailable_lights": True,
    }
    try:
        if _HIDDEN_FILE.is_file():
            raw = json.loads(_HIDDEN_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                defaults.update(raw)
    except Exception:
        pass
    ids = {str(x).strip() for x in (defaults.get("entity_ids") or []) if str(x).strip()}
    keywords = [_norm(str(k)) for k in (defaults.get("name_keywords") or []) if str(k).strip()]
    return {
        "entity_ids": ids,
        "name_keywords": keywords,
        "hide_unavailable_lights": bool(defaults.get("hide_unavailable_lights", True)),
    }


def entity_hidden_from_jarvis(st: dict[str, Any] | None) -> bool:
    """True when Jarvis should not list or control this HA entity."""
    if not st:
        return False
    cfg = _hidden_config()
    eid = (st.get("entity_id") or "").strip()
    if eid in cfg["entity_ids"]:
        return True
    attrs = st.get("attributes") or {}
    hay = _norm(f"{eid} {attrs.get('friendly_name') or ''} {attrs.get('area_id') or ''}")
    if any(kw in hay for kw in cfg["name_keywords"]):
        return True
    if cfg["hide_unavailable_lights"] and eid.startswith("light."):
        state = (st.get("state") or "").lower()
        if state in ("unavailable", "unknown") or attrs.get("restored"):
            return True
    return False


def filter_visible_entities(states: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [st for st in states if not entity_hidden_from_jarvis(st)]
