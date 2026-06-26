# Source Generated with Decompyle++
# File: first_run_downloads.cpython-312.pyc (Python 3.12)

'''Auto-download optional voice assets on first run (#33).'''
from __future__ import annotations
import logging
import shutil
import subprocess
import urllib.request as urllib
from pathlib import Path
from jarvis.config import DATA_DIR, PROJECT_ROOT, piper_model_path, piper_ready
log = logging.getLogger('jarvis.first_run_dl')
PIPER_VOICE_BASE = 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium'
PIPER_RELEASE = 'https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz'

def _download(url = None, dest = None):
    
    try:
        dest.parent.mkdir(parents = True, exist_ok = True)
        urllib.request.urlretrieve(url, dest)
        if dest.is_file():
            dest.is_file()
        return dest.stat().st_size > 0
    except Exception:
        exc = None
        log.warning('download %s failed: %s', url, exc)
        exc = None
        del exc
        return False
        exc = None
        del exc



def ensure_piper_voice():
    '''Download Piper ONNX voice if missing.'''
    if not piper_model_path():
        piper_model_path()
    model = DATA_DIR / 'models' / 'piper' / 'en_US-lessac-medium.onnx'
    json_path = model.with_suffix('.onnx.json')
    if model.is_file() and json_path.is_file():
        return (True, f'''voice ready: {model.name}''')
    ok1 = None(f'''{PIPER_VOICE_BASE}/en_US-lessac-medium.onnx''', model)
    ok2 = _download(f'''{PIPER_VOICE_BASE}/en_US-lessac-medium.onnx.json''', json_path)
    if ok1 and ok2:
        return (True, f'''downloaded Piper voice to {model.parent}''')


def ensure_piper_binary():
    '''Download bundled Piper binary when tools/piper is empty.'''
    if shutil.which('piper'):
        return (True, 'piper on PATH')
    bundled = PROJECT_ROOT / 'tools' / 'piper' / 'piper'
    if bundled.is_file():
        return (True, 'bundled piper')
    if not shutil.which('curl') or shutil.which('tar'):
        return (False, 'curl/tar required for Piper binary install')
    dest_dir = PROJECT_ROOT / 'tools' / 'piper'
    dest_dir.mkdir(parents = True, exist_ok = True)
    archive = DATA_DIR / 'cache' / 'piper_linux_x86_64.tar.gz'
    archive.parent.mkdir(parents = True, exist_ok = True)
    if not archive.is_file() and _download(PIPER_RELEASE, archive):
        return (False, 'Piper binary download failed')
    
    try:
        subprocess.run([
            'tar',
            '-xzf',
            str(archive),
            '-C',
            str(dest_dir.parent)], check = True, timeout = 120, capture_output = True)
        inner = dest_dir.parent / 'piper'
        if inner.is_dir() and inner != dest_dir:
            for item in inner.iterdir():
                target = dest_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, target, dirs_exist_ok = True)
                    continue
                shutil.copy2(item, target)
            shutil.rmtree(inner, ignore_errors = True)
        if bundled.is_file():
            bundled.chmod(493)
            return (True, 'installed bundled piper')
        return (False, 'Piper binary extract failed')
    except Exception:
        exc = None
        log.warning('piper extract failed: %s', exc)
        exc = None
        del exc
        return (False, 'Piper binary extract failed')
        exc = None
        del exc



def warm_whisper_weights():
    '''Trigger faster-whisper model download if backend is available.'''
    
    try:
        whisper_backend = whisper_backend
        import jarvis.audio_whisper
        if whisper_backend() == 'none':
            return (False, 'Whisper backend not installed')
        if not __import__('os').getenv('JARVIS_WHISPER_MODEL', 'small').strip():
            __import__('os').getenv('JARVIS_WHISPER_MODEL', 'small').strip()
        model_name = 'small'
        
        try:
            WhisperModel = WhisperModel
            import faster_whisper
            WhisperModel(model_name, device = 'cpu', compute_type = 'int8')
            return (True, f'''faster-whisper weights cached ({model_name})''')
            except Exception:
                return (False, 'Whisper check skipped')
        except ImportError:
            return (False, 'pip install faster-whisper')
            except Exception:
                exc = None
                log.warning('whisper warm failed: %s', exc)
                del exc
                return None
                None = 
                del exc




def ensure_voice_assets():
    '''Run all first-run voice asset steps.'''
    notes = []
    pulled = []
    (ok_v, msg_v) = ensure_piper_voice()
    notes.append(msg_v)
    if ok_v:
        pulled.append('piper_voice')
    if not piper_ready():
        (ok_b, msg_b) = ensure_piper_binary()
        notes.append(msg_b)
        if ok_b:
            pulled.append('piper_binary')
    (ok_w, msg_w) = warm_whisper_weights()
    notes.append(msg_w)
    if ok_w:
        pulled.append('whisper')
    return {
        'ok': True,
        'pulled': pulled,
        'voice': notes }

