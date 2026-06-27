"""Room aliases for Home Assistant voice control."""

from __future__ import annotations

import json
import re
from typing import Any

from jarvis.config import DATA_DIR

ALIASES_FILE = DATA_DIR / "ha_aliases.json"


def _load() -> dict[str, list[str]]:
    if not ALIASES_FILE.exists():
        return {}
    try:
        raw = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
        aliases = raw.get("aliases") or raw
        if not isinstance(aliases, dict):
            return {}
        out: dict[str, list[str]] = {}
        for key, val in aliases.items():
            if isinstance(val, list):
                out[str(key).lower()] = [str(v) for v in val]
            elif isinstance(val, str):
                out[str(key).lower()] = [val]
        return out
    except (json.JSONDecodeError, OSError):
        return {}


def save_aliases(aliases: dict[str, list[str]]) -> dict[str, list[str]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ALIASES_FILE.write_text(
        json.dumps({"aliases": aliases}, indent=2),
        encoding="utf-8",
    )
    return aliases


def get_aliases() -> dict[str, list[str]]:
    return _load()


def set_alias(name: str, entity_ids: list[str]) -> dict[str, list[str]]:
    aliases = _load()
    key = (name or "").lower().strip()
    if not key:
        raise ValueError("alias name required")
    aliases[key] = [e.strip() for e in entity_ids if e.strip()]
    return save_aliases(aliases)


def resolve_alias(query: str) -> list[str]:
    q = re.sub(r"[\s_]+", " ", (query or "").lower()).strip()
    if not q:
        return []
    aliases = _load()
    if q in aliases:
        return list(aliases[q])
    for key, ids in aliases.items():
        if key in q or q in key:
            return list(ids)
    return []
