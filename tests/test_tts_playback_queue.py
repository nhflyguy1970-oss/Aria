# Source Generated with Decompyle++
# File: test_tts_playback_queue.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''TTS playback queue tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
from unittest.mock import patch
import _pytest.assertion.rewrite, assertion

def test_enqueue_and_wait_idle(tmp_path):
    clear_tts_queue = clear_tts_queue
    enqueue_play = enqueue_play
    wait_tts_idle = wait_tts_idle
    import jarvis.tts_playback_queue
    wav = tmp_path / 'a.wav'
    wav.write_bytes(b'RIFF')
    clear_tts_queue()
    patch('jarvis.tts_playback_queue.play_file', return_value = str(wav), create = True)
    play = patch('jarvis.audio_device.play_file', return_value = str(wav))
    enqueue_play(wav)
    @py_assert1 = 2
    @py_assert3 = wait_tts_idle(timeout = @py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(timeout=%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(wait_tts_idle) if 'wait_tts_idle' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(wait_tts_idle) else 'wait_tts_idle',
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
    play.assert_called_once_with(str(wav))
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


def test_clear_drops_pending(tmp_path):
    clear_tts_queue = clear_tts_queue
    enqueue_play = enqueue_play
    tts_queue_busy = tts_queue_busy
    import jarvis.tts_playback_queue
    a = tmp_path / 'a.wav'
    b = tmp_path / 'b.wav'
    a.write_bytes(b'RIFF')
    b.write_bytes(b'RIFF')
    clear_tts_queue()
    patch('jarvis.audio_device.play_file', side_effect = (lambda p: p))
    enqueue_play(a)
    enqueue_play(b)
    None(None, None)
    clear_tts_queue()
    @py_assert1 = tts_queue_busy()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(tts_queue_busy) if 'tts_queue_busy' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(tts_queue_busy) else 'tts_queue_busy',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    return None
    with None:
        if not None:
            pass
    continue

