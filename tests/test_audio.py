# Source Generated with Decompyle++
# File: test_audio.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for Jarvis audio module.'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
from unittest.mock import MagicMock, patch
import pytest
from jarvis.modules.audio import AudioEngine
audio_engine = (lambda monkeypatch: monkeypatch.setenv('JARVIS_AUTO_PLAY', '0')monkeypatch.setenv('JARVIS_SET_DEFAULT_SINK', '0')patch.object(AudioEngine, '__init__', (lambda self: pass))
    engine = AudioEngine()
    None(None, None)
# WARNING: Decompyle incomplete
)()

def test_default_whisper_model(monkeypatch):
    monkeypatch.setenv('JARVIS_WHISPER_MODEL', 'small')
    patch.object(AudioEngine, '__init__', (lambda self: pass))
    engine = AudioEngine()
    None(None, None)
# WARNING: Decompyle incomplete


def test_build_fade_out_uses_duration(audio_engine):
    cmd = audio_engine._build_ffmpeg_edit_cmd(Path('/tmp/in.wav'), Path('/tmp/out.wav'), fade_out_sec = 2, src_duration = 10)
    joined = ' '.join(cmd)
    @py_assert0 = 'afade=t=out:st=8.0:d=2.0'
    @py_assert2 = @py_assert0 in joined
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, joined)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(joined) if 'joined' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(joined) else 'joined' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_transcribe_uses_env_model(audio_engine, monkeypatch, tmp_path):
    monkeypatch.setenv('JARVIS_WHISPER_MODEL', 'tiny')
    wav = tmp_path / 'clip.wav'
    wav.write_bytes(b'RIFF')
    tmp_path / 'clip.txt'
    patch.object(audio_engine, '_resolve_audio', return_value = wav)
    fw = patch('jarvis.audio_whisper.transcribe', return_value = 'hello world')
    patch('jarvis.audio_search.index_transcript')
    result = audio_engine.transcribe(str(wav), model = 'tiny')
    None(None, None)
    None(None, None)
    None(None, None)
    @py_assert2 = 'hello world'
# WARNING: Decompyle incomplete


def test_record_delegates(audio_engine, tmp_path):
    out = tmp_path / 'rec.wav'
    rec = patch('jarvis.modules.audio.record_to_file', return_value = str(out))
    result = audio_engine.record(3, source = 'alsa_input.usb-mic')
    None(None, None)
# WARNING: Decompyle incomplete


def test_effective_input_source_prefers_creative_over_usb(monkeypatch):
    audio_device = audio_device
    import jarvis
    monkeypatch.delenv('JARVIS_AUDIO_SOURCE', raising = False)
    usb = 'alsa_input.usb-BlueTrm_USB_MIC_20170726905923-00.mono-fallback'
    creative = 'alsa_input.pci-0000_04_00.0.analog-stereo'
    patch('jarvis.audio_settings.saved_input_source', return_value = '')
    patch.object(audio_device, 'list_input_sources', return_value = [
        {
            'name': usb,
            'is_usb_mic': True },
        {
            'name': creative,
            'is_usb_mic': False }])
    @py_assert1 = audio_device.effective_input_source
    @py_assert3 = @py_assert1()
    @py_assert5 = @py_assert3 == creative
    if not @py_assert5:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.effective_input_source\n}()\n} == %(py6)s',), (@py_assert3, creative)) % {
            'py0': @pytest_ar._saferepr(audio_device) if 'audio_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(audio_device) else 'audio_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(creative) if 'creative' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(creative) else 'creative' }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    None(None, None)
    None(None, None)
    return None
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass


def test_effective_input_source_uses_saved_usb_when_set(monkeypatch):
    audio_device = audio_device
    import jarvis
    usb = 'alsa_input.usb-BlueTrm_USB_MIC_20170726905923-00.mono-fallback'
    patch('jarvis.audio_settings.saved_input_source', return_value = usb)
    @py_assert1 = audio_device.effective_input_source
    @py_assert3 = @py_assert1()
    @py_assert5 = @py_assert3 == usb
    if not @py_assert5:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.effective_input_source\n}()\n} == %(py6)s',), (@py_assert3, usb)) % {
            'py0': @pytest_ar._saferepr(audio_device) if 'audio_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(audio_device) else 'audio_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(usb) if 'usb' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(usb) else 'usb' }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    None(None, None)
    return None
    with None:
        if not None:
            pass


def test_effective_output_sink_uses_saved_digital(monkeypatch):
    audio_device = audio_device
    import jarvis
    digital = 'alsa_output.pci-0000_05_00.0.iec958-stereo'
    patch('jarvis.audio_settings.saved_output_sink', return_value = digital)
    @py_assert1 = audio_device.effective_output_sink
    @py_assert3 = @py_assert1()
    @py_assert5 = @py_assert3 == digital
    if not @py_assert5:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.effective_output_sink\n}()\n} == %(py6)s',), (@py_assert3, digital)) % {
            'py0': @pytest_ar._saferepr(audio_device) if 'audio_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(audio_device) else 'audio_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(digital) if 'digital' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(digital) else 'digital' }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    None(None, None)
    return None
    with None:
        if not None:
            pass


def test_is_digital_sink():
    audio_device = audio_device
    import jarvis
    @py_assert1 = audio_device._is_digital_sink
    @py_assert3 = 'alsa_output.pci-0000_05_00.0.iec958-stereo'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s._is_digital_sink\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(audio_device) if 'audio_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(audio_device) else 'audio_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = audio_device._is_digital_sink
    @py_assert3 = 'alsa_output.pci-0000_05_00.0.analog-stereo'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s._is_digital_sink\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(audio_device) if 'audio_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(audio_device) else 'audio_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_prepare_creative_card_profile_digital(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_alsa_playback_device_digital(monkeypatch):
    audio_device = audio_device
    import jarvis
    monkeypatch.setenv('JARVIS_ALSA_PLAYBACK', '')
    patch.object(audio_device, 'effective_output_sink', return_value = 'alsa_output.pci-0000_05_00.0.iec958-stereo')
    @py_assert1 = audio_device.alsa_playback_device
    @py_assert3 = @py_assert1()
    @py_assert6 = 'plughw:CARD=Creative,DEV=1'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.alsa_playback_device\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(audio_device) if 'audio_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(audio_device) else 'audio_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    None(None, None)
    return None
    with None:
        if not None:
            pass


def test_capture_volume_for_creative_defaults_100(monkeypatch):
    audio_device = audio_device
    import jarvis
    monkeypatch.delenv('JARVIS_CREATIVE_CAPTURE_VOLUME', raising = False)
    monkeypatch.delenv('JARVIS_CAPTURE_VOLUME', raising = False)
    patch('jarvis.audio_settings.saved_creative_capture_volume', return_value = '')
    @py_assert1 = audio_device.capture_volume_for
    @py_assert3 = 'alsa_input.pci-0000_04_00.0.analog-stereo'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = '100%'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.capture_volume_for\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(audio_device) if 'audio_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(audio_device) else 'audio_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    None(None, None)
    return None
    with None:
        if not None:
            pass


def test_capture_volume_for_creative(monkeypatch):
    audio_device = audio_device
    import jarvis
    monkeypatch.setenv('JARVIS_CREATIVE_CAPTURE_VOLUME', '200%')
    patch('jarvis.audio_settings.saved_creative_capture_volume', return_value = '')
    @py_assert1 = audio_device.capture_volume_for
    @py_assert3 = 'alsa_input.pci-0000_04_00.0.analog-stereo'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = '200%'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.capture_volume_for\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(audio_device) if 'audio_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(audio_device) else 'audio_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None
    None(None, None)
    return None
    with None:
        if not None:
            pass


def test_prepare_input_source_uses_pactl_only(monkeypatch):
    audio_device = audio_device
    import jarvis
    patch('jarvis.audio_settings.saved_creative_capture_volume', return_value = '200%')
    run = patch.object(audio_device, '_run')
    audio_device.prepare_input_source('alsa_input.pci-0000_04_00.0.analog-stereo')
    None(None, None)
    None(None, None)
# WARNING: Decompyle incomplete


def test_mic_routing_status_mismatch():
    audio_device = audio_device
    import jarvis
    patch.object(audio_device, 'creative_mixer_snapshot', return_value = {
        'input_source': 'Microphone' })
    patch('jarvis.audio_settings.saved_mic_profile', return_value = 'front')
    st = audio_device.mic_routing_status()
    None(None, None)
    None(None, None)
# WARNING: Decompyle incomplete


def test_speech_enhance_af_creative():
    audio_device = audio_device
    import jarvis
    af = audio_device._speech_enhance_af('alsa_input.pci-0000_04_00.0.analog-stereo')
    @py_assert0 = 'afftdn'
    @py_assert2 = @py_assert0 in af
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, af)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(af) if 'af' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(af) else 'af' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'loudnorm'
    @py_assert2 = @py_assert0 in af
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, af)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(af) if 'af' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(af) else 'af' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'agate'
    @py_assert2 = @py_assert0 in af
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, af)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(af) if 'af' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(af) else 'af' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_record_rejects_silent(tmp_path):
    audio_device = audio_device
    import jarvis
    dest = tmp_path / 'silent.wav'
    dest.write_bytes(b'RIFF')
    patch.object(audio_device, 'measure_levels_db', return_value = {
        'peak_db': -58.5,
        'mean_db': -70 })
    patch.object(audio_device, 'normalize_recording', return_value = True)
    patch.object(audio_device, '_record_with_pw_record', return_value = (True, str(dest)))
    patch.object(audio_device, 'prepare_input_source')
    result = audio_device.record_to_file(dest, 1, source = 'alsa_input.pci-0000_04_00.0.analog-stereo')
    None(None, None)
    None(None, None)
    None(None, None)
    None(None, None)
# WARNING: Decompyle incomplete


def test_status_shape(audio_engine):
    patch.object(audio_engine, '_whisper_path', return_value = '/bin/whisper')
    patch.object(audio_engine, '_ffmpeg_path', return_value = '/bin/ffmpeg')
    patch.object(audio_engine, '_espeak_path', return_value = '/bin/espeak')
    patch.object(audio_engine, 'get_devices', return_value = {
        'name': 'Test' })
    patch('jarvis.config.piper_ready', return_value = False)
    st = audio_engine.status()
    None(None, None)
    None(None, None)
    None(None, None)
    None(None, None)
    None(None, None)
# WARNING: Decompyle incomplete


def test_music_gen_missing_backends(tmp_path, monkeypatch):
    music_gen = music_gen
    import jarvis
    monkeypatch.setattr(music_gen, 'MUSIC_DIR', tmp_path)
    monkeypatch.setattr(music_gen, '_transformers_available', (lambda : False))
    monkeypatch.setattr(music_gen, '_audiocraft_available', (lambda : False))
    result = music_gen.generate_music('calm piano', duration = 5)
    @py_assert1 = result.startswith
    @py_assert3 = 'ERROR:'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.startswith\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_musicgen_backend_detects_transformers():
    musicgen_available = musicgen_available
    musicgen_backend = musicgen_backend
    import jarvis.music_gen
    @py_assert2 = musicgen_available()
    @py_assert5 = isinstance(@py_assert2, bool)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n}, %(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(musicgen_available) if 'musicgen_available' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(musicgen_available) else 'musicgen_available',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py4': @pytest_ar._saferepr(bool) if 'bool' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bool) else 'bool',
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert2 = None
    @py_assert5 = None
    if musicgen_available():
        @py_assert1 = musicgen_backend()
        @py_assert4 = ('transformers', 'audiocraft')
        @py_assert3 = @py_assert1 in @py_assert4
        if not @py_assert3:
            @py_format6 = @pytest_ar._call_reprcompare(('in',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} in %(py5)s',), (@py_assert1, @py_assert4)) % {
                'py0': @pytest_ar._saferepr(musicgen_backend) if 'musicgen_backend' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(musicgen_backend) else 'musicgen_backend',
                'py2': @pytest_ar._saferepr(@py_assert1),
                'py5': @pytest_ar._saferepr(@py_assert4) }
            @py_format8 = 'assert %(py7)s' % {
                'py7': @py_format6 }
            raise AssertionError(@pytest_ar._format_explanation(@py_format8))
        @py_assert1 = None
        @py_assert3 = None
        @py_assert4 = None
        return None


def test_saved_whisper_model():
    WHISPER_MODELS = WHISPER_MODELS
    saved_whisper_model = saved_whisper_model
    import jarvis.audio_settings
    @py_assert0 = 'base'
    @py_assert2 = @py_assert0 in WHISPER_MODELS
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, WHISPER_MODELS)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(WHISPER_MODELS) if 'WHISPER_MODELS' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(WHISPER_MODELS) else 'WHISPER_MODELS' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert1 = []
    @py_assert3 = saved_whisper_model()
    @py_assert6 = ''
    @py_assert5 = @py_assert3 == @py_assert6
    @py_assert0 = @py_assert5
    if not @py_assert5:
        @py_assert12 = saved_whisper_model()
        @py_assert14 = @py_assert12 in WHISPER_MODELS
        @py_assert0 = @py_assert14
# WARNING: Decompyle incomplete


def test_default_whisper_model_uses_saved(monkeypatch):
    patch.object(AudioEngine, '__init__', (lambda self: pass))
    engine = AudioEngine()
    None(None, None)
    patch('jarvis.modules.audio.saved_whisper_model', return_value = 'small')
# WARNING: Decompyle incomplete


def test_analyze_audio(audio_engine, monkeypatch, tmp_path):
    wav = tmp_path / 'clip.wav'
    wav.write_bytes(b'RIFF')
    patch.object(audio_engine, 'transcribe', return_value = 'hello there')
    patch('jarvis.modules.audio.llm.ask', return_value = 'Summary line')
    result = audio_engine.analyze(str(wav))
    None(None, None)
    None(None, None)
# WARNING: Decompyle incomplete


def test_waveform_peaks(audio_engine, tmp_path):
    import struct
    import wave
    wav = tmp_path / 'tone.wav'
    wf = wave.open(str(wav), 'w')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(8000)
    frames = struct.pack('<h', 16000) * 800
    wf.writeframes(frames)
    None(None, None)
    patch.object(audio_engine, '_resolve_audio', return_value = wav)
    patch.object(audio_engine, '_probe_duration', return_value = 0.1)
    result = audio_engine.waveform(str(wav), samples = 50)
    None(None, None)
    None(None, None)
# WARNING: Decompyle incomplete


def test_ptt_cancels_stale_sessions():
    audio_device = audio_device
    import jarvis
    patch('jarvis.audio_device.shutil.which', return_value = '/usr/bin/pw-record')
    patch.object(audio_device, 'effective_input_source', return_value = 'alsa_input.test')
    patch.object(audio_device, 'prepare_input_source')
    patch.object(audio_device, '_is_creative_input', return_value = False)
    popen = patch('jarvis.audio_device.subprocess.Popen')
    proc = MagicMock()
    proc.poll.return_value = None
    popen.return_value = proc
    (sid1, _) = audio_device.start_ptt_record(Path('/tmp/a.wav'))
    (sid2, _) = audio_device.start_ptt_record(Path('/tmp/b.wav'))
    None(None, None)
    None(None, None)
    None(None, None)
    None(None, None)
    None(None, None)
# WARNING: Decompyle incomplete


def test_record_ptt_flow(audio_engine, tmp_path, monkeypatch):
    out = tmp_path / 'ptt.wav'
    patch('jarvis.modules.audio.start_ptt_record', return_value = ('abc123', ''))
    patch('jarvis.modules.audio.RECORDINGS_DIR', tmp_path)
    (sid, path) = audio_engine.record_ptt_start()
    None(None, None)
    None(None, None)
    @py_assert2 = 'abc123'
# WARNING: Decompyle incomplete


def test_audio_search_index():
    index_transcript = index_transcript
    search = search
    import jarvis.audio_search
    index_transcript('/tmp/test.wav', 'hello jarvis audio search', title = 'test.wav')
    hits = search('jarvis audio')
    @py_assert1 = hits()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_whisper_backend():
    whisper_backend = whisper_backend
    import jarvis.audio_whisper
    @py_assert1 = whisper_backend()
    @py_assert4 = ('faster-whisper', 'cli', 'none')
    @py_assert3 = @py_assert1 in @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('in',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} in %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(whisper_backend) if 'whisper_backend' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(whisper_backend) else 'whisper_backend',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_torch_device():
    device_info = device_info
    torch_device = torch_device
    whisper_device = whisper_device
    import jarvis.torch_device
    @py_assert1 = torch_device()
    @py_assert4 = ('cuda', 'cpu', 'mps')
    @py_assert3 = @py_assert1 in @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('in',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} in %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(torch_device) if 'torch_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(torch_device) else 'torch_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert1 = whisper_device()
    @py_assert4 = ('cuda', 'cpu', 'auto')
    @py_assert3 = @py_assert1 in @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('in',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} in %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(whisper_device) if 'whisper_device' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(whisper_device) else 'whisper_device',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    info = device_info()
    @py_assert0 = 'device'
    @py_assert2 = @py_assert0 in info
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, info)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(info) if 'info' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(info) else 'info' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'whisper_device'
    @py_assert2 = @py_assert0 in info
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, info)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(info) if 'info' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(info) else 'info' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_hf_token_configured(monkeypatch):
    diarize_status = diarize_status
    hf_token_configured = hf_token_configured
    import jarvis.audio_diarize
    monkeypatch.delenv('HF_TOKEN', raising = False)
    monkeypatch.delenv('HUGGINGFACE_TOKEN', raising = False)
    @py_assert1 = hf_token_configured()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(hf_token_configured) if 'hf_token_configured' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hf_token_configured) else 'hf_token_configured',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    st = diarize_status()
    @py_assert0 = 'pyannote'
    @py_assert2 = @py_assert0 in st
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, st)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(st) if 'st' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(st) else 'st' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = st['hf_token']
    @py_assert3 = False
    @py_assert2 = @py_assert0 is @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_diarize_fallback(tmp_path):
    _format_diarized = _format_diarized
    import jarvis.audio_diarize
    segs = [
        {
            'speaker': 'Speaker A',
            'start': 0,
            'end': 1,
            'text': 'hello' },
        {
            'speaker': 'Speaker B',
            'start': 2,
            'end': 3,
            'text': 'world' }]
    text = _format_diarized(segs)
    @py_assert0 = 'Speaker A'
    @py_assert2 = @py_assert0 in text
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, text)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(text) if 'text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(text) else 'text' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'hello'
    @py_assert2 = @py_assert0 in text
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, text)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(text) if 'text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(text) else 'text' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_clean_wakeword_transcript():
    _clean_wakeword_transcript = _clean_wakeword_transcript
    import jarvis.audio_wakeword
    @py_assert1 = "Hey Jarvis, what's the weather?"
    @py_assert3 = _clean_wakeword_transcript(@py_assert1)
    @py_assert6 = "what's the weather?"
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(_clean_wakeword_transcript) if '_clean_wakeword_transcript' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_clean_wakeword_transcript) else '_clean_wakeword_transcript',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = 'Hey ARIA, set a timer'
    @py_assert3 = _clean_wakeword_transcript(@py_assert1)
    @py_assert6 = 'set a timer'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(_clean_wakeword_transcript) if '_clean_wakeword_transcript' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_clean_wakeword_transcript) else '_clean_wakeword_transcript',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = "hey aria what's up"
    @py_assert3 = _clean_wakeword_transcript(@py_assert1)
    @py_assert6 = "what's up"
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(_clean_wakeword_transcript) if '_clean_wakeword_transcript' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_clean_wakeword_transcript) else '_clean_wakeword_transcript',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert1 = 'hey jarvis'
    @py_assert3 = _clean_wakeword_transcript(@py_assert1)
    @py_assert6 = 'hey jarvis'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(_clean_wakeword_transcript) if '_clean_wakeword_transcript' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_clean_wakeword_transcript) else '_clean_wakeword_transcript',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None


def test_wakeword_status():
    status = status
    wakeword_available = wakeword_available
    wakeword_phrase = wakeword_phrase
    import jarvis.audio_wakeword
    @py_assert2 = wakeword_available()
    @py_assert5 = isinstance(@py_assert2, bool)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n}, %(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(wakeword_available) if 'wakeword_available' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(wakeword_available) else 'wakeword_available',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py4': @pytest_ar._saferepr(bool) if 'bool' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bool) else 'bool',
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert2 = None
    @py_assert5 = None
    st = status()
    @py_assert0 = 'available'
    @py_assert2 = @py_assert0 in st
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, st)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(st) if 'st' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(st) else 'st' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'record_on_detect'
    @py_assert2 = @py_assert0 in st
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, st)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(st) if 'st' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(st) else 'st' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'phrase'
    @py_assert2 = @py_assert0 in st
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, st)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(st) if 'st' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(st) else 'st' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert1 = 'hey_jarvis'
    @py_assert3 = wakeword_phrase(@py_assert1)
    @py_assert6 = 'Hey ARIA'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(wakeword_phrase) if 'wakeword_phrase' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(wakeword_phrase) else 'wakeword_phrase',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert6 = None
    @py_assert0 = st['model_resolved']
    @py_assert3 = 'hey_jarvis'
    @py_assert2 = @py_assert0 == @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None


def test_load_wakeword_model():
    OWW_FRAME_SAMPLES = OWW_FRAME_SAMPLES
    load_wakeword_model = load_wakeword_model
    import jarvis.audio_wakeword
    import numpy as np
    model = load_wakeword_model('hey_jarvis')
    @py_assert1 = model.models
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.models\n}' % {
            'py0': @pytest_ar._saferepr(model) if 'model' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(model) else 'model',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None
    frame = np.zeros(OWW_FRAME_SAMPLES, dtype = np.int16)
    pred = model.predict(frame)
    if not pred:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(pred) if 'pred' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(pred) else 'pred' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    model_aria = load_wakeword_model('hey_aria')
    @py_assert1 = model_aria.models
    if not @py_assert1:
        @py_format3 = 'assert %(py2)s\n{%(py2)s = %(py0)s.models\n}' % {
            'py0': @pytest_ar._saferepr(model_aria) if 'model_aria' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(model_aria) else 'model_aria',
            'py2': @pytest_ar._saferepr(@py_assert1) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert1 = None


def test_sanitize_for_speech_strips_sources_block():
    plain_speak_text = plain_speak_text
    sanitize_for_speech = sanitize_for_speech
    import jarvis.tts_stream
    text = 'The answer is 42.\n\n**Sources**\n1. [Example](https://example.com)\n2. www.example.org/page'
    cleaned = sanitize_for_speech(text)
    @py_assert0 = 'Sources'
    @py_assert2 = @py_assert0 not in cleaned
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, cleaned)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(cleaned) if 'cleaned' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cleaned) else 'cleaned' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'example.com'
    @py_assert2 = @py_assert0 not in cleaned
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, cleaned)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(cleaned) if 'cleaned' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cleaned) else 'cleaned' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = '42'
    @py_assert2 = @py_assert0 in cleaned
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, cleaned)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(cleaned) if 'cleaned' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cleaned) else 'cleaned' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert2 = plain_speak_text(text)
    @py_assert4 = @py_assert2 == cleaned
    if not @py_assert4:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py5)s',), (@py_assert2, cleaned)) % {
            'py0': @pytest_ar._saferepr(plain_speak_text) if 'plain_speak_text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(plain_speak_text) else 'plain_speak_text',
            'py1': @pytest_ar._saferepr(text) if 'text' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(text) else 'text',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(cleaned) if 'cleaned' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cleaned) else 'cleaned' }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert2 = None
    @py_assert4 = None


def test_sanitize_for_speech_strips_www_urls():
    sanitize_for_speech = sanitize_for_speech
    import jarvis.tts_stream
    cleaned = sanitize_for_speech('See www.example.com for details.')
    @py_assert0 = 'www.'
    @py_assert2 = @py_assert0 not in cleaned
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py3)s',), (@py_assert0, cleaned)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(cleaned) if 'cleaned' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cleaned) else 'cleaned' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'details'
    @py_assert2 = @py_assert0 in cleaned
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, cleaned)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(cleaned) if 'cleaned' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cleaned) else 'cleaned' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_resolve_audio_rejects_unknown(audio_engine):
    pytest.raises(ValueError, match = 'Unsupported')
    audio_engine._resolve_audio('file.xyz')
    None(None, None)
    return None
    with None:
        if not None:
            pass

