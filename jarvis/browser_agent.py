# Source Generated with Decompyle++
# File: browser_agent.cpython-312.pyc (Python 3.12)

'''Playwright browser agent with safety limits and human takeover.'''
from __future__ import annotations
import logging
import re
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from jarvis.p2_flags import browser_agent_enabled
log = logging.getLogger('jarvis.browser')
_BLOCKED_HOST_PATTERNS = ('paypal', 'checkout', 'stripe', 'buy\\.apple', 'amazon\\..*/gp/buy')
_BLOCKED_PATH = re.compile('|'.join(_BLOCKED_HOST_PATTERNS), re.I)
_DOWNLOAD_EXT = re.compile('\\.(exe|msi|dmg|apk|deb|rpm|zip|tar|gz|7z|pkg|app)$', re.I)
_STATE: 'dict[str, Any]' = {
    'status': 'idle',
    'url': '',
    'message': '',
    'paused': False,
    'takeover': False,
    'last_screenshot': '',
    'allow_downloads': False,
    'blocked_download': '' }
_LOCK = threading.Lock()
_PLAYWRIGHT = None
_BROWSER = None
_PAGE = None

def _playwright_available():
    browser_stack_ready = browser_stack_ready
    import jarvis.browser_playwright
    stack = browser_stack_ready()
    if stack.get('playwright'):
        stack.get('playwright')
    return bool(stack.get('chromium'))


def status():
    browser_stack_ready = browser_stack_ready
    import jarvis.browser_playwright
    stack = browser_stack_ready()
    _LOCK
    if stack.get('playwright'):
        stack.get('playwright')
# WARNING: Decompyle incomplete


def _check_url_safe(url = None, *, allow_risky):
    if allow_risky:
        return (True, '')
    parsed = urlparse(url)
    host_path = f'''{parsed.netloc}{parsed.path}'''
    if _BLOCKED_PATH.search(host_path):
        return (False, 'Blocked URL (checkout/payment) — confirm required for web_agent.')
    return (True, '')


def _check_download_safe(filename = None, *, allow_downloads):
    if allow_downloads:
        return (True, '')
    if not filename:
        filename
    name = ''.strip()
    if not name:
        return (False, 'Download blocked — confirm required.')
    if _DOWNLOAD_EXT.search(name):
        return (False, f'''Blocked download ({name}) — executable/archive requires confirm.''')
    return (None, f'''Download blocked ({name}) — enable allow_downloads or confirm web_agent.''')


def prepare_for_browser():
    prepare_for_browser_agent = prepare_for_browser_agent
    import jarvis.browser_vram
    return prepare_for_browser_agent(vision = False)


def _agent_paused():
    _LOCK
    if not _STATE.get('paused'):
        _STATE.get('paused')
    None(None, None)
    return 
    with None:
        if not None, bool(_STATE.get('takeover')):
            pass


def _set_message(msg = None):
    _LOCK
    _STATE['message'] = msg[:500]
    None(None, None)
    return None
    with None:
        if not None:
            pass


def pause():
    _LOCK
    _STATE['paused'] = True
    _STATE['status'] = 'paused'
    None(None, None)
    return status()
    with None:
        if not None:
            pass
    return status()


def resume():
    _LOCK
    _STATE['paused'] = False
    _STATE['takeover'] = False
    _STATE['status'] = 'running' if _STATE.get('url') else 'idle'
    None(None, None)
    return status()
    with None:
        if not None:
            pass
    return status()


def takeover():
    _LOCK
    _STATE['takeover'] = True
    _STATE['paused'] = True
    _STATE['status'] = 'takeover'
    _STATE['message'] = 'Human takeover — click in browser, then resume agent.'
    None(None, None)
    return status()
    with None:
        if not None:
            pass
    return status()


def stop():
    global _PAGE, _BROWSER, _PLAYWRIGHT
    _LOCK
    _STATE.update({
        'status': 'idle',
        'url': '',
        'message': '',
        'paused': False,
        'takeover': False })
    None(None, None)
    
    try:
        if _PAGE:
            _PAGE.close()
        if _BROWSER:
            _BROWSER.close()
        if _PLAYWRIGHT:
            _PLAYWRIGHT.stop()
        _PAGE = None
        _BROWSER = None
        _PLAYWRIGHT = None
        return status()
        with None:
            if not None:
                pass
        continue
    except Exception:
        continue



def _ensure_page():
    global _PLAYWRIGHT, _BROWSER, _PAGE
    if _PAGE:
        return _PAGE
    sync_playwright = sync_playwright
    import playwright.sync_api
    browser_session_dir = browser_session_dir
    import jarvis.active_project
    
    try:
        ensure_playwright = ensure_playwright
        import jarvis.browser_playwright
        ensure_playwright()
        prepare_for_browser()
        _PLAYWRIGHT = sync_playwright().start()
        _BROWSER = _PLAYWRIGHT.chromium.launch(headless = False)
        ctx = _BROWSER.new_context(storage_state = None)
        profile = Path(browser_session_dir()) / 'storage.json'
        if profile.is_file():
            
            try:
                ctx = _BROWSER.new_context(storage_state = str(profile))
                _PAGE = ctx.new_page()
                _wire_download_guard(_PAGE)
                return _PAGE
                except Exception:
                    continue
            except Exception:
                continue




def allow_downloads(enabled = None):
    _LOCK
    _STATE['allow_downloads'] = bool(enabled)
    if enabled:
        _STATE['blocked_download'] = ''
    None(None, None)
    return status()
    with None:
        if not None:
            pass
    return status()


def _wire_download_guard(page = None):
    
    def _on_download(download = None):
        if not download.suggested_filename:
            download.suggested_filename
        name = 'file'
        _LOCK
        allowed = bool(_STATE.get('allow_downloads'))
        None(None, None)
    # WARNING: Decompyle incomplete

    
    try:
        page.on('download', _on_download)
        return None
    except Exception:
        return None



def navigate(url = None, *, allow_risky):
    if not browser_agent_enabled():
        return {
            'ok': False,
            'message': 'Browser agent disabled' }
    (safe, reason) = None(url, allow_risky = allow_risky)
    if not safe:
        return {
            'ok': False,
            'message': reason,
            'needs_confirm': True }
# WARNING: Decompyle incomplete


def screenshot(dest = None):
    pass
# WARNING: Decompyle incomplete


def click_selector(selector = None):
    if _agent_paused():
        return {
            'ok': False,
            'message': 'Agent paused or in human takeover' }
    if not None:
        return {
            'ok': False,
            'message': 'No active browser page' }
    
    try:
        _PAGE.click(selector, timeout = 10000)
        return {
            'ok': True,
            'selector': selector }
    except Exception:
        exc = None
        del exc
        return None
        None = 
        del exc



def run_agent_task(goal = None, *, mode, max_steps, assistant):
    '''Multi-step browser agent (DOM and/or VLM).'''
    if not browser_agent_enabled():
        return {
            'ok': False,
            'message': 'Browser agent disabled' }
    if not None:
        pass
    goal = ''.strip()
    if not goal:
        return {
            'ok': False,
            'message': 'Goal required' }
    if not None and _playwright_available():
        return {
            'ok': False,
            'message': 'Open a page first (browse_web)' }
    steps = None
    if not mode:
        mode
    mode = 'auto'.lower()
    use_vlm = mode in ('vlm', 'auto', 'vision')
# WARNING: Decompyle incomplete


def save_session():
    if not _BROWSER:
        return None
    browser_session_dir = browser_session_dir
    import jarvis.active_project
    path = Path(browser_session_dir()) / 'storage.json'
    
    try:
        contexts = _BROWSER.contexts
        if contexts:
            contexts[0].storage_state(path = str(path))
            return None
        return None
    except Exception:
        exc = None
        log.debug('save session failed: %s', exc)
        exc = None
        del exc
        return None
        exc = None
        del exc


