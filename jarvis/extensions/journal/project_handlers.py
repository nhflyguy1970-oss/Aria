# Source Generated with Decompyle++
# File: project_handlers.cpython-312.pyc (Python 3.12)

'''Project journal handlers.'''
from __future__ import annotations
import re
from jarvis.handlers.registry import register_action
from jarvis.response import err, ok

def _project_slug(assistant = None, params = None, message = None):
    resolve_project = resolve_project
    import jarvis.project_journal
    if not params.get('project'):
        params.get('project')
    return resolve_project(message, explicit = ''.strip(), session_namespace = assistant.session.memory_namespace)

project_journal_list = (lambda assistant = None, params = None, message = register_action('project_journal_list', module = 'journal', extension = 'journal', description = 'List project journals'): list_projects = list_projectsimport jarvis.project_journalprojects = list_projects()if not projects:
ok('No project journals yet. Say **log to jarvis project journal: shipped auth module**.', module = 'journal')# WARNING: Decompyle incomplete
)()
project_journal_today = (lambda assistant = None, params = None, message = register_action('project_journal_today', module = 'journal', extension = 'journal', description = "Today's project journal"): ProjectJournal = ProjectJournalimport jarvis.project_journalslug = _project_slug(assistant, params, message)if not params.get('day'):
params.get('day')if not ''.strip():
''.strip()day = Nonejournal = ProjectJournal(slug)journal.ensure(title = slug)page = journal.format_daily(day)ok(page, module = 'journal', project = slug))()
project_journal_log = (lambda assistant = None, params = None, message = register_action('project_journal_log', module = 'journal', extension = 'journal', description = 'Log to project journal'): ProjectJournal = ProjectJournalparse_project_log_text = parse_project_log_textimport jarvis.project_journalslug = _project_slug(assistant, params, message)if not params.get('text'):
params.get('text')if not parse_project_log_text(message):
parse_project_log_text(message)text = ''.strip()text = re.sub('^(log|journal|project log)[:\\s]+', '', text, flags = re.I).strip()if not text:
err('What should I log? Example: **log to jarvis project journal: fixed router bug**', module = 'journal')journal = ProjectJournal(slug)journal.ensure(title = slug)if not params.get('bullet_type'):
params.get('bullet_type')bullet_type = 'note'.strip().lower()bullet = journal.daily_add(text, bullet_type = bullet_type)assistant.session.note_memory_namespace(slug)auto_journal_learn_enabled = auto_journal_learn_enabledimport jarvis.brain_memoryauto = auto_journal_learn_enabled()learn_note = ''if auto:
learn_from_project_journal = learn_from_project_journalimport jarvis.journal_learninglr = learn_from_project_journal(assistant.memory, slug)if lr.get('ok'):
if not lr.get('facts'):
lr.get('facts')learn_note = f'''\n\n_Auto-learned {len([])} item(s)._'''assistant.refresh_system_prompt()if not journal.data.get('title'):
journal.data.get('title')ok(f'''Logged to **{slug}** journal:\n\n• {bullet['content']}{learn_note}''', module = 'journal', project = slug))()
project_journal_daily_update = (lambda assistant = None, params = None, message = register_action('project_journal_daily_update', module = 'journal', extension = 'journal', description = 'Update project journal daily'): update_all_project_journals = update_all_project_journalsupdate_project_journal_daily = update_project_journal_dailyimport jarvis.project_journal_dailyif not params.get('project'):
params.get('project')slug = ''.strip()if not slug:
m = re.search('\\bupdate\\s+([\\w-]+)\\s+project journal\\b', message, re.I)if re.search('\\bupdate\\s+([\\w-]+)\\s+project journal\\b', message, re.I):
slug = m.group(1)elif 'all project' in message.lower():
slug = ''else:
slug = _project_slug(assistant, params, message)if not params.get('phase'):
params.get('phase')phase = 'morning'.strip().lower()if 'evening' in message.lower() or 'wrap' in message.lower():
phase = 'evening'if not params.get('force'):
params.get('force')if not ''.lower() in ('1', 'true', 'yes'):
''.lower() in ('1', 'true', 'yes')force = 'force' in message.lower()if slug and slug not in ('all', 'projects'):
result = update_project_journal_daily(slug, phase = phase, force = force, memory = assistant.memory)if not result.get('ok'):
err(result.get('message', 'Update failed.'), module = 'journal')if None.get('skipped'):
ok(f'''**{slug}** project journal already updated ({phase}).''', module = 'journal')body = None.get('message', 'Updated.')if not result.get('bullets'):
result.get('bullets')bullets = []if bullets:
None += '\n'.join + (lambda .0: pass# WARNING: Decompyle incomplete
)(bullets())
        if result.get('learned'):
            assistant.refresh_system_prompt()
            body += f'''\n\n_Auto-learned {result['learned']} item(s)._'''
        return ok(body, module = 'journal', project = slug)
    results = update_all_project_journals(phase = phase, force = force, memory = assistant.memory)
# WARNING: Decompyle incomplete
)()
journal_learn = (lambda assistant = None, params = None, message = register_action('journal_learn', module = 'journal', extension = 'journal', description = 'Learn from journal pages'): format_learnings_markdown = format_learnings_markdownlearn_from_main_journal = learn_from_main_journallearn_from_project_journal = learn_from_project_journalimport jarvis.journal_learningresolve_project = resolve_projectimport jarvis.project_journalif not params.get('project'):
params.get('project')project = ''.strip()if not project:
m = re.search('\\blearn from\\s+([\\w-]+)\\s+(?:project\\s+)?journal\\b', message, re.I)if re.search('\\blearn from\\s+([\\w-]+)\\s+(?:project\\s+)?journal\\b', message, re.I):
project = m.group(1)elif 'project journal' in message.lower():
project = resolve_project(message, session_namespace = assistant.session.memory_namespace)else:
project = ''if not params.get('day'):
params.get('day')if not ''.strip():
''.strip()day = Noneif project and project not in ('main', 'today', 'journal'):
result = learn_from_project_journal(assistant.memory, project, day = day, namespace = project)else:
result = learn_from_main_journal(assistant.memory, day = day)if not result.get('ok'):
err(result.get('message', 'Could not learn from journal.'), module = 'journal')None.refresh_system_prompt()if not result.get('facts'):
result.get('facts')facts = []body = result['message']# WARNING: Decompyle incomplete
)()
journal_learn_recall = (lambda assistant = None, params = None, message = register_action('journal_learn_recall', module = 'journal', extension = 'journal', description = 'Recall journal learnings'): format_learnings_markdown = format_learnings_markdownlist_journal_learnings = list_journal_learningsparse_journal_learn_recall_query = parse_journal_learn_recall_queryimport jarvis.journal_learningif not params.get('query'):
params.get('query')if not parse_journal_learn_recall_query(message):
parse_journal_learn_recall_query(message)query = ''.strip()project = _project_slug(assistant, params, message) if not query or params.get('project') else ''.strip()if project in ('default', 'main'):
project = ''entries = list_journal_learnings(assistant.memory, query = query, project = project)if not entries:
ok('No journal learnings yet. Log to a **project journal** and say **learn from project journal**.', module = 'journal')title = f'''Journal learnings about **{query}**''' if None else 'Journal learnings'ok(title + '\n\n' + format_learnings_markdown(entries), module = 'journal'))()
