# Source Generated with Decompyle++
# File: test_voice_only.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for P1 #34 voice-only demo mode.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import os = import _pytest.assertion.rewrite, assertion

def test_strip_for_speech():
    strip_for_speech = strip_for_speech
    import jarvis.voice_only
    @py_assert1 = '**Hello** `world`'
    @py_assert3 = strip_for_speech(@py_assert1)
    @py_assert6 = 'Hello world'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(strip_for_speech) if 'strip_for_speech' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(strip_for_speech) else 'strip_for_speech',
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
    @py_assert1 = []
    @py_assert2 = 'code'
    @py_assert6 = 'Before ```python\nx=1\n``` after'
    @py_assert8 = strip_for_speech(@py_assert6)
    @py_assert10 = @py_assert8.lower
    @py_assert12 = @py_assert10()
    @py_assert4 = @py_assert2 in @py_assert12
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert17 = 'Before'
        @py_assert21 = 'Before ```python\nx=1\n``` after'
        @py_assert23 = strip_for_speech(@py_assert21)
        @py_assert19 = @py_assert17 in @py_assert23
        @py_assert0 = @py_assert19
# WARNING: Decompyle incomplete


def test_prepare_voice_only_env():
    prepare_voice_only_env = prepare_voice_only_env
    import jarvis.voice_only
    prepare_voice_only_env()
    @py_assert1 = os.environ
    @py_assert3 = @py_assert1.get
    @py_assert5 = 'JARVIS_VOICE_ONLY'
    @py_assert7 = @py_assert3(@py_assert5)
    @py_assert10 = '1'
    @py_assert9 = @py_assert7 == @py_assert10
    if not @py_assert9:
        @py_format12 = @pytest_ar._call_reprcompare(('==',), (@py_assert9,), ('%(py8)s\n{%(py8)s = %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.environ\n}.get\n}(%(py6)s)\n} == %(py11)s',), (@py_assert7, @py_assert10)) % {
            'py0': @pytest_ar._saferepr(os) if 'os' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(os) else 'os',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert10 = None
    @py_assert1 = os.environ
    @py_assert3 = @py_assert1.get
    @py_assert5 = 'JARVIS_WAKEWORD_TO_CHAT'
    @py_assert7 = @py_assert3(@py_assert5)
    @py_assert10 = '1'
    @py_assert9 = @py_assert7 == @py_assert10
    if not @py_assert9:
        @py_format12 = @pytest_ar._call_reprcompare(('==',), (@py_assert9,), ('%(py8)s\n{%(py8)s = %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.environ\n}.get\n}(%(py6)s)\n} == %(py11)s',), (@py_assert7, @py_assert10)) % {
            'py0': @pytest_ar._saferepr(os) if 'os' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(os) else 'os',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert10 = None
    @py_assert1 = os.environ
    @py_assert3 = @py_assert1.get
    @py_assert5 = 'JARVIS_WAKEWORD_SPEAK'
    @py_assert7 = @py_assert3(@py_assert5)
    @py_assert10 = '0'
    @py_assert9 = @py_assert7 == @py_assert10
    if not @py_assert9:
        @py_format12 = @pytest_ar._call_reprcompare(('==',), (@py_assert9,), ('%(py8)s\n{%(py8)s = %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.environ\n}.get\n}(%(py6)s)\n} == %(py11)s',), (@py_assert7, @py_assert10)) % {
            'py0': @pytest_ar._saferepr(os) if 'os' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(os) else 'os',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert10 = None


def test_voice_only_flag():
    voice_only_enabled = voice_only_enabled
    import jarvis.p1_flags
    @py_assert2 = voice_only_enabled()
    @py_assert5 = isinstance(@py_assert2, bool)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n}, %(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(isinstance) if 'isinstance' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(isinstance) else 'isinstance',
            'py1': @pytest_ar._saferepr(voice_only_enabled) if 'voice_only_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(voice_only_enabled) else 'voice_only_enabled',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py4': @pytest_ar._saferepr(bool) if 'bool' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(bool) else 'bool',
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert2 = None
    @py_assert5 = None


def test_run_once_mock(monkeypatch):
    pass
# WARNING: Decompyle incomplete

