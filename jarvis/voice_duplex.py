# Source Generated with Decompyle++
# File: voice_duplex.cpython-312.pyc (Python 3.12)

'''Duplex voice helpers — barge-in and playback/listen coordination (#27).'''
from __future__ import annotations
from jarvis.voice_settings import duplex_mode, load_voice_settings
_DUPLEX_HELP = {
    'off': 'Wake word ignored during TTS; no barge-in.',
    'half': 'Wake or PTT stops playback, then listens (no mid-sentence interrupt).',
    'full': 'Speak during TTS to barge-in; assistant turn truncated in memory.' }

def duplex_status():
    mode = duplex_mode()
    return {
        'mode': mode,
        'label': {
            'off': 'Duplex off',
            'half': 'Half duplex',
            'full': 'Full duplex' }.get(mode, mode),
        'help': _DUPLEX_HELP.get(mode, ''),
        'barge_in': mode == 'full',
        'stop_before_listen': mode != 'full',
        'wake_during_playback': mode != 'off',
        'interrupt_on_speak': bool(load_voice_settings().get('interrupt_on_speak', True)) }


def ignore_wake_during_playback():
    return duplex_mode() == 'off'


def before_listen():
    '''Stop assistant playback before capture unless full-duplex barge-in is active.'''
    if duplex_mode() == 'full':
        return None
    stop_playback = stop_playback
    import jarvis.audio_device
    stop_playback()


def on_wake_during_playback():
    '''Whether a wake word hit during TTS should start capture.'''
    mode = duplex_mode()
    if mode == 'off':
        return False
    stop_playback = stop_playback
    import jarvis.audio_device
    stop_playback()
    if mode == 'half':
        
        try:
            emit_voice_state = emit_voice_state
            import jarvis.events
            emit_voice_state('listening', detail = 'half-duplex-wake')
            return True
            return True
        except Exception:
            return True



def maybe_barge_in(peak_db = None, speech_threshold_db = None):
    '''Interrupt TTS when the user speaks during full-duplex playback.'''
    if not load_voice_settings().get('interrupt_on_speak', True):
        return False
    if duplex_mode() != 'full':
        return False
    playback_active = playback_active
    stop_playback = stop_playback
    import jarvis.audio_device
    if not playback_active():
        return False
    if peak_db < speech_threshold_db:
        return False
    stop_playback()
    
    try:
        get_assistant = get_assistant
        import jarvis.assistant_instance
        assistant = get_assistant()
        if assistant and assistant.conversation.truncate_last_assistant():
            assistant.branches.persist(session = assistant.session)
        
        try:
            emit_voice_state = emit_voice_state
            import jarvis.events
            emit_voice_state('listening', detail = 'barge-in')
            return True
            except Exception:
                continue
        except Exception:
            return True



