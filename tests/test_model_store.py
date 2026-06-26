# Source Generated with Decompyle++
# File: test_model_store.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Model settings — missing-model detection for Ollama pulls.'''
import builtins as @py_builtins

rewrite
from jarvis.model_store import get_missing_models, is_ollama_pullable
is_ollama_pullable = is_ollama_pullable
import _pytest.assertion.rewrite, assertion

def test_is_ollama_pullable_skips_image_backends():
    @py_assert1 = 'qwen2.5:7b'
    @py_assert3 = is_ollama_pullable(@py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(is_ollama_pullable) if 'is_ollama_pullable' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_ollama_pullable) else 'is_ollama_pullable',
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
    @py_assert1 = 'comfyui'
    @py_assert3 = is_ollama_pullable(@py_assert1)
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(is_ollama_pullable) if 'is_ollama_pullable' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_ollama_pullable) else 'is_ollama_pullable',
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
    @py_assert1 = ''
    @py_assert3 = is_ollama_pullable(@py_assert1)
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(is_ollama_pullable) if 'is_ollama_pullable' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_ollama_pullable) else 'is_ollama_pullable',
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


def test_get_missing_models_excludes_comfyui(monkeypatch):
    monkeypatch.setattr('jarvis.model_store.get_models', (lambda : {
'general': 'qwen2.5:7b',
'coder': 'qwen2.5-coder:14b',
'review': 'qwen2.5:7b',
'vision': 'moondream:latest',
'image': 'comfyui',
'embed': 'nomic-embed-text' }))
    monkeypatch.setattr('jarvis.model_store._installed', (lambda : [
'qwen2.5:7b',
'qwen2.5-coder:14b',
'moondream:latest',
'nomic-embed-text:latest']))
    @py_assert1 = get_missing_models()
    @py_assert4 = []
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(get_missing_models) if 'get_missing_models' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(get_missing_models) else 'get_missing_models',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_vision_fallback_when_mllama_unsupported(monkeypatch):
    get_models = get_models
    import jarvis.model_store
    monkeypatch.setattr('jarvis.model_store._installed', (lambda : [
'llama3.2-vision:11b',
'moondream:latest',
'llava:13b']))
    monkeypatch.setattr('jarvis.ollama_health.supports_mllama', (lambda : False))
    monkeypatch.setattr('jarvis.model_store._load_raw', (lambda : {
'standard': {
'vision': 'llama3.2-vision:11b' },
'uncensored': { } }))
    monkeypatch.setattr('jarvis.config.load_vision_quality', (lambda : 'custom'))
    @py_assert0 = get_models()['vision']
    @py_assert3 = 'llava:13b'
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


def test_supports_mllama_old_ollama(monkeypatch):
    oh = ollama_health
    import jarvis.ollama_health
    supports_mllama = supports_mllama
    import jarvis.ollama_health
    oh._MLLAMA_SUPPORT = None
    monkeypatch.setattr(oh, 'ollama_version', (lambda : (0, 30, 7)))
    @py_assert1 = True
    @py_assert3 = supports_mllama(refresh = @py_assert1)
    @py_assert6 = False
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(refresh=%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(supports_mllama) if 'supports_mllama' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(supports_mllama) else 'supports_mllama',
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
    oh._MLLAMA_SUPPORT = None
    monkeypatch.setattr(oh, 'ollama_version', (lambda : (0, 24, 0)))
    @py_assert1 = True
    @py_assert3 = supports_mllama(refresh = @py_assert1)
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(refresh=%(py2)s)\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(supports_mllama) if 'supports_mllama' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(supports_mllama) else 'supports_mllama',
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

