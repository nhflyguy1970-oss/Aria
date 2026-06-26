# Source Generated with Decompyle++
# File: loader.cpython-312.pyc (Python 3.12)

'''Discover and load jarvis/extensions/* packages.'''
from __future__ import annotations
import importlib
import logging
import pkgutil
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from fastapi import FastAPI
    from jarvis.assistant import JarvisAssistant
    from jarvis.extensibility.base import Extension
    from jarvis.router_table import RouteRule
logger = logging.getLogger('jarvis.extensions')
_LOADED = False
_EXTENSIONS: 'list[Extension]' = []

def _import_extension(info = None):
    module_name = f'''{info.name}.extension'''
# WARNING: Decompyle incomplete


def load_extensions(*, force):
    '''Load all extensions once (handlers + route metadata).'''
    global _EXTENSIONS
    if not _LOADED and force:
        return _EXTENSIONS
    if None:
        _EXTENSIONS = []
    pkg = extensions
    import jarvis.extensions
# WARNING: Decompyle incomplete


def extension_routes():
    load_extensions()
    rules = []
    for ext in _EXTENSIONS:
        rules.extend(ext.routes())
    return rules


def list_extensions():
    load_extensions()
# WARNING: Decompyle incomplete


def register_extension_api(app = None, assistant = None):
    load_extensions()
    for ext in _EXTENSIONS:
        ext.register_api(app, assistant)
    return None
    except Exception:
        logger.exception('Extension %s API registration failed', ext.meta.name)
        continue

