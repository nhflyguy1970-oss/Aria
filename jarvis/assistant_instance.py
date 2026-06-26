# Source Generated with Decompyle++
# File: assistant_instance.cpython-312.pyc (Python 3.12)

'''Shared JarvisAssistant instance — server and MCP must use the same object.'''
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from jarvis.assistant import JarvisAssistant
log = logging.getLogger('jarvis.assistant_instance')
_assistant: 'JarvisAssistant | None' = None
_initializing = False

def set_assistant(assistant = None):
    global _assistant
    _assistant = assistant


def get_assistant():
    pass
# WARNING: Decompyle incomplete


def clear_assistant():
    '''Test helper.'''
    global _assistant
    _assistant = None

