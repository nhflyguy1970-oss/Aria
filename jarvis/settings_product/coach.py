"""Settings coach — warn only; never auto-change preferences."""

from __future__ import annotations

from typing import Any


def coach_warnings() -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []

    # Integrations / secrets hygiene
    try:
        from jarvis.integrations_product.secrets_bus import storage_info

        info = storage_info()
        if info.get("world_readable"):
            warnings.append(
                {
                    "id": "env_world_readable",
                    "severity": "warning",
                    "title": "Secret file may be world-readable",
                    "detail": "Run chmod 600 on data/jarvis.env",
                    "deep_link": {"view": "integrations", "section": "hygiene"},
                }
            )
        if not info.get("encrypted"):
            warnings.append(
                {
                    "id": "env_plaintext",
                    "severity": "info",
                    "title": "Secrets stored in plaintext jarvis.env",
                    "detail": "Integrations owns secrets — Aria does not encrypt this file today.",
                    "deep_link": {"view": "integrations"},
                }
            )
    except Exception:
        pass

    # Models present?
    try:
        from jarvis.model_store import load_settings as load_models

        ms = load_models() if callable(load_models) else {}
        if isinstance(ms, dict) and not (ms.get("chat") or ms.get("roles") or ms.get("models")):
            warnings.append(
                {
                    "id": "models_empty",
                    "severity": "info",
                    "title": "Model roles may be unset",
                    "detail": "Open Models Home to assign chat/coder roles.",
                    "deep_link": {"view": "models"},
                }
            )
    except Exception:
        pass

    # PIN lock flag without setup signal
    try:
        import os

        if os.getenv("JARVIS_PIN_LOCK", "").lower() in ("1", "true", "yes"):
            warnings.append(
                {
                    "id": "pin_enabled",
                    "severity": "info",
                    "title": "PIN lock flag enabled",
                    "detail": "Confirm PIN setup in Security if you expect workstation lock.",
                    "deep_link": {"view": "security", "section": "pin"},
                }
            )
    except Exception:
        pass

    # Appearance migration note
    try:
        from jarvis.settings_product.appearance import load_appearance

        app = load_appearance()
        if app.get("migrated_from_aria_theme"):
            warnings.append(
                {
                    "id": "theme_migrated",
                    "severity": "info",
                    "title": "Theme migrated into Settings appearance store",
                    "detail": "Legacy aria_theme localStorage was synced.",
                    "deep_link": {"view": "settings", "section": "appearance"},
                }
            )
    except Exception:
        pass

    return warnings
