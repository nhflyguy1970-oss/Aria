# Source Generated with Decompyle++
# File: voice_only.cpython-312.pyc (Python 3.12)

'''Voice-only demo — minimal assistant without the web GUI (P1 #34).'''
from __future__ import annotations
import logging
import os
import re
import signal
import sys
import threading
from typing import Any
log = logging.getLogger('jarvis.voice_only')
_stop = threading.Event()
_console_state = 'idle'
_last_confirm_id: 'str | None' = None

def prepare_voice_only_env():
    '''Sensible defaults for headless voice demo.'''
    os.environ.setdefault('JARVIS_VOICE_ONLY', '1')
    os.environ.setdefault('JARVIS_WAKEWORD_TO_CHAT', '1')
    os.environ.setdefault('JARVIS_WAKEWORD_SPEAK', '0')
    os.environ.setdefault('JARVIS_WAKEWORD_RECORD', '1')
    os.environ.setdefault('JARVIS_AUTO_PLAY', '1')
    os.environ.setdefault('JARVIS_NO_BROWSER', '1')


def strip_for_speech(text = None):
    '''Remove markdown/code/citations so TTS sounds natural.'''
    sanitize_for_speech = sanitize_for_speech
    import jarvis.tts_stream
    return sanitize_for_speech(text)


def speak_max_chars():
    raw = os.getenv('JARVIS_VOICE_SPEAK_MAX_CHARS', '1200').strip()
    
    try:
        return max(80, min(int(raw), 4000))
    except ValueError:
        return 1200



def speak_text(text = None, *, assistant):
    '''Generate Piper audio and play through the default sink.'''
    emit_voice_state = emit_voice_state
    import jarvis.events
    cleaned = strip_for_speech(text)
    if not cleaned:
        return ''
    limit = speak_max_chars()
    if len(cleaned) > limit:
        cleaned = cleaned[:limit - 3].rstrip() + '…'
    emit_voice_state('speaking', detail = 'voice-only')
# WARNING: Decompyle incomplete


def voice_chat_processor(message = None, voice = None, *, assistant):
    '''Process one utterance and speak the reply (no GUI).'''
    global _last_confirm_id, _last_confirm_id
    get_assistant = get_assistant
    import jarvis.assistant_instance
    if not assistant:
        assistant
    assistant = get_assistant()
    result = assistant.process(message, voice = True)
    if not result.get('message'):
        result.get('message')
    reply = ''.strip()
    if result.get('type') == 'confirm_required':
        if not result.get('confirm_id'):
            result.get('confirm_id')
        if not ''.strip():
            ''.strip()
        _last_confirm_id = None
        speak_text('That action needs confirmation. Say yes to confirm, or no to cancel.', assistant = assistant)
        return result
    _last_confirm_id = None
    if reply and result.get('ok', True):
        speak_text(reply, assistant = assistant)
        return result
    if None.get('ok', True) and reply:
        speak_text(reply, assistant = assistant)
    return result


def _console_voice_state(event = None, **payload):
    global _console_state
    if not payload.get('state'):
        payload.get('state')
    state = 'idle'.strip().lower()
    if not payload.get('detail'):
        payload.get('detail')
    detail = ''.strip()
    if not state == _console_state and detail:
        return None
    _console_state = state
    labels = {
        'idle': '○ idle',
        'listening': '● listening',
        'thinking': '◐ thinking',
        'speaking': '♪ speaking' }
    line = labels.get(state, state)
    if detail:
        line = f'''{line} ({detail})'''
    print(line, flush = True)


def _voice_on_detect(model = None, score = None):
    _start_record_after_detect = _start_record_after_detect
    wakeword_phrase = wakeword_phrase
    import jarvis.audio_wakeword
    print(f'''\n● {wakeword_phrase(model)} ({score:.0%})''', flush = True)
    _start_record_after_detect(model, score)


def _execute_confirm(confirm_id = None, approved = None, *, assistant):
    log_event = log_event
    import jarvis.action_log
    call_action = call_action
    has_action = has_action
    import jarvis.handlers.registry
    pop_pending = pop_pending
    import jarvis.tool_permissions
    row = pop_pending(confirm_id)
    if not row:
        return {
            'ok': False,
            'message': 'Confirm expired.' }
    if not row.get('message'):
        row.get('message')
    log_event('tool_confirm', tool = row.get('tool'), action = row.get('action'), approved = approved, message = ''[:200])
    if not approved:
        return {
            'ok': True,
            'message': 'Cancelled.' }
    if not None.get('action'):
        None.get('action')
    action = ''
    if not row.get('params'):
        row.get('params')
    params = dict({ })
    params['_confirmed'] = True
    if not row.get('message'):
        row.get('message')
    message = ''
    if has_action(action):
        return call_action(assistant, action, params, message)
    if None == 'ha_control':
        return assistant._ha_control(params, message)
    if None == 'ha_scene':
        return assistant._ha_scene(params, message)
    return {
        'ok': None,
        'message': f'''Unknown confirmed action: {action}''' }


def _handle_confirm_followup(text = None, assistant = None):
    '''If the last turn needs confirmation, accept yes/no by voice.'''
    global _last_confirm_id, _last_confirm_id
    if not _last_confirm_id:
        return False
    lower = text.strip().lower()
    if lower in ('yes', 'yeah', 'yep', 'confirm', 'do it', 'go ahead', 'approve'):
        result = _execute_confirm(_last_confirm_id, True, assistant = assistant)
        _last_confirm_id = None
        if not result.get('message'):
            result.get('message')
        reply = ''.strip()
        if reply:
            speak_text(reply, assistant = assistant)
        return True
    if lower in ('no', 'nope', 'cancel', 'stop', 'deny'):
        _execute_confirm(_last_confirm_id, False, assistant = assistant)
        _last_confirm_id = None
        speak_text('Cancelled.', assistant = assistant)
        return True
    return False


def process_utterance(text = None, *, assistant):
    get_assistant = get_assistant
    import jarvis.assistant_instance
    if not assistant:
        assistant
    assistant = get_assistant()
    if not text:
        text
    cleaned = ''.strip()
    if not cleaned:
        return {
            'ok': False,
            'message': 'Empty transcript' }
    if None(cleaned, assistant):
        return {
            'ok': True,
            'message': 'confirmation handled' }
    return None(cleaned, voice = True, assistant = assistant)


def run_ptt_loop(*, assistant):
    record_until_silence = record_until_silence
    import jarvis.audio_live
    emit_voice_state = emit_voice_state
    on = on
    import jarvis.events
    transcribe = transcribe
    import jarvis.stt
# WARNING: Decompyle incomplete


def run_wakeword_loop(*, assistant):
    audio_wakeword = audio_wakeword
    import jarvis
    on = on
    import jarvis.events
# WARNING: Decompyle incomplete


def run_once(text = None, *, assistant):
    '''Single command for scripting / smoke tests.'''
    pass
# WARNING: Decompyle incomplete


def assistant_name():
    _name = assistant_name
    import jarvis.branding
    return _name()


def _install_signal_handlers():
    
    def _shutdown(signum, _frame):
        _stop.set()
        
        try:
            audio_wakeword = audio_wakeword
            import jarvis
            audio_wakeword.stop_listener()
            print('\nVoice demo stopped.', flush = True)
            return None
        except Exception:
            continue


    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)


def run_voice_only(argv = None):
    '''Entry for `python main.py voice`. Returns process exit code.'''
    load_jarvis_env = load_jarvis_env
    import jarvis.env_loader
    if not argv:
        argv
    argv = list(sys.argv[2:])
    load_jarvis_env()
    prepare_voice_only_env()
    once_text = ''
    force_ptt = False
    i = 0
    if i < len(argv):
        arg = argv[i]
        if arg in ('--ptt', '-p'):
            force_ptt = True
        elif arg in ('--once', '-1') and i + 1 < len(argv):
            once_text = argv[i + 1]
            i += 1
        elif arg in ('-h', '--help'):
            _print_help()
            return 0
        i += 1
        if i < len(argv):
            continue
    _install_signal_handlers()
    JarvisAssistant = JarvisAssistant
    import jarvis.assistant
    set_assistant = set_assistant
    import jarvis.assistant_instance
    is_uncensored = is_uncensored
    import jarvis.config
    ensure_services = ensure_services
    import jarvis.services
    name = assistant_name()
    print(f'''\n{name} voice-only demo (no web GUI)\n''', flush = True)
    ensure_services(pull_models = os.getenv('JARVIS_AUTO_PULL_MODELS', '1') != '0')
    assistant = JarvisAssistant(uncensored = is_uncensored())
    set_assistant(assistant)
    if os.getenv('JARVIS_FIRST_RUN_MODELS', '1') != '0':
        
        try:
            ensure_optional_models = ensure_optional_models
            import jarvis.first_run_models
            ensure_optional_models()
            if once_text:
                run_once(once_text, assistant = assistant)
                return 0
            use_wakeword = not force_ptt
            if use_wakeword:
                wakeword_available = wakeword_available
                import jarvis.audio_wakeword
                if not wakeword_available():
                    print('Wake word unavailable — falling back to push-to-talk.', flush = True)
                    use_wakeword = False
            
            try:
                if use_wakeword:
                    run_wakeword_loop(assistant = assistant)
                    return 0
                    
                    try:
                        run_ptt_loop(assistant = assistant)
                        return 0
                        except Exception:
                            exc = None
                            log.debug('first-run model check skipped: %s', exc)
                            exc = None
                            del exc
                            continue
                            exc = None
                            del exc
                    except RuntimeError:
                        exc = None
                        print(f'''ERROR: {exc}''', flush = True)
                        exc = None
                        del exc
                        return 1
                        exc = None
                        del exc





def _print_help():
    name = assistant_name()
    print(f'''\n{name} voice-only demo (P1 #34) — minimal assistant without the web GUI.\n\nUsage:\n  python main.py voice              Wake word loop (fallback: push-to-talk)\n  python main.py voice --ptt        Push-to-talk only (Enter to record)\n  python main.py voice --once "…"   Single command, speak reply, exit\n\nEnvironment:\n  JARVIS_WAKEWORD_SPEAK=0           voice-only speaks via Piper (avoid double TTS)\n  JARVIS_VOICE_SPEAK_MAX_CHARS=1200 Truncate long TTS\n  JARVIS_WAKEWORD_MODEL=hey_jarvis  Wake phrase model\n''')

