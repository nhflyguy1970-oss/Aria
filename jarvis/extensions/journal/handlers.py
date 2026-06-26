# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''Journal action handlers.'''
from __future__ import annotations
import re
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok

def _task_disambiguation(candidates = None, hint = None):
    lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(candidates[:8]())
    prefix = f''' for “{hint}”''' if hint else ''
    return ok(f'''Which task{prefix}?\n{lines}\n\nSay the task name or include the bullet ID.''', module = 'journal')

journal_today = (lambda assistant = None, params = None, message = register_action('journal_today', module = 'journal', extension = 'journal', description = "Today's daily journal page"): if not params.get('day'):
params.get('day')day = ''if not day:
daypage = assistant.journal.format_page('daily', None)ok(page, module = 'journal'))()
journal_monthly = (lambda assistant = None, params = None, message = register_action('journal_monthly', module = 'journal', extension = 'journal', description = 'Monthly journal page'): _month_key = _month_keyimport jarvis.modules.journalif not params.get('month'):
params.get('month')month = _month_key()page = assistant.journal.format_page('monthly', month)ok(page, module = 'journal'))()
journal_open_tasks = (lambda assistant = None, params = None, message = register_action('journal_open_tasks', module = 'journal', extension = 'journal', description = 'Open journal tasks'): pass# WARNING: Decompyle incomplete
)()
journal_log = (lambda assistant = None, params = None, message = register_action('journal_log', module = 'journal', extension = 'journal', description = "Rapid log to today's journal"): if not params.get('text'):
params.get('text')text = messagetext = re.sub('^(log|journal|add to journal)[:\\s]+', '', text, flags = re.I).strip()bullets = assistant.journal.parse_rapid_log(text)lines = (lambda .0: pass# WARNING: Decompyle incomplete
)(bullets())
    return ok(f'''Added to today\'s log:\n\n{lines}''', module = 'journal')
)()
journal_reflect = (lambda assistant = None, params = None, message = register_action('journal_reflect', module = 'journal', extension = 'journal', description = 'AI reflection on journal'): if 'month' in message.lower():
passelif 'week' in message.lower():
passscope = 'today'reflection = assistant.journal.ai_reflect(scope)ok(reflection, module = 'journal'))()
journal_migrate = (lambda assistant = None, params = None, message = register_action('journal_migrate', module = 'journal', extension = 'journal', description = 'Migrate open tasks to next month'): _month_key = _month_keyimport jarvis.modules.journalmk = _month_key()(y, m) = map(int, mk.split('-'))nm = f'''{y:04d}-{m + 1:02d}''' if m < 12 else f'''{y + 1:04d}-01'''r = assistant.journal.migrate_month(mk, nm)ok(f'''Monthly migration: moved {r['migrated']} tasks to {nm}.''', module = 'journal'))()
journal_search = (lambda assistant = None, params = None, message = register_action('journal_search', module = 'journal', extension = 'journal', description = 'Search journal entries'): pass# WARNING: Decompyle incomplete
)()
journal_remember = (lambda assistant = None, params = None, message = register_action('journal_remember', module = 'journal', extension = 'journal', description = 'Save journal bullet to memory'): pass# WARNING: Decompyle incomplete
)()
journal_schedule = (lambda assistant = None, params = None, message = register_action('journal_schedule', module = 'journal', extension = 'journal', description = 'Schedule open task to future month'): _month_key = _month_keyimport jarvis.modules.journalif not params.get('month'):
params.get('month')month = _month_key()(task, candidates, hint) = assistant.journal.match_open_task(message, bullet_id = params.get('bullet_id'), task_query = params.get('task_query'))if not task:
if not candidates:
ok('No open tasks to schedule.', module = 'journal')None(candidates, hint)b = None.journal.bullet_schedule(task['id'], month)if not b:
err('Could not schedule task.')None(f'''Scheduled to future log ({month}): {b.get('content', '')}''', module = 'journal'))()
journal_thread = (lambda assistant = None, params = None, message = register_action('journal_thread', module = 'journal', extension = 'journal', description = 'Thread/migrate task to daily log'): _today = _todayimport jarvis.modules.journalif not params.get('day'):
params.get('day')day = _today()dup = params.get('duplicate') in (True, 'true', '1')(task, candidates, hint) = assistant.journal.match_open_task(message, bullet_id = params.get('bullet_id'), task_query = params.get('task_query'))if not task:
if not candidates:
ok('No open tasks to thread.', module = 'journal')None(candidates, hint)b = None.journal.bullet_thread_to_daily(task['id'], day, duplicate = dup)if not b:
err('Could not thread task to daily log.')verb = 'Copied' if None else 'Migrated'ok(f'''{verb} to {day}: {b.get('content', '')}''', module = 'journal'))()
journal_review = (lambda assistant = None, params = None, message = register_action('journal_review', module = 'journal', extension = 'journal', description = 'AI summary after review checklist'): scope = 'week' if 'week' in message.lower() else 'month'text = assistant.journal.ai_reflect_review(scope)ok(text, module = 'journal'))()
