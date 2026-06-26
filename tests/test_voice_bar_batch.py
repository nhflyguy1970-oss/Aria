# Source Generated with Decompyle++
# File: test_voice_bar_batch.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for voice bar batch #26 #27 #30 #84.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
from unittest.mock import patch
import _pytest.assertion.rewrite, assertion

def test_duplex_status_modes():
    duplex_status = duplex_status
    import jarvis.voice_duplex
    patch('jarvis.voice_duplex.duplex_mode', return_value = 'half')
    st = duplex_status()
    None(None, None)
# WARNING: Decompyle incomplete


def test_tts_stream_chunks():
    split_speak_chunks = split_speak_chunks
    import jarvis.tts_stream
    text = 'Hello world. This is ARIA. More text here. More text here. More text here. More text here. More text here. '
    chunks = split_speak_chunks(text, max_chars = 40)
    if not chunks:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(chunks) if 'chunks' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(chunks) else 'chunks' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    @py_assert1 = chunks()
    @py_assert3 = all(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(all) if 'all' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(all) else 'all',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_ptt_stops_playback_before_record(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_cloud_live_openai_session_mock():
    start_live_session = start_live_session
    import jarvis.cloud_live_voice
    fake = {
        'ok': True,
        'provider': 'openai_realtime',
        'client_secret': 'ek_test',
        'model': 'gpt-4o-realtime-preview' }
    patch('jarvis.cloud_live_voice.cloud_live_status', return_value = {
        'available': True,
        'provider': 'openai_realtime',
        'openai_key': True })
    patch('jarvis.cloud_live_voice._create_openai_realtime_session', return_value = fake)
    out = start_live_session()
    None(None, None)
    None(None, None)
# WARNING: Decompyle incomplete


def test_cloud_live_openai_unavailable_without_gemini():
    cloud_live_status = cloud_live_status
    import jarvis.cloud_live_voice
    patch.dict('os.environ', {
        'OPENAI_API_KEY': 'sk-test',
        'GEMINI_API_KEY': '' }, clear = False)
    patch('jarvis.p4_flags.cloud_live_voice_enabled', return_value = True)
    st = cloud_live_status()
    None(None, None)
    None(None, None)
# WARNING: Decompyle incomplete

