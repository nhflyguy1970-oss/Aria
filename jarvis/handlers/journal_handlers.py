# Source Generated with Decompyle++
# File: journal_handlers.cpython-312.pyc (Python 3.12)

'''Journal read handlers.'''
from __future__ import annotations
from jarvis.handlers.registry import register_action
from jarvis.response import ok
journal_today = (lambda assistant = None, params = None, message = register_action('journal_today', module = 'journal', description = "Today's daily journal page"): if not params.get('day'):
params.get('day')day = ''if not day:
daypage = assistant.journal.format_page('daily', None)ok(page, module = 'journal'))()
journal_monthly = (lambda assistant = None, params = None, message = register_action('journal_monthly', module = 'journal', description = 'Monthly journal page'): _month_key = _month_keyimport jarvis.modules.journalif not params.get('month'):
params.get('month')month = _month_key()page = assistant.journal.format_page('monthly', month)ok(page, module = 'journal'))()
journal_open_tasks = (lambda assistant = None, params = None, message = register_action('journal_open_tasks', module = 'journal', description = 'Open journal tasks'): pass# WARNING: Decompyle incomplete
)()
