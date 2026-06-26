# Source Generated with Decompyle++
# File: browser_vlm.cpython-312.pyc (Python 3.12)

'''VLM-guided browser clicks — screenshot → vision model → coordinates.'''
from __future__ import annotations
import json
import logging
import re
from pathlib import Path
from typing import Any
log = logging.getLogger('jarvis.browser.vlm')
_VLM_PROMPT = 'You are a browser automation assistant. Look at this screenshot.\nThe user wants: {goal}\n\nReply with ONLY one JSON object (no markdown):\n{{"action":"click","x":123,"y":456,"reason":"short"}}\nOR if done: {{"action":"done","summary":"what was accomplished"}}\nOR if stuck: {{"action":"fail","reason":"why"}}\nUse pixel coordinates from the top-left of the image.'

def _parse_vlm_json(raw = None):
    if not raw:
        raw
    text = ''.strip()
    if text.startswith('```'):
        text = re.sub('^```\\w*\\n?', '', text)
        text = re.sub('\\n?```$', '', text)
    start = text.find('{')
    end = text.rfind('}') + 1
    if start < 0 or end <= start:
        m = re.search('\\{\\s*\\"action\\"\\s*:', text)
        if m:
            start = m.start()
    if start < 0:
        return None
    
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None



def vlm_plan_click(screenshot_path = None, goal = None, *, assistant):
    '''Ask vision model what to click on the screenshot.'''
    path = Path(screenshot_path)
    if not path.is_file():
        return {
            'ok': False,
            'error': f'''Screenshot missing: {path}''' }
    prepare_for_browser_vlm = prepare_for_browser_vlm
    import jarvis.browser_vram
    prepare_for_browser_vlm()
# WARNING: Decompyle incomplete


def vlm_click_at(x = None, y = None):
    _PAGE = _PAGE
    _agent_paused = _agent_paused
    import jarvis.browser_agent
    if _agent_paused():
        return {
            'ok': False,
            'message': 'Agent paused' }
    if not None:
        return {
            'ok': False,
            'message': 'No browser page' }
    
    try:
        _PAGE.mouse.click(int(x), int(y))
        return {
            'ok': True,
            'x': x,
            'y': y }
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc


