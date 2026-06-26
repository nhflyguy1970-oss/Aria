# Source Generated with Decompyle++
# File: journal_learning.cpython-312.pyc (Python 3.12)

'''Learn durable facts from bullet and project journal pages.'''
from __future__ import annotations
import json
import logging
import os
import re
from typing import Any
from jarvis import llm
from jarvis.memory_context import normalize_journal_memory_text
log = logging.getLogger('jarvis.journal_learning')
JOURNAL_LEARN_NAMESPACE = 'journal-learned'
JOURNAL_LEARN_TAG = 'journal-learn'
_MAX_CHARS = int(os.getenv('JARVIS_JOURNAL_LEARN_CHARS', '10000'))
_MAX_FACTS = int(os.getenv('JARVIS_JOURNAL_LEARN_FACTS', '8'))
_LEARN_JOURNAL = re.compile("\\b(learn from (?:today'?s? |my )?journal|remember (?:from )?(?:today'?s? )?journal|journal learn|learn from project journal)\\b", re.I)
_LEARN_PROJECT = re.compile('\\blearn from\\s+([\\w-]+)\\s+(?:project\\s+)?journal\\b', re.I)
_RECALL = re.compile('\\b(what did (?:i|we) (?:log|write) in (?:the )?journal|journal (?:learning )?recall|what did i learn from (?:the )?journal)\\b', re.I)
_RECALL_QUERY = re.compile('(?:what did (?:i|we) (?:log|write) in (?:the )?journal(?: about)?|journal (?:learning )?recall(?: about)?|what did i learn from (?:the )?journal(?: about)?)\\s+(.+)$', re.I)

def is_journal_learn(message = None):
    if not message:
        message
    text = ''.strip()
    if re.search('\\b(remember (this )?bullet|save journal to memory|remember journal entry)\\b', text, re.I):
        return False
    if not _LEARN_JOURNAL.search(text):
        _LEARN_JOURNAL.search(text)
    return bool(_LEARN_PROJECT.search(text))


def is_journal_learn_recall(message = None):
    if not message:
        message
    return bool(_RECALL.search(''.strip()))


def parse_journal_learn_recall_query(message = None):
    if not message:
        message
    m = _RECALL_QUERY.search(''.strip())
    if m:
        return m.group(1).strip().rstrip('?.!')
    return None.rstrip('?.!')


def _parse_facts_from_llm(raw = None, *, limit):
    pass
# WARNING: Decompyle incomplete


def extract_journal_learnings(text = None, *, project, day, max_facts):
    if not text:
        text
    excerpt = ''.strip()
    if not excerpt:
        return []
    if None(excerpt) > _MAX_CHARS:
        excerpt = excerpt[-_MAX_CHARS:]
# WARNING: Decompyle incomplete


def _store_learnings(memory = None, facts = None, *, project, day, namespace):
    if not namespace:
        namespace
        if not project:
            project
    if not JOURNAL_LEARN_NAMESPACE.strip():
        JOURNAL_LEARN_NAMESPACE.strip()
    ns = JOURNAL_LEARN_NAMESPACE
    if ns == 'default':
        ns = JOURNAL_LEARN_NAMESPACE
    location = f'''project:{project}:daily:{day}''' if project else f'''daily:{day}'''
    stored = []
    proj_tag = f'''project:{project[:32]}''' if project else 'project:main'
    for fact in facts:
        body = fact.strip()
        if not body:
            continue
        normalized = normalize_journal_memory_text(f'''From bullet journal ({location}): {body}''')
        if memory.similar_exists(normalized, namespace = ns):
            continue
        memory.add('fact', normalized, tags = [
            JOURNAL_LEARN_TAG,
            proj_tag,
            f'''journal-day:{day}'''], namespace = ns)
        stored.append(normalized)
    return stored
    except ValueError:
        exc = None
        log.debug('Skip journal learning: %s', exc)
        exc = None
        del exc
        continue
        exc = None
        del exc


def learn_from_text(memory = None, text = None, *, project, day, namespace):
    facts = extract_journal_learnings(text, project = project, day = day)
    if not facts:
        return {
            'ok': False,
            'message': 'Nothing substantive to learn from that journal page.',
            'facts': [] }
    stored = None(memory, facts, project = project, day = day, namespace = namespace)
    return {
        'ok': True,
        'message': f'''Learned **{len(stored)}** item(s) from journal.''',
        'facts': stored,
        'project': project,
        'day': day }


def extract_and_store(memory = None, text = None, *, project, day, namespace, max_facts):
    '''Lightweight extract+store for auto-feed hooks (reuses journal LLM prompts).'''
    if not text:
        text
    excerpt = ''.strip()
    if len(excerpt) < 12:
        return {
            'ok': False,
            'facts': [] }
    facts = None(excerpt, project = project, day = day, max_facts = max_facts)
    if not facts:
        return {
            'ok': False,
            'facts': [] }
    stored = None(memory, facts, project = project, day = day, namespace = namespace)
    return {
        'ok': True,
        'facts': stored,
        'project': project,
        'day': day }


def learn_from_project_journal(memory = None, project = None, *, day, namespace):
    ProjectJournal = ProjectJournal
    import jarvis.project_journal
    store = ProjectJournal(project)
    if not day:
        day
    d = __import__('jarvis.modules.journal', fromlist = [
        '_today'])._today()
    page = store.daily_get(d)
    if not page.get('bullets'):
        page.get('bullets')
    bullets = []
    if not page.get('notes'):
        page.get('notes')
    notes = ''.strip()
    if not bullets and notes:
        return {
            'ok': False,
            'message': f'''No journal entries for **{store.slug}** on {d}.''',
            'facts': [] }
    text = None.page_text(d)
    result = learn_from_text(memory, text, project = store.slug, day = d, namespace = namespace)
    if result.get('ok'):
        store.daily_mark_learned(d)
    return result


def learn_from_main_journal(memory = None, *, day, namespace):
    BulletJournal = BulletJournal
    _format_bullet = _format_bullet
    _today = _today
    import jarvis.modules.journal
    journal = BulletJournal()
    if not day:
        day
    d = _today()
    page = journal.daily_get(d, enrich = False)
    parts = [
        f'''Main bullet journal — {d}''']
    if not page.get('bullets'):
        page.get('bullets')
    for b in []:
        parts.append(_format_bullet(b))
    if not page.get('gratitude'):
        page.get('gratitude')
    for line in []:
        if not line:
            continue
        parts.append(f'''Gratitude: {line}''')
    if not page.get('prompts'):
        page.get('prompts')
    prompts = { }
    if prompts.get('morning'):
        parts.append(f'''Morning: {prompts['morning']}''')
    if prompts.get('evening'):
        parts.append(f'''Evening: {prompts['evening']}''')
    text = '\n'.join(parts)
    if not namespace:
        namespace
    return learn_from_text(memory, text, project = 'main', day = d, namespace = JOURNAL_LEARN_NAMESPACE)


def list_journal_learnings(memory = None, *, query, project, limit):
    entries = memory.list_entries(namespace = JOURNAL_LEARN_NAMESPACE)
# WARNING: Decompyle incomplete


def journal_learning_context_for_chat(memory = None, message = None, *, limit):
    pass
# WARNING: Decompyle incomplete


def format_learnings_markdown(entries = None):
    if not entries:
        return '_No journal learnings stored yet._'
    return (lambda .0: pass# WARNING: Decompyle incomplete
)(entries())

