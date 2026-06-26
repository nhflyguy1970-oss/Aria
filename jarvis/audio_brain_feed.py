# Source Generated with Decompyle++
# File: audio_brain_feed.cpython-312.pyc (Python 3.12)

'''Debounced auto-feed from audio transcripts into brain memory.'''
from __future__ import annotations
import logging
import threading
import time
from pathlib import Path
log = logging.getLogger('jarvis.audio_brain_feed')
_LOCK = threading.Lock()
_LAST_FEED: 'dict[str, float]' = { }
_DEBOUNCE_SEC = float(__import__('os').getenv('JARVIS_AUDIO_FEED_DEBOUNCE', '60'))

def _enabled():
    auto_audio_learn_enabled = auto_audio_learn_enabled
    import jarvis.brain_memory
    return auto_audio_learn_enabled()


def maybe_feed_transcript(memory = None, transcript = None, audio_path = None):
    '''Schedule debounced transcript → brain learning (non-blocking).'''
    if not transcript:
        transcript
    text = ''.strip()
# WARNING: Decompyle incomplete


def _feed_worker(memory = None, transcript = None, audio_path = None):
    
    try:
        extract_and_store = extract_and_store
        import jarvis.journal_learning
        label = Path(audio_path).name if audio_path else 'recording'
        extract_and_store(memory, f'''Audio transcript ({label}):\n{transcript[:2500]}''', project = 'main')
        return None
    except Exception:
        exc = None
        log.debug('Audio brain feed skipped: %s', exc)
        exc = None
        del exc
        return None
        exc = None
        del exc


