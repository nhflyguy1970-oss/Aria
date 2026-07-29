"""Integration API keys — facade over Integrations secret bus (data/jarvis.env).

Prefer ``jarvis.integrations_product.secrets_bus`` for new code.
This module remains for backward compatibility with existing imports and tests.
"""

from __future__ import annotations

from typing import Any


def get_secret(field_or_env: str) -> str:
    from jarvis.integrations_product.secrets_bus import get_secret as _get

    return _get(field_or_env)


def get(field_or_env: str) -> str:
    """Alias used by connector bootstrap."""
    return get_secret(field_or_env)


def secrets_status() -> dict[str, Any]:
    from jarvis.integrations_product.secrets_bus import secrets_status as _status

    return _status(last4=True)


def save_secrets(patch: dict[str, Any]) -> dict[str, Any]:
    from jarvis.integrations_product.secrets_bus import save_secrets as _save

    return _save(patch)


def clear_secret(field: str) -> dict[str, Any]:
    from jarvis.integrations_product.secrets_bus import clear_secret as _clear

    return _clear(field)
