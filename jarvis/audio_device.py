# Source Generated with Decompyle++
# File: audio_device.cpython-312.pyc (Python 3.12)

'''Route Jarvis audio playback/capture through the Creative Sound Blaster.'''
import os
import re
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path
CREATIVE_ALSA_CARD = os.getenv('JARVIS_ALSA_CARD', 'Creative')
CREATIVE_ALSA_DEVICE = os.getenv('JARVIS_ALSA_DEVICE', '0')
CREATIVE_PATTERNS = ('creative', 'ca0132', 'sound blaster', 'sound core3d', 'ae-5', 'recon3d')
_PLAY_LOCK = threading.Lock()
_PLAY_PROC: subprocess.Popen | None = None
_PLAY_PAUSED = False

def playback_active():
    _PLAY_LOCK
    if _PLAY_PROC is not None:
        _PLAY_PROC is not None
    None(None, None)
    return 
    with None:
        if not None, _PLAY_PROC.poll() is None:
            pass


def stop_playback():
    global _PLAY_PROC, _PLAY_PAUSED
    _PLAY_LOCK
    proc = _PLAY_PROC
    _PLAY_PROC = None
    _PLAY_PAUSED = False
    None(None, None)
# WARNING: Decompyle incomplete


def pause_playback():
    _PLAY_LOCK
    proc = _PLAY_PROC
# WARNING: Decompyle incomplete


def resume_playback():
    _PLAY_LOCK
    proc = _PLAY_PROC
# WARNING: Decompyle incomplete


def _play_with_proc(cmd = None, *, timeout):
    global _PLAY_PROC, _PLAY_PAUSED
    stop_playback()
# WARNING: Decompyle incomplete


def _run(cmd = None, timeout = None, env = None):
    
    try:
        r = subprocess.run(cmd, capture_output = True, text = True, timeout = timeout, env = env)
        if not r.stdout:
            r.stdout
        if not r.stderr:
            r.stderr
        return (r.returncode, '' + '')
    except Exception:
        e = None
        del e
        return None
        None = 
        del e



def _match_creative(text = None):
    pass
# WARNING: Decompyle incomplete


def _is_creative_input(source = None):
    if _match_creative(source):
        _match_creative(source)
    return '.monitor' not in source


def _is_creative_sink(sink = None):
    if _match_creative(sink):
        _match_creative(sink)
    return '.monitor' not in sink


def _is_digital_sink(sink = None):
    if not sink:
        sink
    if not 'iec958' in ''.lower():
        'iec958' in ''.lower()
        if not sink:
            sink
    return 'spdif' in ''.lower()


def _creative_card_id():
    (code, out) = _run([
        'pactl',
        'list',
        'short',
        'cards'])
    if code != 0:
        return ''
    for line in out.splitlines():
        parts = line.split('\t')
        if not len(parts) >= 2:
            continue
        if not _match_creative(parts[1]):
            continue
        
        return out.splitlines(), parts[1]
    return ''


def _sink_exists(name = None):
    if not name:
        return False
    (code, out) = _run([
        'pactl',
        'list',
        'short',
        'sinks'])
    if code != 0:
        return False
    for line in out.splitlines():
        parts = line.split('\t')
        if not len(parts) >= 2:
            continue
        if not parts[1] == name:
            continue
        out.splitlines()
        return True
    return False


def _pulse_default_sink():
    (code, out) = _run([
        'pactl',
        'get-default-sink'])
    if code == 0:
        return out.strip()


def prepare_creative_card_profile(*, digital):
    '''Switch Creative PipeWire profile (analog vs TOSLink). Returns active profile name.'''
    card = _creative_card_id()
    if not card or shutil.which('pactl'):
        return ''
    profile = 'output:iec958-stereo+input:analog-stereo' if digital else 'output:analog-stereo+input:analog-stereo'
    _run([
        'pactl',
        'set-card-profile',
        card,
        profile])
    if digital:
        _run([
            'amixer',
            '-c',
            CREATIVE_ALSA_CARD,
            'set',
            'IEC958',
            'on'])
    return profile


def prepare_output_sink(sink = None):
    '''Ensure PipeWire profile + ALSA routing match the chosen output sink.'''
    if not sink:
        return None
    if _is_creative_sink(sink):
        prepare_creative_card_profile(digital = _is_digital_sink(sink))
        return None
    if _is_digital_sink(sink):
        _run([
            'amixer',
            '-c',
            CREATIVE_ALSA_CARD,
            'set',
            'IEC958',
            'on'])
        return None


def _auto_detect_output_sink():
    '''Prefer Creative analog output when nothing is configured.'''
    (code, out) = _run([
        'pactl',
        'list',
        'short',
        'sinks'])
    if code != 0:
        return ''
    creative = []
    for line in out.splitlines():
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        name = parts[1]
        if '.monitor' in name or name.startswith('effect_input.'):
            continue
        if not _match_creative(name):
            continue
        creative.append(name)
    if not creative:
        return ''
    for name in creative:
        if not 'analog-stereo' in name:
            continue
        if not 'iec958' not in name:
            continue
        
        return creative, name
    return creative[0]


def effective_output_sink():
    saved_output_sink = saved_output_sink
    import jarvis.audio_settings
    saved = saved_output_sink()
    if saved:
        return saved
    env = None.getenv('JARVIS_AUDIO_SINK', '').strip()
    if env:
        return env
    return None()


def _detect_pipewire_sink():
    return effective_output_sink()


def _pulse_default_source():
    (code, out) = _run([
        'pactl',
        'get-default-source'])
    if code == 0:
        return out.strip()


def list_input_sources():
    '''All PipeWire/Pulse capture sources (non-monitor).'''
    (code, out) = _run([
        'pactl',
        'list',
        'short',
        'sources'])
    if code != 0:
        return []
    default = None()
    sources = []
    for line in out.splitlines():
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        name = parts[1]
        if '.monitor' in name:
            continue
        state = parts[3] if len(parts) > 3 else ''
        label = name
        if 'usb' in name.lower() and 'mic' in name.lower():
            label = f'''USB Microphone ({name.split('.')[-1]})'''
        elif _is_creative_input(name):
            label = 'Creative Sound Blaster (combo jack)'
        if 'usb' in name.lower():
            'usb' in name.lower()
        sources.append({
            'name': name,
            'label': label,
            'state': state,
            'is_default': name == default,
            'is_usb_mic': 'mic' in name.lower() })
    return sources


def _output_sink_label(name = None):
    if _is_digital_sink(name):
        return 'Creative TOSLink / S/PDIF (digital)'
    if _is_creative_sink(name):
        if 'analog' in name:
            return 'Creative analog (speakers / headphones)'
        return 'Creative Sound Blaster'
    if name.startswith('effect_input.jarvis_ae5_'):
        preset = name.replace('effect_input.jarvis_ae5_', '').replace('.monitor', '')
        return f'''Jarvis AE-5 EQ ({preset})'''
    if None in name:
        return name.split('.')[-1]


def list_output_sinks():
    '''PipeWire playback sinks (non-monitor).'''
    (code, out) = _run([
        'pactl',
        'list',
        'short',
        'sinks'])
    if code != 0:
        return []
    default = None()
    sinks = []
    for line in out.splitlines():
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        name = parts[1]
        if '.monitor' in name:
            continue
        state = parts[3] if len(parts) > 3 else ''
        sinks.append({
            'name': name,
            'label': _output_sink_label(name),
            'state': state,
            'is_default': name == default,
            'is_digital': _is_digital_sink(name),
            'is_creative': _is_creative_sink(name) })
    sinks.sort(key = (lambda s: (0 if s.get('is_creative') and s.get('is_digital') else 1, 0 if s.get('is_creative') else 1, s.get('label', ''))))
    return sinks


def _auto_detect_input_source():
    '''Prefer Creative analog line/mic; USB mics only when explicitly chosen in the GUI.'''
    sources = list_input_sources()
    for s in sources:
        name = s.get('name', '')
        if not _match_creative(name):
            continue
        if not '.monitor' not in name:
            continue
        
        return sources, name
    if default and '.monitor' not in default:
        return default
    for None in _pulse_default_source():
        if s.get('is_usb_mic'):
            continue
        
        return None, s['name']
    if sources:
        return sources[0]['name']


def effective_input_source():
    saved_input_source = saved_input_source
    import jarvis.audio_settings
    saved = saved_input_source()
    if saved:
        return saved
    env = None.getenv('JARVIS_AUDIO_SOURCE', '').strip()
    if env:
        return env
    auto = None()
    if auto:
        return auto


def _detect_pipewire_source():
    return effective_input_source()


def alsa_playback_device():
    env = os.getenv('JARVIS_ALSA_PLAYBACK', '').strip()
    if env:
        return env
    device = None
    if _is_digital_sink(effective_output_sink()):
        device = os.getenv('JARVIS_ALSA_DEVICE_DIGITAL', '1')
    return f'''plughw:CARD={CREATIVE_ALSA_CARD},DEV={device}'''


def alsa_capture_device():
    env = os.getenv('JARVIS_ALSA_CAPTURE', '').strip()
    if env:
        return env
    return f'''{CREATIVE_ALSA_CARD},DEV={CREATIVE_ALSA_DEVICE}'''


def detect_devices():
    sink = effective_output_sink()
    if not sink and _is_creative_sink(sink) and _sink_exists(sink):
        prepare_output_sink(sink)
    if sink and _sink_exists(sink) and _is_creative_sink(sink):
        for s in list_output_sinks():
            if not _is_creative_sink(s['name']):
                continue
            if not _is_digital_sink(sink) == s.get('is_digital'):
                continue
            sink = s['name']
            list_output_sinks()
    alsa_play = alsa_playback_device()
    name = 'Creative Sound Blaster'
    (code, out) = _run([
        'aplay',
        '-l'])
    if code == 0:
        for line in out.splitlines():
            if not _match_creative(line):
                continue
            name = line.split(':', 2)[-1].strip()
            out.splitlines()
    backend = 'pipewire' if shutil.which('pactl') else 'alsa'
    if shutil.which('pw-play'):
        backend = 'pipewire'
    if not sink:
        sink
    return {
        'name': name,
        'backend': backend,
        'output_sink': 'alsa_output.pci-0000_05_00.0.analog-stereo',
        'output_sinks': list_output_sinks(),
        'output_digital': _is_digital_sink(sink),
        'input_source': _detect_pipewire_source(),
        'input_sources': list_input_sources(),
        'creative_mixer': creative_mixer_snapshot(),
        'mic_routing': mic_routing_status(),
        'alsa_playback': alsa_play,
        'alsa_capture': alsa_capture_device(),
        'auto_play': os.getenv('JARVIS_AUTO_PLAY', '1').lower() not in ('0', 'false', 'no'),
        'set_default_on_start': os.getenv('JARVIS_SET_DEFAULT_SINK', '1').lower() not in ('0', 'false', 'no') }


def _should_set_default_source():
    return os.getenv('JARVIS_SET_DEFAULT_SOURCE', '0').lower() not in ('0', 'false', 'no')


def creative_mixer_snapshot():
    '''Read-only Creative hardware routing (amixer sget only — never changes levels).'''
    info = { }
    for ctrl in ('Input Source', 'Mic Boost', 'Capture'):
        (code, out) = _run([
            'amixer',
            '-c',
            CREATIVE_ALSA_CARD,
            'sget',
            ctrl])
        if code != 0:
            continue
        for line in out.splitlines():
            if not 'Item0:' in line:
                continue
            info[ctrl.lower().replace(' ', '_')] = line.split(':', 1)[-1].strip().strip("'")
            out.splitlines()
    return info


def mic_routing_status():
    '''Compare saved mic profile to alsamixer Input Source (read-only).'''
    mic_profile_info = mic_profile_info
    import jarvis.audio_settings
    profile = mic_profile_info()
    mixer = creative_mixer_snapshot()
    hardware = mixer.get('input_source', '')
    expected = profile.get('expected_input_source', '')
    if not hardware:
        return {
            'profile': profile['id'],
            'profile_label': profile['label'],
            'hardware_input_source': '',
            'routing_ok': None,
            'routing_hint': profile.get('hint', '') }
    ok = None == expected
    hint = profile.get('hint', '')
    if ok and hardware and expected:
        hint = f'''Profile is {profile['label']} but alsamixer Input Source is \'{hardware}\'. Set Input Source to \'{expected}\' in alsamixer -c Creative (Jarvis will not change it).'''
    return {
        'profile': profile['id'],
        'profile_label': profile['label'],
        'hardware_input_source': hardware,
        'expected_input_source': expected,
        'mic_boost': mixer.get('mic_boost', ''),
        'routing_ok': ok,
        'routing_hint': hint }


def capture_volume_for(source = None):
    '''PipeWire capture gain per source (never touches ALSA mixer).'''
    mic_profile_info = mic_profile_info
    saved_capture_volume = saved_capture_volume
    saved_creative_capture_volume = saved_creative_capture_volume
    saved_mic_profile = saved_mic_profile
    import jarvis.audio_settings
    if _is_creative_input(source):
        if not saved_creative_capture_volume():
            saved_creative_capture_volume()
            if not os.getenv('JARVIS_CREATIVE_CAPTURE_VOLUME', '').strip():
                os.getenv('JARVIS_CREATIVE_CAPTURE_VOLUME', '').strip()
        return mic_profile_info(saved_mic_profile()).get('default_capture_volume', '100%')
    if not saved_capture_volume():
        saved_capture_volume()
        if not os.getenv('JARVIS_CAPTURE_VOLUME', '').strip():
            os.getenv('JARVIS_CAPTURE_VOLUME', '').strip()
    return '100%'


def prepare_input_source(source = None):
    '''Unmute and boost PipeWire capture volume for one source only (never opens ALSA).'''
    if not source or shutil.which('pactl'):
        return None
    _run([
        'pactl',
        'set-source-mute',
        source,
        '0'])
    _run([
        'pactl',
        'set-source-volume',
        source,
        capture_volume_for(source)])


def apply_system_default():
    '''Set PipeWire default playback sink to Creative. Input source is left alone unless opted in.'''
    dev = detect_devices()
    if not dev.get('set_default_on_start'):
        return 'skipped (JARVIS_SET_DEFAULT_SINK=0)'
    msgs = []
    sink = dev.get('output_sink', '')
    if sink and shutil.which('pactl'):
        prepare_output_sink(sink)
        (code, out) = _run([
            'pactl',
            'set-default-sink',
            sink])
        if code == 0:
            tag = 'TOSLink' if dev.get('output_digital') else 'analog'
            msgs.append(f'''default sink → {sink} ({tag})''')
        else:
            msgs.append(f'''sink failed: {out.strip()}''')
    if _should_set_default_source():
        source = dev.get('input_source', '')
        if source and shutil.which('pactl'):
            (code, out) = _run([
                'pactl',
                'set-default-source',
                source])
            if code == 0:
                msgs.append(f'''default source → {source}''')
            else:
                msgs.append(f'''source failed: {out.strip()}''')
    if msgs:
        return '; '.join(msgs)


def play_file(path = None, *, vst_chain):
    '''Play an audio file through the Creative Sound Blaster (optional VST/EQ chain).'''
    path = Path(path)
    if not path.exists():
        return f'''ERROR: File not found: {path}'''
    if not None:
        pass
    chain = ''.strip().lower()
    if not chain:
        saved_vst_playback_chain = saved_vst_playback_chain
        import jarvis.audio_settings
        if not saved_vst_playback_chain():
            saved_vst_playback_chain()
        chain = os.getenv('JARVIS_VST_CHAIN', '').strip().lower()
    if chain and chain not in ('flat', 'off', 'none'):
        process_file = process_file
        import jarvis.audio_vst
        processed = process_file(path, chain)
        if processed.startswith('ERROR:'):
            return processed
        path = None(processed)
    dev = detect_devices()
    sink = dev.get('output_sink', '')
    errors = []
    if shutil.which('pw-play') and sink:
        (ok, err) = _play_with_proc([
            'pw-play',
            '--target',
            sink,
            str(path)], timeout = 600)
        if ok:
            return str(path)
        None.append(f'''pw-play: {err}''')
    if shutil.which('paplay') and sink:
        (ok, err) = _play_with_proc([
            'paplay',
            f'''--device={sink}''',
            str(path)], timeout = 600)
        if ok:
            return str(path)
        None.append(f'''paplay: {err}''')
    if os.getenv('JARVIS_PLAYBACK_USE_ALSA', '').lower() in ('1', 'true', 'yes') and shutil.which('aplay'):
        alsa = dev.get('alsa_playback', alsa_playback_device())
        (ok, err) = _play_with_proc([
            'aplay',
            '-D',
            alsa,
            str(path)], timeout = 600)
        if ok:
            return str(path)
        None.append(f'''aplay: {err}''')
    return f'''ERROR: Could not play audio. {' | '.join(errors)}'''


def ffmpeg_env():
    '''Environment for ffmpeg subprocesses (ALSA device hints).'''
    dev = detect_devices()
    env = os.environ.copy()
    env['AUDIODEV'] = dev.get('alsa_playback', alsa_playback_device())
    env['ALSA_PCM_CARD'] = CREATIVE_ALSA_CARD
    env['ALSA_PCM_DEVICE'] = CREATIVE_ALSA_DEVICE
    return env


def measure_levels_db(path = None):
    '''Peak and mean volume in dB from ffmpeg volumedetect.'''
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg or path.exists():
        return {
            'peak_db': None,
            'mean_db': None }
    (code, out) = None([
        ffmpeg,
        '-hide_banner',
        '-i',
        str(path),
        '-af',
        'volumedetect',
        '-f',
        'null',
        '-'], timeout = 60)
    if code != 0:
        return {
            'peak_db': None,
            'mean_db': None }
    levels = {
        'peak_db': None,
        'mean_db': None }
    for line in out.splitlines():
        if 'max_volume:' in line:
            m = re.search('max_volume:\\s*(-?\\d+(?:\\.\\d+)?)\\s*dB', line)
            if m:
                levels['peak_db'] = float(m.group(1))
        if not 'mean_volume:' in line:
            continue
        m = re.search('mean_volume:\\s*(-?\\d+(?:\\.\\d+)?)\\s*dB', line)
        if not m:
            continue
        levels['mean_db'] = float(m.group(1))
    return levels


def measure_peak_db(path = None):
    return measure_levels_db(path).get('peak_db')


def sample_input_peak_db(source = None, *, duration_ms):
    '''Quick mic peak dB sample for barge-in during TTS playback.'''
    if not source:
        source
    src = effective_input_source().strip()
    if not src:
        return None
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        return None
    
    try:
        proc = subprocess.run([
            ffmpeg,
            '-hide_banner',
            '-loglevel',
            'error',
            '-f',
            'pulse',
            '-i',
            src,
            '-t',
            str(max(0.05, duration_ms / 1000)),
            '-ar',
            '16000',
            '-ac',
            '1',
            '-f',
            's16le',
            'pipe:1'], capture_output = True, timeout = 2)
        if not proc.returncode != 0 or proc.stdout:
            return None
        
        try:
            import numpy as np
            arr = np.frombuffer(proc.stdout, dtype = np.int16)
            if arr.size == 0:
                return None
                
                try:
                    peak = int(np.max(np.abs(arr)))
                    return round(20 * np.log10(peak / 32768 + 1e-09), 1)
                    except Exception:
                        return None
                except Exception:
                    return None





def _speech_enhance_af(source = None):
    '''ffmpeg -af chain: denoise + level speech without touching ALSA.'''
    if 'usb' in source.lower() and 'mic' in source.lower():
        return 'highpass=f=150,lowpass=f=6000,afftdn=nf=-25,agate=threshold=-38dB:ratio=6:attack=12:release=180,acompressor=threshold=-24dB:ratio=3:makeup=6,loudnorm=I=-14:TP=-1:LRA=9'
    if _is_creative_input(source):
        if not os.getenv('JARVIS_CREATIVE_GATE_DB', '-34').strip():
            os.getenv('JARVIS_CREATIVE_GATE_DB', '-34').strip()
        gate = '-34'
        if not os.getenv('JARVIS_CREATIVE_DENOISE_NF', '-22').strip():
            os.getenv('JARVIS_CREATIVE_DENOISE_NF', '-22').strip()
        nf = '-22'
        if not os.getenv('JARVIS_CREATIVE_MAKEUP_DB', '10').strip():
            os.getenv('JARVIS_CREATIVE_MAKEUP_DB', '10').strip()
        makeup = '10'
        if not os.getenv('JARVIS_PLAYBACK_LOUDNESS', '-14').strip():
            os.getenv('JARVIS_PLAYBACK_LOUDNESS', '-14').strip()
        loudness = '-14'
        return f'''highpass=f=200,lowpass=f=5500,afftdn=nf={nf}:nt=w,agate=threshold={gate}dB:ratio=8:attack=8:release=180,acompressor=threshold=-22dB:ratio=4:makeup={makeup}:attack=5:release=80,loudnorm=I={loudness}:TP=-1:LRA=9'''
    return 'highpass=f=120,afftdn,dynaudnorm=f=120:g=12,alimiter=limit=0.92'


def normalize_recording(path = None, *, source):
    '''Denoise and level capture for playback and Whisper (in-place, software only).'''
    if os.getenv('JARVIS_RECORD_NORMALIZE', '1').lower() in ('0', 'false', 'no'):
        return True
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg or path.exists():
        return False
    tmp = path.with_suffix('.norm.wav')
    if not source:
        source
    af = _speech_enhance_af(effective_input_source())
    (code, _) = _run([
        ffmpeg,
        '-y',
        '-hide_banner',
        '-loglevel',
        'error',
        '-i',
        str(path),
        '-ar',
        '16000',
        '-ac',
        '1',
        '-af',
        af,
        str(tmp)], timeout = 120)
    if code == 0 and tmp.exists() and tmp.stat().st_size > 1000:
        tmp.replace(path)
        return True
    tmp.unlink(missing_ok = True)
    return False


def _silent_recording_message(source = None, peak = None, mean = None):
    pass
# WARNING: Decompyle incomplete


def _finalize_recording(dest = None, input_source = None, min_peak_db = None):
    normalize_recording(dest, source = input_source)
    levels = measure_levels_db(dest)
    peak = levels.get('peak_db')
    mean = levels.get('mean_db')
# WARNING: Decompyle incomplete


def _convert_to_whisper_wav(src = None, dest = None, sample_rate = None, *, source):
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        return (False, 'ffmpeg not found')
    if not source:
        source
    src_name = effective_input_source()
    af = f'''pan=mono|c0=0.5*c0+0.5*c1,{_speech_enhance_af(src_name)}'''
    (code, out) = _run([
        ffmpeg,
        '-y',
        '-hide_banner',
        '-loglevel',
        'error',
        '-i',
        str(src),
        '-ar',
        str(sample_rate),
        '-ac',
        '1',
        '-af',
        af,
        str(dest)], timeout = 60)
    if not code != 0 or dest.exists():
        return (False, out.strip()[-400:])
    return (None, str(dest))


def _use_creative_alsa_capture():
    '''Opt-in: record via arecord subprocess only — never calls amixer or changes defaults.'''
    return os.getenv('JARVIS_CREATIVE_ALSA_CAPTURE', '0').lower() in ('1', 'true', 'yes')


def _record_alsa_arecord(dest = None, duration_sec = None, *, sample_rate):
    '''Direct card read via arecord (bypasses PipeWire node; does not touch mixer).'''
    arecord = shutil.which('arecord')
    if not arecord:
        return (False, 'arecord not found')
    alsa = alsa_capture_device()
    secs = max(1, int(round(duration_sec)))
    cmd = [
        arecord,
        '-q',
        '-D',
        alsa,
        '-f',
        'S16_LE',
        '-r',
        str(sample_rate),
        '-c',
        '1',
        '-d',
        str(secs),
        str(dest)]
    (code, out) = _run(cmd, timeout = secs + 15)
    if code == 0 and dest.exists() and dest.stat().st_size > 1000:
        return (True, str(dest))
    if not out.strip()[-400:]:
        out.strip()[-400:]
    return (None, 'arecord failed')


def _record_with_pw_record(dest = None, duration_sec = None, source = None, *, sample_rate, stereo):
    if not shutil.which('pw-record'):
        return (False, 'pw-record not available')
    tmp = dest.with_name(dest.stem + '_raw.wav')
    channels = '2' if stereo else '1'
    rate = '48000' if stereo else str(sample_rate)
    cmd = [
        'pw-record',
        '--target',
        source,
        '--rate',
        rate,
        '--channels',
        channels,
        '--format',
        's16',
        str(tmp)]
    proc = subprocess.Popen(cmd, stderr = subprocess.PIPE, text = True)
    
    try:
        time.sleep(duration_sec)
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout = 8)
        err = proc.stderr.read() if proc.stderr else ''.strip()
        if tmp.exists() or tmp.stat().st_size < 1000:
            tmp.unlink(missing_ok = True)
            if not err[-400:]:
                err[-400:]
            return (False, 'pw-record produced empty file')
        if None:
            (ok, msg) = _convert_to_whisper_wav(tmp, dest, sample_rate, source = source)
            tmp.unlink(missing_ok = True)
            return (ok, msg)
        if None != dest:
            tmp.replace(dest)
        return (True, str(dest))
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout = 3)
        tmp.unlink(missing_ok = True)
        return (False, 'pw-record timed out')



def record_to_file(dest = None, duration_sec = None, *, sample_rate, source, min_peak_db):
    '''Record via PipeWire (default). Optional arecord for Creative — never calls amixer.'''
    ffmpeg = shutil.which('ffmpeg')
    if not shutil.which('pw-record') and _use_creative_alsa_capture():
        return 'ERROR: Need pw-record for PipeWire capture.'
    duration_sec = max(0.5, min(float(duration_sec), 120))
    dest = Path(dest)
    dest.parent.mkdir(parents = True, exist_ok = True)
    if not source:
        source
    input_source = effective_input_source().strip()
    if not input_source:
        return 'ERROR: No capture source configured.'
    errors = []
    use_stereo = _is_creative_input(input_source)
    if _is_creative_input(input_source) and _use_creative_alsa_capture():
        (ok, msg) = _record_alsa_arecord(dest, duration_sec, sample_rate = sample_rate)
        if ok and dest.exists():
            return _finalize_recording(dest, input_source, min_peak_db)
        if None:
            errors.append(f'''arecord ({alsa_capture_device()}): {msg}''')
    if shutil.which('pactl'):
        prepare_input_source(input_source)
    (ok, msg) = _record_with_pw_record(dest, duration_sec, input_source, sample_rate = sample_rate, stereo = use_stereo)
    if ok and dest.exists():
        return _finalize_recording(dest, input_source, min_peak_db)
    if None:
        errors.append(f'''pw-record: {msg}''')
    if ffmpeg:
        cmd = [
            ffmpeg,
            '-y',
            '-hide_banner',
            '-loglevel',
            'error',
            '-f',
            'pulse',
            '-i',
            input_source,
            '-t',
            str(duration_sec),
            '-ar',
            str(sample_rate),
            '-ac',
            '1',
            str(dest)]
        (code, out) = _run(cmd, timeout = int(duration_sec) + 30)
        if code == 0 and dest.exists():
            return _finalize_recording(dest, input_source, min_peak_db)
        None.append(f'''pulse ({input_source}): {out.strip()[-400:]}''')
    backend = 'arecord+PipeWire' if _use_creative_alsa_capture() else 'PipeWire'
    return f'''ERROR: Could not record from `{input_source}` ({backend}). {' | '.join(errors)}'''


def probe_capture(source = None, duration_sec = None):
    '''Short PipeWire capture test — returns levels without keeping the file.'''
    import tempfile
    if not source:
        source
    input_source = effective_input_source().strip()
    if not input_source:
        return {
            'ok': False,
            'message': 'No capture source' }
    tmp = None.TemporaryDirectory()
    dest = Path(tmp) / 'probe.wav'
    result = record_to_file(dest, duration_sec, source = input_source, min_peak_db = -90)
    if result.startswith('ERROR:'):
        None(None, None)
        return 
    levels.get('peak_db') = None(dest)
    if peak is not None:
        peak is not None
    None(None, None)
    return 
    with None:
        if not None, {
            'ok': True,
            'source': input_source,
            'peak_db': peak,
            'mean_db': levels.get('mean_db'),
            'pipewire_volume': capture_volume_for(input_source),
            'likely_ok': peak > -40,
            'mic_routing': mic_routing_status() }:
            pass

_active_ptt: dict[(str, dict)] = { }

def _ptt_record_cmd(dest = None, source = None, *, sample_rate, stereo):
    channels = '2' if stereo else '1'
    rate = '48000' if stereo else str(sample_rate)
    return [
        'pw-record',
        '--target',
        source,
        '--rate',
        rate,
        '--channels',
        channels,
        '--format',
        's16',
        str(dest)]


def _cancel_stale_ptt_sessions():
    pass
# WARNING: Decompyle incomplete


def start_ptt_record(dest = None, source = None):
    '''Start push-to-talk capture. Returns (session_id, error_or_empty).'''
    if not shutil.which('pw-record'):
        return ('', 'ERROR: pw-record not available')
    before_listen = before_listen
    import jarvis.voice_duplex
    before_listen()
    _cancel_stale_ptt_sessions()
    if not source:
        source
    input_source = effective_input_source().strip()
    if not input_source:
        return ('', 'ERROR: No capture source configured.')
    dest = Path(dest)
    dest.parent.mkdir(parents = True, exist_ok = True)
    tmp = dest.with_name(dest.stem + '_ptt_raw.wav')
    use_stereo = _is_creative_input(input_source)
    if shutil.which('pactl'):
        prepare_input_source(input_source)
    proc = subprocess.Popen(_ptt_record_cmd(tmp, input_source, stereo = use_stereo), stderr = subprocess.PIPE, text = True)
    import uuid
    session_id = uuid.uuid4().hex[:12]
    _active_ptt[session_id] = {
        'proc': proc,
        'tmp': tmp,
        'dest': dest,
        'source': input_source,
        'stereo': use_stereo }
    return (session_id, '')


def stop_ptt_record(session_id = None, *, min_peak_db):
    '''Stop PTT session and finalize WAV.'''
    entry = _active_ptt.pop(session_id, None)
    if not entry:
        return 'ERROR: No active recording for that session.'
    proc = entry['proc']
    tmp = entry['tmp']
    dest = entry['dest']
    source = entry['source']
    stereo = entry['stereo']
# WARNING: Decompyle incomplete


def trim_silence_vad(src = None, dst = None, *, threshold_db, min_silence_sec, padding_sec):
    '''Trim leading/trailing silence after a max-duration capture.'''
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        return 'ERROR: ffmpeg not found'
    src = Path(src)
    if not src.exists():
        return f'''ERROR: File not found: {src}'''
    out = Path(dst) if None else src.with_name(f'''{src.stem}_vad{src.suffix}''')
    out.parent.mkdir(parents = True, exist_ok = True)
    thr = f'''{threshold_db}dB'''
    af = f'''silenceremove=start_periods=1:start_duration={padding_sec}:start_threshold={thr}:stop_periods=1:stop_duration={min_silence_sec}:stop_threshold={thr}'''
    (code, err) = _run([
        ffmpeg,
        '-y',
        '-hide_banner',
        '-loglevel',
        'error',
        '-i',
        str(src),
        '-af',
        af,
        str(out)], timeout = 120, env = ffmpeg_env())
    if not code != 0 or out.exists():
        return f'''ERROR: VAD trim failed: {err.strip()[-400:]}'''
    if None != src:
        src.unlink(missing_ok = True)
    return str(out)

