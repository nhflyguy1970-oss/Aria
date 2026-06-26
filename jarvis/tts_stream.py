# Source Generated with Decompyle++
# File: tts_stream.cpython-312.pyc (Python 3.12)

'''Low-latency TTS chunking helpers (#26).'''
from __future__ import annotations
import re
import time
from typing import Any
from jarvis.voice_settings import load_voice_settings

def chunk_max_chars():
    if not load_voice_settings().get('tts_chunk_max_chars'):
        load_voice_settings().get('tts_chunk_max_chars')
    return max(40, min(400, int(220)))


def min_chunk_chars():
    if not load_voice_settings().get('tts_min_chunk_chars'):
        load_voice_settings().get('tts_min_chunk_chars')
    return max(8, min(80, int(24)))

_SOURCE_PREFIX_RE = re.compile("^(?:according to (?:the )?sources?(?: i(?:'ve| have) found)?|based on (?:my )?search|from (?:my )?search|sources?:|references?:|this (?:information|estimation) comes from|i(?:'ve| have) found|from historical records)[,:]?\\s*", re.I)
_URL_RE = re.compile('https?://\\S+|www\\.\\S+', re.I)
_CITATION_RE = re.compile('\\[\\d+\\]|\\(\\s*source\\s*:\\s*[^)]+\\)', re.I)

def sanitize_for_speech(text = None):
    '''Strip markdown, citations, and source narration for natural TTS.'''
    if not text:
        return ''
    out = str(text).strip()
    out = re.sub('\\*\\*Sources\\*\\*[\\s\\S]*', '', out, flags = re.I)
    out = re.sub('```[\\s\\S]*?```', ' ', out)
    out = re.sub('`([^`]+)`', '\\1', out)
    out = re.sub('!\\[[^\\]]*\\]\\([^)]+\\)', ' ', out)
    out = re.sub('\\[([^\\]]+)\\]\\([^)]+\\)', '\\1', out)
    out = re.sub('^#{1,6}\\s+', '', out, flags = re.M)
    out = re.sub('\\*\\*([^*]+)\\*\\*', '\\1', out)
    out = re.sub('\\*([^*]+)\\*', '\\1', out)
    out = _URL_RE.sub(' ', out)
    out = _CITATION_RE.sub(' ', out)
    lines = []
    for line in out.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match('^(?:source|reference|via)\\s*:', stripped, re.I):
            continue
        if re.match('^\\d+\\.\\s', stripped):
            continue
        if re.match('^[-*•]\\s*(?:https?://|www\\.)', stripped, re.I):
            continue
        stripped = _SOURCE_PREFIX_RE.sub('', stripped).strip()
        if stripped or re.match('^[-*•]\\s*$', stripped):
            continue
        lines.append(stripped)
    out = ' '.join(lines)
    out = re.sub("\\baccording to (?:the )?sources?(?: i(?:'ve| have) found)?[,.]?\\s*", '', out, flags = re.I)
    out = re.sub('\\bbased on (?:my )?search[,.]?\\s*', '', out, flags = re.I)
    out = re.sub('\\s+', ' ', out).strip()
    return out


def plain_speak_text(text = None):
    '''Alias for client-side plainSpeakText — single source for TTS cleanup tests.'''
    return sanitize_for_speech(text)


def split_speak_chunks(text = None, *, max_chars):
    '''Split plain text into speakable chunks (sentences, then max length).'''
    if not max_chars:
        max_chars
    limit = chunk_max_chars()
    if not text:
        text
    plain = re.sub('\\s+', ' ', ''.strip())
    if not plain:
        return []
    parts = None
    buf = ''
    for sentence in re.split('(?<=[.!?])\\s+', plain):
        sentence = sentence.strip()
        if not sentence:
            continue
        if len(sentence) <= limit:
            if buf and len(buf) + 1 + len(sentence) > limit:
                parts.append(buf)
                buf = sentence
            elif buf:
                pass
            
            buf = sentence
            continue
        if buf:
            parts.append(buf)
            buf = ''
        for i in range(0, len(sentence), limit):
            parts.append(sentence[i:i + limit].strip())
    if buf:
        parts.append(buf)
# WARNING: Decompyle incomplete


def speak_chunk_metrics(text = None, *, generate_ms):
    if not text:
        text
    return {
        'chars': len(''),
        'generate_ms': generate_ms,
        'chunk_max_chars': chunk_max_chars() }

