# Source Generated with Decompyle++
# File: experience_memory.cpython-312.pyc (Python 3.12)

'''Experience memory — durable successes and failures for learning from outcomes.'''
from __future__ import annotations
import re
from jarvis import llm
EXPERIENCE_NAMESPACE = 'experience'
EXPERIENCE_TYPES = ('success', 'failure')
_TASK_HINTS = re.compile('\\b(fix|debug|implement|refactor|test|pytest|error|failed|worked|approach|image|comfy|generate|coding|script|module|tool)\\b', re.I)
_SUCCESS_REMEMBER = re.compile('^(?:please\\s+)?(?:remember\\s+)?(?:that\\s+)?(?:this|that)\\s+worked\\s*(?::|-)?\\s*(.*)$', re.I | re.S)
_FAILURE_REMEMBER = re.compile('^(?:please\\s+)?(?:remember\\s+)?(?:that\\s+)?(?:this|that)\\s+failed\\s*(?::|-)?\\s*(.*)$', re.I | re.S)
_SUCCESS_PREFIX = re.compile('^(?:remember\\s+)?success\\s*:\\s*', re.I)
_FAILURE_PREFIX = re.compile('^(?:remember\\s+)?failure\\s*:\\s*', re.I)
_RECALL_QUERY = re.compile('^(?:please\\s+)?(?:what|show|list|recall)\\s+(?:(?:past|previous)\\s+)?(?:(?:experiences?|outcomes?)\\s+)?(?:for|about|with|on)\\s+(.+)$|^(?:please\\s+)?(?:what worked|what failed|past failures|past successes)\\s*(?:for|with|on)?\\s*(.*)$', re.I)

def _format_content(*, outcome, task, detail, module, context):
    label = 'Succeeded' if outcome == 'success' else 'Failed'
    parts = []
    if module:
        parts.append(f'''[{module}]''')
    if task:
        parts.append(task.strip()[:160])
    if not detail.strip()[:500]:
        detail.strip()[:500]
        if not task.strip()[:500]:
            task.strip()[:500]
    body = 'unspecified'
    if context:
        parts.append(f'''({context.strip()[:120]})''')
    head = ' '.join(parts).strip()
    if head:
        return f'''{label}: {head} — {body}'''
    return f'''{None}: {body}'''


def record_experience(store = None, *, outcome, task, detail, module, context, namespace, tags):
    '''Store a success or failure experience.'''
    outcome = outcome if outcome in EXPERIENCE_TYPES else 'failure'
    content = _format_content(outcome = outcome, task = task, detail = detail, module = module, context = context)
    if store.similar_exists(content, entry_type = outcome, namespace = namespace, tags_include = [
        f'''outcome-{outcome}''']):
        return None
    entry_tags = [
        'experience',
        f'''outcome-{outcome}''']
    if module:
        entry_tags.append(module)
    if tags:
        for tag in tags:
            if not tag not in entry_tags:
                continue
            entry_tags.append(tag)
    return store.add(outcome, content, tags = entry_tags, namespace = namespace)


def record_failure(store = None, *, path, error, task, namespace):
    if not error:
        error
    excerpt = ''.strip()[:500]
    if not excerpt and path:
        return None
    if not excerpt:
        excerpt
    if not namespace:
        namespace
    return record_experience(store, outcome = 'failure', task = task, detail = 'unknown error', module = 'coding', context = path, namespace = EXPERIENCE_NAMESPACE, tags = [
        'coding'])


def record_success(store = None, *, paths, task, detail, module, note, namespace):
    context = ''
    if paths:
        context = (lambda .0: pass# WARNING: Decompyle incomplete
)(paths[:4]())
    if not detail:
        detail
    body = note
    if body and context:
        body = f'''verified for {context}'''
    if not body and task:
        return None
    if not namespace:
        namespace
    if module == 'coding':
        return record_experience(store, outcome = 'success', task = task, detail = body, module = module, context = context, namespace = EXPERIENCE_NAMESPACE, tags = [
            'coding'])
    return None(record_experience, outcome = store, task = 'success', detail = task, module = body, context = module, namespace = context, tags = EXPERIENCE_NAMESPACE)


def record_tool_outcome(store = None, *, action, detail, ok, namespace):
    if not ok or action:
        return None
    if not detail:
        detail
    snippet = action[:120]
    return record_experience(store, outcome = 'success', task = action, detail = snippet, module = 'tool', namespace = namespace, tags = [
        'tool-outcome',
        action])


def parse_experience_remember(text = None):
    '''Parse user phrases → (outcome, detail).'''
    if not text:
        text
    raw = ''.strip()
    if not raw:
        return None
    m = _SUCCESS_REMEMBER.match(raw)
    if m:
        if not m.group(1):
            m.group(1)
        return ('success', 'user noted this worked'.strip())
    m = None.match(raw)
    if m:
        if not m.group(1):
            m.group(1)
        return ('failure', 'user noted this failed'.strip())
    if None.match(raw):
        return ('success', _SUCCESS_PREFIX.sub('', raw, count = 1).strip())
    if None.match(raw):
        return ('failure', _FAILURE_PREFIX.sub('', raw, count = 1).strip())


def parse_experience_recall_query(message = None):
    if not message:
        message
    m = _RECALL_QUERY.match(''.strip())
    if not m:
        return ''
    if not m.group(1):
        m.group(1)
        if not m.group(2):
            m.group(2)
    return ''.strip()


def list_experiences(store = None, *, outcome, limit):
    filter_entry_list = filter_entry_list
    import jarvis.trust_memory
    types = [
        outcome] if outcome in EXPERIENCE_TYPES else list(EXPERIENCE_TYPES)
    entries = []
    seen = set()
    for entry_type in types:
        for e in store.list_entries(entry_type = entry_type, namespace = EXPERIENCE_NAMESPACE):
            if not e.get('id') not in seen:
                continue
            seen.add(e['id'])
            entries.append(e)
        for e in store.list_entries(entry_type = entry_type, namespace = 'jarvis'):
            if not e.get('id') not in seen:
                continue
            seen.add(e['id'])
            entries.append(e)
    entries.sort(key = (lambda e: e.get('timestamp', '')), reverse = True)
    return filter_entry_list(entries[:limit])


def recall_experiences(store = None, query = None, *, limit):
    filter_entry_list = filter_entry_list
    import jarvis.trust_memory
    if not query:
        query
    q = ''.strip()
    if not q:
        return list_experiences(store, limit = limit)
    hits = None
    seen = set()
    if llm.embed_available():
        for ns in (EXPERIENCE_NAMESPACE, 'jarvis', None):
            for e in store.search(q, limit = limit, namespace = ns):
                if e.get('type') not in EXPERIENCE_TYPES or e.get('id') in seen:
                    continue
                seen.add(e['id'])
                hits.append(e)
    if not hits:
        ql = q.lower()
        for e in list_experiences(store, limit = limit * 3):
            if not ql in e.get('content', '').lower():
                continue
            hits.append(e)
    return filter_entry_list(hits[:limit])


def experience_stats(store = None):
    successes = list_experiences(store, outcome = 'success', limit = 500)
    failures = list_experiences(store, outcome = 'failure', limit = 500)
    return {
        'successes': len(successes),
        'failures': len(failures),
        'namespace': EXPERIENCE_NAMESPACE }


def experience_context_for_action(store = None, query = None, *, limit):
    '''Inject relevant past experiences before coding, image gen, or tool runs.'''
    filter_trusted_content = filter_trusted_content
    import jarvis.trust_memory
    if not query:
        query
    text = ''.strip()
    if len(text) < 4:
        return ''
    hits = recall_experiences(store, text, limit = limit)
    if not hits:
        return ''
    lines = []
    for e in hits:
        line = filter_trusted_content(e.get('content', ''))
        if not line:
            continue
        lines.append(f'''- [{e.get('type', 'experience')}] {line}''')
    if not lines:
        return ''
    return 'Relevant past experiences (learn from these):\n' + '\n'.join(lines)


def experience_context_for_chat(store = None, message = None, *, limit):
    '''Inject relevant past successes/failures when the user is doing similar work.'''
    filter_trusted_content = filter_trusted_content
    import jarvis.trust_memory
    if not message:
        message
    text = ''.strip()
    if not len(text) < 8 or _TASK_HINTS.search(text):
        return ''
    hits = recall_experiences(store, text, limit = limit)
    if not hits:
        return ''
    lines = []
    for e in hits:
        line = filter_trusted_content(e.get('content', ''))
        if not line:
            continue
        lines.append(f'''- [{e.get('type', 'experience')}] {line}''')
    if not lines:
        return ''
    return 'Past experiences (learn from these — do not repeat failures):\n' + '\n'.join(lines)

