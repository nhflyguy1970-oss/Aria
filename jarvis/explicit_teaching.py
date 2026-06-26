# Source Generated with Decompyle++
# File: explicit_teaching.cpython-312.pyc (Python 3.12)

'''Explicit teaching — deliberate lessons the user teaches ARIA.'''
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any
from jarvis import llm
TEACHING_NAMESPACE = 'teaching'
EXPLICIT_TEACH_TAG = 'explicit-teach'
TEACHING_KINDS = ('fact', 'rule', 'preference', 'procedure', 'relationship', 'skill')
_TEACH_TYPED = re.compile('^(?:please\\s+)?teach\\s+(?:aria|jarvis)?\\s*(fact|rule|preference|procedure|relationship|skill)\\s*:\\s*(.+)$', re.I | re.S)
_TEACH_THAT = re.compile('^(?:please\\s+)?teach\\s+(?:aria|jarvis)\\s+(?:that\\s+)?(.+)$', re.I | re.S)
_TEACH_BARE = re.compile('^(?:please\\s+)?teach\\s+(?:aria|jarvis)?\\s+(.+)$', re.I | re.S)
_RECALL = re.compile('\\b(?:what did i teach|what have i taught|recall (?:my )?teaching|taught you about)\\b', re.I)
_RECALL_QUERY = re.compile('(?:what did i teach(?: you)?(?: about)?|what have i taught(?: you)?(?: about)?|recall (?:my )?teaching(?: about)?|taught you about)\\s+(.+)$', re.I)
_RULE_MARKERS = re.compile("\\b(always|never|must|should not|don't|do not|when answering|when i ask)\\b", re.I)
_PROCEDURE_MARKERS = re.compile('\\b(first|then|step\\s*\\d|steps?:|to deploy|to fix|to run|how to)\\b', re.I)
TeachIntent = <NODE:12>()
TeachResult = <NODE:12>()

def _kind_tag(kind = None):
    if not kind:
        kind
    k = 'fact'.lower()
    if k in TEACHING_KINDS:
        return f'''teach-{k}'''


def _format_lesson(kind = None, content = None):
    label = kind.capitalize()
    if not content:
        content
    body = ''.strip()
    if body.lower().startswith(f'''[{kind}]'''):
        return body
    return f'''{label}] {body}'''


def infer_teaching_kind(content = None):
    if not content:
        content
    text = ''.strip()
    lower = text.lower()
    if _PROCEDURE_MARKERS.search(lower):
        return 'procedure'
    if _RULE_MARKERS.search(lower):
        return 'rule'
    if re.search('\\b(prefer|preference|likes? to)\\b', lower):
        return 'preference'
    if re.search('\\b(works on|uses|knows|related to|connected to)\\b', lower):
        return 'relationship'
    if re.search('\\b(when i|use tool|call action|route to)\\b', lower):
        return 'skill'
    return 'fact'


def parse_teach_message(message = None):
    if not message:
        message
    raw = ''.strip()
    if not raw:
        return None
    m = _TEACH_TYPED.match(raw)
    if m:
        kind = m.group(1).lower()
        content = m.group(2).strip()
        if content:
            return TeachIntent(kind = kind, content = content, raw = raw)
        m = None.match(raw)
        if m:
            content = m.group(1).strip()
            if content:
                return TeachIntent(kind = infer_teaching_kind(content), content = content, raw = raw)
            m = None.match(raw)
            if m:
                content = m.group(1).strip()
                if not content and _RECALL.search(content):
                    return TeachIntent(kind = infer_teaching_kind(content), content = content, raw = raw)


def is_teach_recall(message = None):
    if not message:
        message
    return bool(_RECALL.search(''.strip()))


def parse_teach_recall_query(message = None):
    if not message:
        message
    m = _RECALL_QUERY.search(''.strip())
    if m:
        return m.group(1).strip().rstrip('?.!')
    return None.rstrip('?.!')


def _teaching_tags(kind = None):
    return [
        EXPLICIT_TEACH_TAG,
        _kind_tag(kind),
        'user-taught']


def apply_explicit_teaching(memory = None, intent = None, *, namespace, extra_tags):
    '''Store an explicit lesson and mirror into specialized memory layers.'''
    kind = intent.kind if intent.kind in TEACHING_KINDS else 'fact'
    content = intent.content.strip()
    if not namespace:
        namespace
    if not TEACHING_NAMESPACE.strip():
        TEACHING_NAMESPACE.strip()
    ns = TEACHING_NAMESPACE
    lesson = _format_lesson(kind, content)
    mirrors = []
    if not extra_tags:
        extra_tags
# WARNING: Decompyle incomplete


def list_teachings(memory = None, *, query, kind, limit):
    pass
# WARNING: Decompyle incomplete


def teaching_stats(memory = None):
    entries = list_teachings(memory, limit = 500)
    by_kind = { }
    for e in entries:
        if not e.get('tags'):
            e.get('tags')
        tags = []
        kind = (lambda .0: pass# WARNING: Decompyle incomplete
)(tags(), 'fact')
        by_kind[kind] = by_kind.get(kind, 0) + 1
    return {
        'total': len(entries),
        'namespace': TEACHING_NAMESPACE,
        'by_kind': by_kind }


def explicit_teaching_system_block(memory = None, *, max_items):
    filter_trusted_content = filter_trusted_content
    import jarvis.trust_memory
    entries = list_teachings(memory, limit = max_items)
    lines = []
    for e in entries:
        line = filter_trusted_content(e.get('content', ''))
        if not line:
            continue
        lines.append(f'''- {line}''')
    if not lines:
        return ''
    return 'Explicit teachings (user-taught — follow these):\n' + '\n'.join(lines)


def explicit_teaching_context_for_chat(memory = None, message = None, *, limit):
    pass
# WARNING: Decompyle incomplete


def format_teachings_markdown(entries = None):
    if not entries:
        return '_No explicit teachings stored yet._'
    lines = []
    for e in entries:
        if not e.get('tags'):
            e.get('tags')
        tags = []
        kind = (lambda .0: pass# WARNING: Decompyle incomplete
)(tags(), 'fact')
        lines.append(f'''• **[{kind}]** {e.get('content', '')}''')
    return '\n'.join(lines)

