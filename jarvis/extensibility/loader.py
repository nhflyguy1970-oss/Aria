"""Discover and load jarvis/extensions/* packages (policy-aware)."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

    from jarvis.assistant import JarvisAssistant
    from jarvis.extensibility.base import Extension

logger = logging.getLogger("jarvis.extensions")
_LOADED = False
_EXTENSIONS: list[Extension] = []
_SKIPPED: list[dict] = []


def _discover_extension_names() -> list[str]:
    import jarvis.extensions as extensions_pkg

    root = Path(list(extensions_pkg.__path__)[0])
    names: list[str] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        if (child / "extension.py").is_file():
            names.append(child.name)
    return names


def _import_extension(name: str) -> Extension | None:
    module_name = f"jarvis.extensions.{name}.extension"
    mod = importlib.import_module(module_name)
    ext = getattr(mod, "EXTENSION", None)
    if ext is None:
        logger.warning("Extension %s has no EXTENSION export", name)
        return None
    return ext


def _policy_allows(name: str) -> bool:
    try:
        from jarvis.capabilities_product import policy as cap_policy

        cap_id = f"host:{name}"
        if cap_policy.is_quarantined(cap_id):
            return False
        return cap_policy.is_enabled(cap_id, trust="first_party", default=True)
    except Exception:
        return True


def load_extensions(*, force: bool = False) -> list[Extension]:
    """Load enabled extensions once (handlers + route metadata)."""
    global _LOADED, _EXTENSIONS, _SKIPPED
    if _LOADED and not force:
        return _EXTENSIONS
    if force:
        _EXTENSIONS = []
        _SKIPPED = []
    for name in _discover_extension_names():
        if not _policy_allows(name):
            _SKIPPED.append({"name": name, "reason": "disabled_or_quarantined"})
            logger.info("Skipping disabled/quarantined extension: %s", name)
            continue
        try:
            ext = _import_extension(name)
            if ext is None:
                continue
            # Lazy host extensions: record but skip heavy load()
            try:
                from jarvis.capabilities_product import policy as cap_policy

                if cap_policy.is_lazy(f"host:{name}"):
                    _SKIPPED.append({"name": name, "reason": "lazy"})
                    _EXTENSIONS.append(ext)  # metadata available
                    logger.info("Lazy host extension deferred: %s", name)
                    continue
            except Exception:
                pass
            ext.load()
            _EXTENSIONS.append(ext)
            logger.info("Loaded extension: %s", ext.meta.name)
        except Exception:
            logger.exception("Extension %s failed to load", name)
            try:
                from jarvis.capabilities_product import policy as cap_policy

                cap_policy.record_failure(f"host:{name}", "load failed")
            except Exception:
                pass
    _LOADED = True
    return _EXTENSIONS


def ensure_extension_loaded(name: str) -> Extension | None:
    """Load a single lazy/disabled-allowed host extension on demand."""
    global _EXTENSIONS
    if not _policy_allows(name):
        return None
    for ext in _EXTENSIONS:
        if ext.meta.name == name:
            try:
                ext.load()
            except Exception:
                logger.exception("Lazy load failed for %s", name)
                return None
            return ext
    try:
        ext = _import_extension(name)
        if ext is None:
            return None
        ext.load()
        _EXTENSIONS.append(ext)
        return ext
    except Exception:
        logger.exception("ensure_extension_loaded failed for %s", name)
        return None


def extension_routes():
    from jarvis.router_table import RouteRule

    load_extensions()
    rules: list[RouteRule] = []
    for ext in _EXTENSIONS:
        try:
            rules.extend(ext.routes())
        except Exception:
            logger.exception("Extension %s routes() failed", ext.meta.name)
    return rules


def list_extensions() -> list[dict]:
    """Return loaded extensions; Capabilities registry also scans disk for disabled ones."""
    load_extensions()
    return [ext.to_dict() for ext in _EXTENSIONS]


def list_extension_names_on_disk() -> list[str]:
    return _discover_extension_names()


def skipped_extensions() -> list[dict]:
    return list(_SKIPPED)


def register_extension_api(app: FastAPI, assistant: JarvisAssistant) -> None:
    load_extensions()
    for ext in _EXTENSIONS:
        try:
            ext.register_api(app, assistant)
        except Exception:
            logger.exception("Extension %s API registration failed", ext.meta.name)
