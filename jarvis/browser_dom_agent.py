# Source Generated with Decompyle++
# File: browser_dom_agent.cpython-312.pyc (Python 3.12)

'''Playwright DOM agent — page snapshot → LLM → click/fill/navigate.'''
from __future__ import annotations
import json
import logging
import re
from typing import Any
log = logging.getLogger('jarvis.browser.dom')
_DOM_PROMPT = 'You are a browser automation agent. Given the page snapshot and user goal, reply with ONLY one JSON object:\n{{"action":"click","selector":"css selector","reason":"..."}}\n{{"action":"fill","selector":"...","text":"...","reason":"..."}}\n{{"action":"wait","ms":500}}\n{{"action":"done","summary":"..."}}\n{{"action":"fail","reason":"..."}}\nPrefer stable selectors (#id, [name=], aria-label). Goal: {goal}\n\nPage snapshot:\n{snapshot}'

def _parse_action(raw = None):
    if not raw:
        raw
    text = ''.strip()
    if '```' in text:
        text = re.sub('```\\w*\\n?', '', text)
        text = text.replace('```', '')
    start = text.find('{')
    end = text.rfind('}') + 1
    if start < 0:
        return None
    
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None



def get_page_snapshot():
    _PAGE = _PAGE
    import jarvis.browser_agent
    if not _PAGE:
        return {
            'ok': False,
            'error': 'No browser page' }
    
    try:
        title = _PAGE.title()
        url = _PAGE.url
        elements = _PAGE.evaluate("() => {\n              const out = [];\n              const nodes = document.querySelectorAll('a, button, input, textarea, select, [role=button]');\n              for (const el of Array.from(nodes).slice(0, 35)) {\n                const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim().slice(0, 80);\n                if (!text && el.tagName !== 'INPUT') continue;\n                out.push({\n                  tag: el.tagName.toLowerCase(),\n                  text,\n                  id: el.id || '',\n                  name: el.name || '',\n                  type: el.type || '',\n                  href: el.href ? el.href.slice(0, 120) : '',\n                });\n              }\n              return out;\n            }")
        if not elements:
            elements
        return {
            'ok': True,
            'title': title,
            'url': url,
            'elements': [] }
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc



def _format_snapshot(snap = None):
    lines = [
        f'''URL: {snap.get('url', '')}''',
        f'''Title: {snap.get('title', '')}''',
        'Elements:']
    if not snap.get('elements'):
        snap.get('elements')
    for el in []:
        parts = [
            el.get('tag', '?')]
        if el.get('id'):
            parts.append(f'''#{el['id']}''')
        if el.get('name'):
            parts.append(f'''name={el['name']}''')
        if el.get('text'):
            parts.append(f'''"{el['text']}"''')
        lines.append('- ' + ' '.join(parts))
    return '\n'.join(lines)[:6000]


def dom_plan_step(goal = None, snapshot = None):
    llm = llm
    import jarvis
    prompt = _DOM_PROMPT.format(goal = goal[:300], snapshot = _format_snapshot(snapshot))
    
    try:
        raw = llm.ask_with_system(llm.general_model(), 'You output only JSON browser actions.', prompt, options = {
            'temperature': 0,
            'num_predict': 200 })
        action = _parse_action(raw)
        if not action:
            return {
                'ok': False,
                'error': 'Invalid DOM plan JSON',
                'raw': raw[:300] }
        return {
            'ok': None,
            'action': action,
            'raw': raw[:400] }
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc



def execute_dom_action(action = None):
    _PAGE = _PAGE
    _agent_paused = _agent_paused
    click_selector = click_selector
    import jarvis.browser_agent
    if _agent_paused():
        return {
            'ok': False,
            'message': 'Agent paused' }
    if not None.get('action'):
        None.get('action')
    kind = ''.lower()
    if kind == 'done':
        return {
            'ok': True,
            'done': True,
            'summary': action.get('summary', '') }
    if None == 'fail':
        return {
            'ok': False,
            'failed': True,
            'reason': action.get('reason', '') }
    if None == 'wait':
        import time
        if not action.get('ms'):
            action.get('ms')
        time.sleep(min(5, max(0.1, int(500) / 1000)))
        return {
            'ok': True,
            'waited': True }
    if None == 'click':
        if not action.get('selector'):
            action.get('selector')
        sel = ''.strip()
        if not sel:
            return {
                'ok': False,
                'message': 'Missing selector' }
        return click_selector(sel)
    if None == 'fill':
        if not action.get('selector'):
            action.get('selector')
        sel = ''.strip()
        if not action.get('text'):
            action.get('text')
        text = ''
        if not _PAGE or sel:
            return {
                'ok': False,
                'message': 'Missing page or selector' }
        
        try:
            _PAGE.fill(sel, str(text), timeout = 10000)
            return {
                'ok': True,
                'selector': sel,
                'filled': True }
            return {
                'ok': False,
                'message': f'''Unknown action: {kind}''' }
        except Exception:
            exc = None
            del exc
            return None
            None = 
            del exc


