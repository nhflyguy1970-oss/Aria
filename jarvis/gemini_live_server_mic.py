# Source Generated with Decompyle++
# File: gemini_live_server_mic.cpython-312.pyc (Python 3.12)

'''Server-side mic capture + speaker playback for Gemini Live (PySide-safe).'''
from __future__ import annotations
import asyncio
import base64
import logging
import os
import shlex
import shutil
import subprocess
import threading
import time
log = logging.getLogger('jarvis.gemini_live.mic')
_CHUNK_BYTES = 3200

def server_audio_enabled():
    if os.getenv('JARVIS_GEMINI_LIVE_SERVER_MIC', '1').strip().lower() in ('0', 'false', 'no', 'off'):
        return False
    return bool(shutil.which('pw-record'))


def server_playback_enabled():
    if os.getenv('JARVIS_GEMINI_LIVE_SERVER_SPEAK', '1').strip().lower() in ('0', 'false', 'no', 'off'):
        return False
    return bool(shutil.which('pw-play'))


def _playback_tail_sec():
    
    try:
        return max(0, min(1.5, float(os.getenv('JARVIS_GEMINI_LIVE_MIC_TAIL_SEC', '0.35'))))
    except ValueError:
        return 0.35



def _capture_cmd():
    _is_creative_input = _is_creative_input
    effective_input_source = effective_input_source
    prepare_input_source = prepare_input_source
    import jarvis.audio_device
    if not effective_input_source():
        effective_input_source()
    source = ''.strip()
    if not source:
        raise RuntimeError('No capture source configured')
    if shutil.which('pactl'):
        prepare_input_source(source)
    stereo = _is_creative_input(source)
    rate = 48000 if stereo else 16000
    channels = 2 if stereo else 1
    pw = [
        'pw-record',
        '--target',
        source,
        '--rate',
        str(rate),
        '--channels',
        str(channels),
        '--format',
        's16',
        '-']
    if stereo and shutil.which('ffmpeg'):
        ff = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel',
            'error',
            '-f',
            's16le',
            '-ar',
            str(rate),
            '-ac',
            str(channels),
            '-i',
            'pipe:0',
            '-ar',
            '16000',
            '-ac',
            '1',
            '-f',
            's16le',
            'pipe:1']
        return (pw, ff)
    if None != 16000 or channels != 1:
        if not shutil.which('ffmpeg'):
            raise RuntimeError('ffmpeg required to resample capture for Gemini Live')
        ff = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel',
            'error',
            '-f',
            's16le',
            '-ar',
            str(rate),
            '-ac',
            str(channels),
            '-i',
            'pipe:0',
            '-ar',
            '16000',
            '-ac',
            '1',
            '-f',
            's16le',
            'pipe:1']
        return (pw, ff)
    return (None, None)


class GeminiLiveServerAudio:
    '''PipeWire capture → Gemini upstream; Gemini audio → PipeWire playback.

    Half-duplex: mic frames are dropped while the assistant is speaking so
    pw-record does not feed Gemini its own pw-play output (echo loop).
    '''
    
    def __init__(self = None):
        self._capture_pw = None
        self._capture_ff = None
        self._play_proc = None
        self._play_rate = 24000
        self._stopped = False
        self._lock = threading.Lock()
        self._speaking_until = 0
        self._tail_sec = _playback_tail_sec()
        self._dropped_while_speaking = 0

    
    def _mic_open(self = None):
        self._lock
        None(None, None)
        return 
        with None:
            if not None, time.monotonic() >= self._speaking_until:
                pass

    
    def _extend_speaking(self = None, pcm_bytes = None, rate = None):
        if pcm_bytes <= 0 or rate <= 0:
            return None
        duration = pcm_bytes / (rate * 2)
        self._lock
        now = time.monotonic()
        self._speaking_until = max(self._speaking_until, now + duration + self._tail_sec)
        None(None, None)
        return None
        with None:
            if not None:
                pass

    
    async def start_capture(self = None, send_audio_b64 = None):
        pass
    # WARNING: Decompyle incomplete

    
    def _ensure_player(self = None, rate = None):
        pass
    # WARNING: Decompyle incomplete

    
    def play_pcm_b64(self = None, data_b64 = None, *, rate):
        if not server_playback_enabled():
            return None
        
        try:
            pcm = base64.b64decode(data_b64)
            if not pcm:
                return None
                
                try:
                    self._extend_speaking(len(pcm), rate)
                    self._ensure_player(rate)
                    if self._play_proc:
                        if self._play_proc.stdin:
                            self._play_proc.stdin.write(pcm)
                            self._play_proc.stdin.flush()
                            return None
                        return None
                    return None
                except Exception:
                    exc = None
                    log.debug('Gemini Live server playback: %s', exc)
                    exc = None
                    del exc
                    return None
                    exc = None
                    del exc



    
    def stop_playback(self = None):
        '''Stop speaker output and keep mic muted briefly (interrupt / barge-in).'''
        self._lock
        self._speaking_until = time.monotonic() + self._tail_sec
        None(None, None)
        self._stop_player()
        return None
        with None:
            if not None:
                pass
        continue

    
    def _stop_player(self = None):
        proc = self._play_proc
        self._play_proc = None
        if not proc:
            return None
        
        try:
            if proc.stdin:
                proc.stdin.close()
            proc.wait(timeout = 1)
            return None
        except Exception:
            proc.kill()
            return None
            except Exception:
                return None


    
    async def stop(self = None):
        pass
    # WARNING: Decompyle incomplete


