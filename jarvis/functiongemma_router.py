# Source Generated with Decompyle++
# File: functiongemma_router.cpython-312.pyc (Python 3.12)

__doc__ = 'FunctionGemma intent router — HF tool-calling to ARIA actions (~50ms on CPU).'
from __future__ import annotations
import json
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any
from jarvis.p1_flags import local_router_enabled
from jarvis.session import SessionContext
log = logging.getLogger('jarvis.functiongemma')
_DEVELOPER_PROMPT = 'You are a model that can do function calling with the following functions'
_ROUTER_ACTIONS = ('system_info', 'morning_briefing', 'planner_add_task', 'planner_set_timer', 'planner_set_alarm', 'planner_today', 'curated_briefing', 'audio_stop', 'audio_pause', 'ha_control', 'ha_status', 'web_search', 'weather_forecast', 'generate_cad', 'iterate_cad', 'chat', 'thinking', 'nonthinking')
# WARNING: Decompyle incomplete
