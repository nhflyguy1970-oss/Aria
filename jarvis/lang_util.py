# Source Generated with Decompyle++
# File: lang_util.cpython-312.pyc (Python 3.12)

'''Lightweight text language hints for chat (no extra dependencies).'''
from __future__ import annotations
import re
_CYRILLIC = re.compile('[\\u0400-\\u04FF]')
_CJK = re.compile('[\\u4e00-\\u9fff\\u3040-\\u30ff\\uac00-\\ud7af]')
_LATIN_EXTENDED = re.compile('[\\u00c0-\\u024f]')

def detect_text_language(text = None):
    '''
    Rough ISO 639-1 hint for chat context, or None when English/unknown.
    '''
    if not text:
        text
    t = ''.strip()
    if len(t) < 8:
        return None
# WARNING: Decompyle incomplete


def language_reply_hint(code = None):
    if code or code in ('en', 'und'):
        return ''
    names = {
        'zh': 'Chinese',
        'ru': 'Russian',
        'es': 'Spanish or another Latin-script language',
        'fr': 'French',
        'de': 'German' }
    label = names.get(code, f'''language code {code}''')
    return f'''User message appears to be in {label}. Reply in the same language unless they ask otherwise.'''

