# Source Generated with Decompyle++
# File: upgrade_deps.cpython-312.pyc (Python 3.12)

'''P0/P1 upgrade dependency and model inventory with live status.'''
from __future__ import annotations
import importlib.util as importlib
import os
import shutil
from typing import Any
PIP_PACKAGES: 'list[dict[str, Any]]' = [
    {
        'id': 'faster_whisper',
        'module': 'faster_whisper',
        'package': 'faster-whisper>=1.0.0',
        'feature': 'Whisper STT (default voice transcription)',
        'tier': 'P1',
        'required': False,
        'install': 'pip install -r requirements-optional.txt',
        'notes': 'Included in requirements-optional.txt; pulls PyTorch.' },
    {
        'id': 'openwakeword',
        'module': 'openwakeword',
        'package': 'openwakeword>=0.4.0',
        'feature': 'Wake word detection',
        'tier': 'P1',
        'required': False,
        'install': 'pip install openwakeword onnxruntime',
        'notes': 'Also needs onnxruntime. Wake models download on first use.' },
    {
        'id': 'onnxruntime',
        'module': 'onnxruntime',
        'package': 'onnxruntime',
        'feature': 'Wake word (openWakeWord runtime)',
        'tier': 'P1',
        'required': False,
        'install': 'pip install onnxruntime' },
    {
        'id': 'transformers',
        'module': 'transformers',
        'package': 'transformers>=4.57.0',
        'feature': 'FunctionGemma HF intent router (P1 #23)',
        'tier': 'P1',
        'required': False,
        'install': 'pip install transformers torch',
        'notes': 'Accept license at huggingface.co/google/functiongemma-270m-it' },
    {
        'id': 'websockets',
        'module': 'websockets',
        'package': 'websockets>=12.0',
        'feature': 'Gemini Live cloud voice WebSocket bridge',
        'tier': 'P4',
        'required': False,
        'env_flag': 'JARVIS_CLOUD_LIVE_VOICE',
        'install': "pip install 'websockets>=12.0'",
        'notes': 'Server proxy to Google BidiGenerateContent; key stays on server. Run ./scripts/enable-cloud-gemini.sh' },
    {
        'id': 'realtimestt',
        'module': 'RealtimeSTT',
        'package': 'realtimestt[faster-whisper]',
        'feature': 'RealTimeSTT low-latency voice pipeline',
        'tier': 'P1',
        'required': False,
        'env_flag': 'JARVIS_REALTIMESTT',
        'install': "pip install 'realtimestt[faster-whisper]'",
        'notes': 'Optional; set JARVIS_REALTIMESTT=1 and pick RealTimeSTT in GUI.' },
    {
        'id': 'ddgs',
        'module': 'ddgs',
        'package': 'ddgs>=9.0.0',
        'feature': 'P0 curated news / web headlines',
        'tier': 'P0',
        'required': False,
        'install': 'pip install ddgs',
        'notes': 'Fallback: duckduckgo-search in requirements-optional.txt.' },
    {
        'id': 'weasyprint',
        'module': 'weasyprint',
        'package': 'weasyprint>=62.0',
        'feature': 'Journal PDF export',
        'tier': 'P0',
        'required': False,
        'install': 'pip install weasyprint' },
    {
        'id': 'python_kasa',
        'module': 'kasa',
        'package': 'python-kasa>=0.7.0',
        'feature': 'P2 TP-Link Kasa smart plugs/bulbs',
        'tier': 'P2',
        'required': False,
        'env_flag': 'JARVIS_KASA',
        'install': 'pip install python-kasa' },
    {
        'id': 'playwright',
        'module': 'playwright',
        'package': 'playwright>=1.40.0',
        'feature': 'P2 browser automation agent',
        'tier': 'P2',
        'required': False,
        'env_flag': 'JARVIS_BROWSER_AGENT',
        'install': 'pip install playwright && playwright install chromium',
        'notes': 'Falls back to system browser if missing.' },
    {
        'id': 'build123d',
        'module': 'build123d',
        'package': 'build123d>=0.8.0',
        'feature': 'P3 parametric CAD (local Python)',
        'tier': 'P3',
        'required': False,
        'env_flag': 'JARVIS_CAD',
        'install': 'pip install build123d',
        'notes': 'OpenSCAD (apt) is an alternative — see install-cad skill.' },
    {
        'id': 'pyside6',
        'module': 'PySide6',
        'package': 'PySide6>=6.6',
        'feature': 'P4 PySide6 desktop shell (#89)',
        'tier': 'P4',
        'required': False,
        'env_flag': 'JARVIS_PYSIDE_SHELL',
        'install': './scripts/install-pyside-shell.sh',
        'notes': 'PySide6-Addons for WebEngine; PySide6-Fluent-Widgets for dark Fluent UI.' },
    {
        'id': 'pyside6_fluent',
        'module': 'qfluentwidgets',
        'package': 'PySide6-Fluent-Widgets>=1.6',
        'feature': 'P4 Fluent dark widgets for PySide shell',
        'tier': 'P4',
        'required': False,
        'env_flag': 'JARVIS_FLUENT_WIDGETS',
        'install': 'pip install PySide6-Fluent-Widgets' }]
OLLAMA_MODELS: 'list[dict[str, Any]]' = [
    {
        'id': 'functiongemma',
        'model': 'google/functiongemma-270m-it',
        'env': 'JARVIS_FUNCTIONGEMMA_MODEL',
        'feature': 'P1 FunctionGemma intent router (HF, ~50ms)',
        'tier': 'P1',
        'required': False,
        'size_approx': '~270M params / ~550MB',
        'pull': 'python scripts/pull-functiongemma.py',
        'fallbacks': [],
        'notes': 'Preferred when JARVIS_ROUTER_BACKEND=auto|functiongemma' },
    {
        'id': 'router',
        'model': 'qwen3:1.7b',
        'env': 'JARVIS_ROUTER_MODEL',
        'feature': 'P1 Ollama JSON fallback router',
        'tier': 'P1',
        'required': True,
        'size_approx': '~1.2 GB',
        'pull': 'ollama pull qwen3:1.7b',
        'fallbacks': [
            'qwen2.5:3b',
            'qwen2.5:7b'] },
    {
        'id': 'fast_chat',
        'model': 'qwen3:1.7b',
        'env': 'JARVIS_FAST_MODEL',
        'feature': 'P1 fast / voice chat model',
        'tier': 'P1',
        'required': True,
        'size_approx': '~1.2 GB',
        'pull': 'ollama pull qwen3:1.7b',
        'fallbacks': [
            'qwen2.5:3b',
            'qwen2.5:7b'] },
    {
        'id': 'reasoning',
        'model': 'deepseek-r1:7b',
        'env': 'JARVIS_REASONING_MODEL',
        'feature': 'P1 deep thinking / reasoning chat',
        'tier': 'P1',
        'required': False,
        'size_approx': '~4.7 GB',
        'pull': 'ollama pull deepseek-r1:7b',
        'fallbacks': [
            'deepseek-r1:1.5b',
            'qwen2.5:14b',
            'qwen2.5:7b'] }]
OTHER_MODELS: 'list[dict[str, Any]]' = [
    {
        'id': 'whisper_small',
        'name': 'whisper small',
        'env': 'JARVIS_WHISPER_MODEL',
        'default': 'small',
        'feature': 'Wake-word & live STT accuracy',
        'tier': 'P1',
        'cache': '~/.cache/huggingface/hub or ~/.cache/whisper',
        'install': 'Used automatically on first transcribe; pre-cache: python -c "from faster_whisper import WhisperModel; WhisperModel(\'small\')"' },
    {
        'id': 'openwakeword_hey_jarvis',
        'name': 'hey_jarvis',
        'env': 'JARVIS_WAKEWORD_MODEL',
        'default': 'hey_jarvis',
        'feature': 'Wake word model',
        'tier': 'P1',
        'install': 'Downloaded by openwakeword on first wake-word start' },
    {
        'id': 'piper_voice',
        'name': 'en_US-lessac-medium',
        'env': 'JARVIS_PIPER_MODEL',
        'feature': 'TTS voice (preferred over espeak)',
        'tier': 'core',
        'install': './scripts/install-dependencies.sh or install-piper.sh' }]
SYSTEM_TOOLS: 'list[dict[str, Any]]' = [
    {
        'id': 'ffmpeg',
        'binary': 'ffmpeg',
        'feature': 'Audio capture, RealTimeSTT file feed, TTS',
        'tier': 'P1' },
    {
        'id': 'pw_record',
        'binary': 'pw-record',
        'feature': 'PipeWire live recording',
        'tier': 'P1' },
    {
        'id': 'espeak',
        'binary': 'espeak-ng',
        'feature': 'Fallback TTS',
        'tier': 'core' }]

def _module_installed(name = None):
    return importlib.util.find_spec(name) is not None


def _env_flag_enabled(name = None, *, default):
    if not name:
        return True
    if name == 'JARVIS_REALTIMESTT':
        default = '0'
    return os.getenv(name, default).strip().lower() not in ('0', 'false', 'no', 'off')


def _functiongemma_installed():
    '''FunctionGemma via HF merged weights / cache — same signal as the voice router.'''
    
    try:
        functiongemma_model_id = functiongemma_model_id
        functiongemma_ready = functiongemma_ready
        import jarvis.functiongemma_router
        if functiongemma_ready():
            model_id = functiongemma_model_id()
            return {
                'installed': True,
                'resolved': model_id,
                'backend': 'hf' }
        return {
            'installed': False,
            'resolved': None }
    except Exception:
        continue



def _ollama_model_status(model = None, fallbacks = None):
    check_ollama = check_ollama
    model_available = model_available
    import jarvis.ollama_health
    ollama = check_ollama()
    if not ollama.get('running'):
        return {
            'installed': False,
            'reason': 'ollama not running',
            'resolved': None }
    if model_available(model):
        return {
            'installed': True,
            'resolved': model }
    if not None:
        pass
    for fb in []:
        if not model_available(fb):
            continue
        
        return [], {
            'installed': True,
            'resolved': fb,
            'fallback': True }
    return {
        'installed': False,
        'resolved': None }


def _model_row_status(row = None):
    '''Installed status for an Ollama/HF model inventory row.'''
    if not os.getenv(row['env']):
        os.getenv(row['env'])
    model = row['model'].strip()
# WARNING: Decompyle incomplete


def dependency_report(*, include_optional):
    '''Full inventory with installed/missing status.'''
    pip_rows = []
    missing_pip = []
# WARNING: Decompyle incomplete


def dependency_summary():
    '''Compact counts for checklist / dashboard.'''
    report = dependency_report(include_optional = False)
# WARNING: Decompyle incomplete

