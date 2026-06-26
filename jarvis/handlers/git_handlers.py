# Source Generated with Decompyle++
# File: git_handlers.cpython-312.pyc (Python 3.12)

'''Git status / diff handlers.'''
from __future__ import annotations
from jarvis.handlers.registry import register_action
from jarvis.response import ok
git_status = (lambda assistant = None, params = None, message = register_action('git_status', module = 'coding', description = 'Git working tree status'): git_util = git_utilimport jarvisok(f'''```\n{git_util.status()}\n```''', module = 'coding'))()
git_diff = (lambda assistant = None, params = None, message = register_action('git_diff', module = 'coding', description = 'Git diff for file or repo'): git_util = git_utilimport jarvisf = params.get('file', '')if not f:
fd = git_util.diff(file = None)ok(f'''```diff\n{d[:8000]}\n```''', module = 'coding'))()
