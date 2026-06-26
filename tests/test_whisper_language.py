# Source Generated with Decompyle++
# File: test_whisper_language.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Whisper language auto-detect.'''
import builtins as @py_builtins

rewrite
from jarvis.audio_whisper import _effective_language
import _pytest.assertion.rewrite, assertion

def test_effective_language_auto(monkeypatch):
    monkeypatch.setenv('JARVIS_WHISPER_LANGUAGE', 'auto')
    monkeypatch.setattr('jarvis.audio_whisper.saved_whisper_language', (lambda : 'auto'))
    @py_assert1 = None
    @py_assert3 = _effective_language(@py_assert1)
    @py_assert6 = None
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(_effective_language) if '_effective_language' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_effective_language) else '_effective_language',
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
    @py_assert1 = 'auto'
    @py_assert3 = _effective_language(@py_assert1)
    @py_assert6 = None
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(_effective_language) if '_effective_language' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_effective_language) else '_effective_language',
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


def test_effective_language_explicit():
    @py_assert1 = 'es'
    @py_assert3 = _effective_language(@py_assert1)
    @py_assert6 = 'es'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(_effective_language) if '_effective_language' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_effective_language) else '_effective_language',
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

