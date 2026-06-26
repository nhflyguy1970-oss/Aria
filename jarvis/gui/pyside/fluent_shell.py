# Source Generated with Decompyle++
# File: fluent_shell.cpython-312.pyc (Python 3.12)

'''FluentWindow shell: native dashboard + WebEngine for other views.'''
from __future__ import annotations
import json
import logging
from typing import Any
logger = logging.getLogger('jarvis.pyside.fluent_shell')

def fluent_shell_available():
    
    try:
        FluentWindow = FluentWindow
        import qfluentwidgets
        return True
    except ImportError:
        return False



def build_aria_fluent_window(base_url = None, *, icon_path):
    '''Build FluentWindow with native dashboard tab + shared web panel.'''
    pass
# WARNING: Decompyle incomplete

