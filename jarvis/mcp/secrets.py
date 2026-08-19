"""The smallest safe secret mechanism this milestone needs.

Provider environment values (an API token for a hosted MCP server, say) must
not sit in Git, in the audit database, in logs, or in anything a model can see.
They live in one owner-only file under DATA_DIR, are loaded only at the moment
a provider process is launched, and are never returned by any read API — only
their key names are.
"""

from __future__ import annotations

import json
import os
import stat
from typing import Any

from jarvis.config import DATA_DIR

SECRETS_FILE = DATA_DIR / "mcp_secrets.json"


def _load() -> dict[str, dict[str, str]]:
    if not SECRETS_FILE.is_file():
        return {}
    try:
        data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save(data: dict[str, Any]) -> None:
    SECRETS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SECRETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Owner-only: a provider credential must not be world readable.
    os.chmod(SECRETS_FILE, stat.S_IRUSR | stat.S_IWUSR)


def set_provider_env(provider_id: str, env: dict[str, str]) -> list[str]:
    """Store a provider's environment. Returns the key names only."""
    data = _load()
    data[provider_id] = {str(k): str(v) for k, v in (env or {}).items()}
    _save(data)
    return sorted(data[provider_id])


def get_provider_env(provider_id: str) -> dict[str, str]:
    """Read a provider's environment. Only the launch path should call this."""
    return dict(_load().get(provider_id) or {})


def env_keys(provider_id: str) -> list[str]:
    """What a read API is allowed to reveal: names, never values."""
    return sorted(_load().get(provider_id) or {})


def clear_provider_env(provider_id: str) -> bool:
    data = _load()
    if provider_id not in data:
        return False
    del data[provider_id]
    _save(data)
    return True
