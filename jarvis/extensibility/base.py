# Source Generated with Decompyle++
# File: base.cpython-312.pyc (Python 3.12)

'''Extension protocol for domain modules.'''
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from fastapi import FastAPI
    from jarvis.assistant import JarvisAssistant
    from jarvis.router_table import RouteRule
ExtensionMeta = <NODE:12>()

class Extension:
    meta: 'ExtensionMeta' = 'Hook surface for a domain extension (actions, routes, optional API).'
    
    def load(self = None):
        '''Import handler modules so @register_action side effects run.'''
        pass

    
    def routes(self = None):
        return []

    
    def register_api(self = None, app = None, assistant = None):
        pass

    
    def to_dict(self = None):
        pass
    # WARNING: Decompyle incomplete


