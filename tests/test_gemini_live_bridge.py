# Source Generated with Decompyle++
# File: test_gemini_live_bridge.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Unit tests for Gemini Live bridge message normalization.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import json = import _pytest.assertion.rewrite, assertion
from jarvis.gemini_live_bridge import build_setup_message, client_audio_to_gemini, normalize_upstream_message

def test_build_setup_message_has_audio_and_voice():
    msg = build_setup_message()
    @py_assert0 = 'setup'
    @py_assert2 = @py_assert0 in msg
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, msg)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(msg) if 'msg' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(msg) else 'msg' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    setup = msg['setup']
    @py_assert0 = setup['generationConfig']['responseModalities']
    @py_assert3 = [
        'AUDIO']
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
    @py_assert0 = 'speechConfig'
    @py_assert3 = setup['generationConfig']
    @py_assert2 = @py_assert0 in @py_assert3
    if not @py_assert2:
        @py_format5 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py4)s',), (@py_assert0, @py_assert3)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        @py_format7 = 'assert %(py6)s' % {
            'py6': @py_format5 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert0 = setup['systemInstruction']['parts'][0]['text']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None


def test_client_audio_to_gemini_pcm():
    payload = client_audio_to_gemini('AAAA')
    @py_assert0 = payload['realtimeInput']['audio']['mimeType']
    @py_assert3 = 'audio/pcm;rate=16000'
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
    @py_assert0 = payload['realtimeInput']['audio']['data']
    @py_assert3 = 'AAAA'
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


def test_normalize_setup_complete():
    raw = json.dumps({
        'setupComplete': { } })
    events = normalize_upstream_message(raw)
    @py_assert0 = {
        'type': 'ready' }
    @py_assert2 = @py_assert0 in events
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, events)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(events) if 'events' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(events) else 'events' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_normalize_output_audio():
    raw = json.dumps({
        'serverContent': {
            'modelTurn': {
                'parts': [
                    {
                        'inlineData': {
                            'mimeType': 'audio/pcm;rate=24000',
                            'data': 'YmFzZTY0' } }] } } })
    events = normalize_upstream_message(raw)
# WARNING: Decompyle incomplete


def test_normalize_transcripts():
    raw = json.dumps({
        'inputTranscription': {
            'text': 'hello' },
        'serverContent': {
            'outputTranscription': {
                'text': 'hi there' } } })
    events = normalize_upstream_message(raw)
# WARNING: Decompyle incomplete


def test_server_playback_forwards_speaking_events():
    '''Bridge should emit speaking/playback_idle for server-side pw-play.'''
    normalize_upstream_message = normalize_upstream_message
    import jarvis.gemini_live_bridge
    audio_raw = json.dumps({
        'serverContent': {
            'modelTurn': {
                'parts': [
                    {
                        'inlineData': {
                            'mimeType': 'audio/pcm;rate=24000',
                            'data': 'YmFzZTY0' } }] } } })
    audio_events = normalize_upstream_message(audio_raw)
    @py_assert1 = audio_events()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    turn_raw = json.dumps({
        'serverContent': {
            'turnComplete': True } })
    turn_events = normalize_upstream_message(turn_raw)
    @py_assert0 = {
        'type': 'turn_complete' }
    @py_assert2 = @py_assert0 in turn_events
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, turn_events)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(turn_events) if 'turn_events' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(turn_events) else 'turn_events' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    interrupt_raw = json.dumps({
        'serverContent': {
            'interrupted': True } })
    interrupt_events = normalize_upstream_message(interrupt_raw)
    @py_assert0 = {
        'type': 'interrupted' }
    @py_assert2 = @py_assert0 in interrupt_events
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, interrupt_events)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(interrupt_events) if 'interrupt_events' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(interrupt_events) else 'interrupt_events' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None

