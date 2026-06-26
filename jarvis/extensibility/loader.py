"""Discover and load jarvis/extensions/* packages."""

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


def load_extensions(*, force: bool = False) -> list[Extension]:
    """Load all extensions once (handlers + route metadata)."""
    global _LOADED, _EXTENSIONS
    if _LOADED and not force:
        return _EXTENSIONS
    if force:
        _EXTENSIONS = []
    for name in _discover_extension_names():
        try:
            ext = _import_extension(name)
            if ext is None:
                continue
            ext.load()
            _EXTENSIONS.append(ext)
            logger.info("Loaded extension: %s", ext.meta.name)
        except Exception:
            logger.exception("Extension %s failed to load", name)
    _LOADED = True
    return _EXTENSIONS


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
    load_extensions()
    return [ext.to_dict() for ext in _EXTENSIONS]


def register_extension_api(app: FastAPI, assistant: JarvisAssistant) -> None:
    load_extensions()
    for ext in _EXTENSIONS:
        try:
            ext.register_api(app, assistant)
        except Exception:
            logger.exception("Extension %s API registration failed", ext.meta.name)
