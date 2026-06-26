# Source Generated with Decompyle++
# File: correction_learning.cpython-312.pyc (Python 3.12)

"""Correction learning — remember when the user fixes ARIA's mistakes."""
from __future__ import annotations
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any
from jarvis import llm
from jarvis.config import DATA_DIR
log = logging.getLogger('jarvis.correction_learning')
CORRECTION_NAMESPACE = 'corrections'
CORRECTION_TAG = 'correction-learn'
REGISTRY_FILE = DATA_DIR / 'correction_learning.json'
_CORRECTION_MARKERS = re.compile("\\b(that'?s wrong|you'?re wrong|you are wrong|that is wrong|that is incorrect|that'?s incorrect|you'?re mistaken|not what i (?:asked|meant|wanted)|don'?t say that|you made a mistake|you got (?:it|that) wrong|no,?\\s+that'?s not|actually,?\\s+no\\b)\\b", re.I)
_CORRECTION_RECALL = re.compile('\\b(what (?:did i|have i) correct(?:ed)?|what corrections? did i make|correction recall|what did i fix (?:that )?you (?:said|got wrong))\\b', re.I)
_CORRECTION_RECALL_QUERY = re.compile('(?:what (?:did i|have i) correct(?:ed)?(?: about)?|what corrections? did i make(?: about)?|correction recall(?: about)?|what did i fix (?:that )?you (?:said|got wrong)(?: about)?)\\s+(.+)$', re.I)
_WRONG_ABOUT = re.compile("^(?:no,?\\s+)?(?:you'?re|you are)\\s+wrong\\s+about\\s+(.+?)[:\\s—-]+(.+)$", re.I | re.S)
_NOT_BUT = re.compile("^(?:no,?\\s+)?(?:not|it'?s not)\\s+(.+?)\\s*,?\\s*(?:it'?s|but)\\s+(.+)$", re.I | re.S)
_ACTUALLY = re.compile('^(?:no,?\\s+)?actually,?\\s+(.+)$', re.I | re.S)
CorrectionIntent = <NODE:12>()
CorrectionResult = <NODE:12>()

def _utc_now():
    datetime = datetime
    timezone = timezone
    import datetime
    return datetime.now(timezone.utc).isoformat()


def _load_registry():
    if not REGISTRY_FILE.is_file():
        return {
            'corrections': [] }
    
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding = 'utf-8'))
        if isinstance(data, dict) and isinstance(data.get('corrections'), list):
            return data
        return {
            None: [] }
    except (json.JSONDecodeError, OSError):
        exc = None
        log.warning('Corrupt correction registry: %s', exc)
        exc = None
        del exc
        return {
            'corrections': [] }
        exc = None
        del exc



def _save_registry(data = None):
    REGISTRY_FILE.parent.mkdir(parents = True, exist_ok = True)
    assert_live_write_allowed = assert_live_write_allowed
    import jarvis.live_data_guard
    assert_live_write_allowed(REGISTRY_FILE)
    REGISTRY_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def _register_correction(*, correction, wrong_claim, kind, module):
    sid = hashlib.sha256(f'''{correction}|{wrong_claim}|{time.time()}'''.encode()).hexdigest()[:12]
    data = _load_registry()
    data['corrections'] = None[:300]
    _save_registry(data)
    return sid


def correction_stats():
    items = _load_registry().get('corrections', [])
    by_kind = { }
    for item in items:
        if not item.get('kind'):
            item.get('kind')
        k = 'fact'
        by_kind[k] = by_kind.get(k, 0) + 1
    return {
        'total': len(items),
        'namespace': CORRECTION_NAMESPACE,
        'by_kind': by_kind }


def is_correction_message(message = None):
    if not message:
        message
    text = ''.strip()
    if not text:
        return False
    if parse_correction(text):
        return True
    return bool(_CORRECTION_MARKERS.search(text))


def is_correction_recall(message = None):
    if not message:
        message
    return bool(_CORRECTION_RECALL.search(''.strip()))


def parse_correction_recall_query(message = None):
    if not message:
        message
    m = _CORRECTION_RECALL_QUERY.search(''.strip())
    if m:
        return m.group(1).strip().rstrip('?.!')
    return None.rstrip('?.!')


def infer_correction_kind(correction = None):
    if not correction:
        correction
    lower = ''.lower()
    if re.search("\\b(always|never|don'?t|do not|prefer|instead|use |route to|when i ask)\\b", lower):
        return 'behavior'
    if re.search('\\b(wrong (?:about|date|name|path|file)|not |is actually|should be)\\b', lower):
        return 'fact'
    return 'fact'


def parse_correction(message = None):
    '''Parse user correction into structured intent.'''
    parse_memory_correct = parse_memory_correct
    import jarvis.trust_memory
    if not message:
        message
    raw = ''.strip()
    if not raw:
        return None
    parsed = parse_memory_correct(raw)
    if parsed:
        (hint, new_fact) = parsed
        return CorrectionIntent(correction = new_fact, wrong_hint = hint, kind = infer_correction_kind(new_fact), raw = raw)
    m = None.match(raw)
    if m:
        return CorrectionIntent(correction = m.group(2).strip().rstrip('.'), wrong_hint = m.group(1).strip(), kind = infer_correction_kind(m.group(2)), raw = raw)
    m = None.match(raw)
    if m:
        return CorrectionIntent(correction = m.group(2).strip().rstrip('.'), wrong_hint = m.group(1).strip(), kind = 'fact', raw = raw)
    if None.search(raw):
        m = _ACTUALLY.match(raw)
        if m:
            body = m.group(1).strip().rstrip('.')
            if len(body) >= 4:
                return CorrectionIntent(correction = body, kind = infer_correction_kind(body), raw = raw)
            m = None.search("(?:that'?s wrong|you'?re wrong|you are wrong|that is wrong|that is incorrect|you got (?:it|that) wrong)[:\\s—-]*(.+)$", raw, re.I | re.S)
            if m:
                body = m.group(1).strip().rstrip('.')
                if len(body) >= 4:
                    return CorrectionIntent(correction = body, kind = infer_correction_kind(body), raw = raw)
                if None(raw) >= 12:
                    return CorrectionIntent(correction = raw, kind = infer_correction_kind(raw), raw = raw)


def _summarize_wrong_claim(assistant_msg = None, correction = None):
    if not assistant_msg:
        assistant_msg
    assistant = ''.strip()
    if not assistant:
        return ''
    if len(assistant) <= 280:
        return assistant
    excerpt = None[:1200]
    prompt = f'''The user is correcting the assistant. From the assistant reply below, write ONE short sentence stating what the assistant got wrong. If unclear, summarize the disputed claim.\n\nUser correction: {correction[:400]}\n\nAssistant reply:\n{excerpt}'''
    
    try:
        summary = llm.ask(llm.general_model(), [
            {
                'role': 'user',
                'content': prompt }]).strip()
        if summary:
            return summary[:400]
        return None[:280]
    except Exception:
        return 



def _format_correction(wrong_claim = None, correction = None):
    if not wrong_claim:
        wrong_claim
    wrong = ''.strip()
    if not correction:
        correction
    right = ''.strip()
    if wrong and right:
        return f'''[Correction] Wrong: {wrong} → Right: {right}'''
    if None.lower().startswith('[correction]'):
        return right
    return f'''{right}'''


def apply_correction(memory = None, intent = None, *, assistant_msg, module):
    '''Store a user correction and update memory/strategy layers.'''
    correction = intent.correction.strip()
    if not correction:
        return CorrectionResult(False, '', message = 'Empty correction.')
    kind = intent.kind if None.kind in ('fact', 'behavior') else infer_correction_kind(correction)
    if not intent.wrong_hint:
        intent.wrong_hint
    wrong_claim = ''.strip()
    if wrong_claim and assistant_msg:
        wrong_claim = _summarize_wrong_claim(assistant_msg, correction)
    removed = 0
    strategy_created = False
    mirrors = []
    correct_memory = correct_memory
    record_strategy = record_strategy
    import jarvis.trust_memory
    if kind == 'fact' or intent.wrong_hint:
        (removed, _fact_entry, strategy_created) = correct_memory(memory, correction, search_hint = intent.wrong_hint)
        if removed:
            mirrors.append(f'''replaced {removed} fact(s)''')
        elif _fact_entry:
            mirrors.append('updated fact')
        elif kind == 'behavior':
            rule = correction if correction.lower().startswith('when ') else f'''When answering: {correction.rstrip('.')}'''
            
            try:
                record_strategy(memory, rule, namespace = CORRECTION_NAMESPACE, source = 'correction-learn')
                mirrors.append('behavior strategy')
                strategy_created = True
                lesson = _format_correction(wrong_claim, correction)
                entry = memory.add('teaching', lesson, tags = [
                    CORRECTION_TAG,
                    f'''correction-{kind}''',
                    'user-corrected'], namespace = CORRECTION_NAMESPACE)
                mirrors.append('correction teaching')
                if strategy_created and 'behavior strategy' not in mirrors:
                    mirrors.append('behavior strategy')
                sid = _register_correction(correction = correction, wrong_claim = wrong_claim, kind = kind, module = module)
                return CorrectionResult(True, correction, wrong_claim = wrong_claim, kind = kind, entry = entry, mirrors = mirrors, removed = removed, message = f'''Remembered your correction ({kind}).''', source_id = sid)
            except ValueError:
                exc = None
                log.debug('Strategy from correction skipped: %s', exc)
                exc = None
                del exc
                continue
                exc = None
                del exc



def list_corrections(memory = None, *, query, limit):
    entries = memory.list_entries(entry_type = 'teaching', namespace = CORRECTION_NAMESPACE)
# WARNING: Decompyle incomplete


def correction_context_for_chat(memory = None, message = None, *, limit):
    pass
# WARNING: Decompyle incomplete


def corrections_system_block(memory = None, *, max_items):
    filter_trusted_content = filter_trusted_content
    import jarvis.trust_memory
    entries = list_corrections(memory, limit = max_items)
    lines = []
    for e in entries:
        line = filter_trusted_content(e.get('content', ''))
        if not line:
            continue
        lines.append(f'''- {line}''')
    if not lines:
        return ''
    return 'User corrections (highest priority — avoid repeating these errors):\n' + '\n'.join(lines)


def format_corrections_markdown(entries = None):
    if not entries:
        return '_No corrections stored yet._'
    return (lambda .0: pass# WARNING: Decompyle incomplete
)(entries())


def should_auto_learn_correction(user_msg = None, mode = None):
    if mode == 'off':
        return False
    if mode == 'explicit':
        return bool(re.search('\\b(remember (?:this )?correction|correct(?:ion)? learn)\\b', user_msg, re.I))
    return None(user_msg)

