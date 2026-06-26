# Source Generated with Decompyle++
# File: system_monitor.cpython-312.pyc (Python 3.12)

'''Live CPU/RAM/GPU and Ollama model stats for the GUI.'''
from __future__ import annotations
import json
import threading
import time
import urllib.request as urllib
from typing import Any
_CACHE_LOCK = threading.Lock()
_CACHE: 'dict[str, Any] | None' = None
_CACHE_AT: 'float' = 0
_CACHE_TTL_SEC = float(__import__('os').getenv('JARVIS_MONITOR_CACHE_SEC', '7'))

def _ollama_running_models():
    pass
# WARNING: Decompyle incomplete


def collect_stats():
    now = time.time()
    _CACHE_LOCK
# WARNING: Decompyle incomplete

