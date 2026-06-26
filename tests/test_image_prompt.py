# Source Generated with Decompyle++
# File: test_image_prompt.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Image prompt normalization and uncensored enhance defaults.'''
import builtins as @py_builtins

rewrite
from jarvis.modules.image import _llm_enhance_enabled, _prompt_model, normalize_image_prompt
_prompt_model = _prompt_model
normalize_image_prompt = normalize_image_prompt
import _pytest.assertion.rewrite, assertion

def test_normalize_strips_generate_image_prefix():
    @py_assert1 = 'Generate image: a red dragon'
    @py_assert3 = normalize_image_prompt(@py_assert1)
    @py_assert6 = 'a red dragon'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(normalize_image_prompt) if 'normalize_image_prompt' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_image_prompt) else 'normalize_image_prompt',
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


def test_normalize_strips_ai_generated_boilerplate():
    p = normalize_image_prompt('create an ai-generated image of a woman on a beach')
    @py_assert1 = []
    @py_assert2 = 'ai-generated'
    @py_assert6 = p.lower
    @py_assert8 = @py_assert6()
    @py_assert4 = @py_assert2 not in @py_assert8
    @py_assert0 = @py_assert4
    if not @py_assert4:
        @py_assert13 = 'woman'
        @py_assert17 = p.lower
        @py_assert19 = @py_assert17()
        @py_assert15 = @py_assert13 in @py_assert19
        @py_assert0 = @py_assert15
# WARNING: Decompyle incomplete


def test_normalize_colon_mangled_prompt():
    @py_assert1 = ': sunset over mountains'
    @py_assert3 = normalize_image_prompt(@py_assert1)
    @py_assert5 = @py_assert3.startswith
    @py_assert7 = 'sunset'
    @py_assert9 = @py_assert5(@py_assert7)
    if not @py_assert9:
        @py_format11 = 'assert %(py10)s\n{%(py10)s = %(py6)s\n{%(py6)s = %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}.startswith\n}(%(py8)s)\n}' % {
            'py0': @pytest_ar._saferepr(normalize_image_prompt) if 'normalize_image_prompt' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(normalize_image_prompt) else 'normalize_image_prompt',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None


def test_llm_enhance_on_in_uncensored_when_global_env_on(monkeypatch):
    monkeypatch.setattr('jarvis.config.UNCENSORED', True)
    monkeypatch.setenv('JARVIS_IMAGE_LLM_ENHANCE', '1')
    @py_assert1 = _llm_enhance_enabled()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(_llm_enhance_enabled) if '_llm_enhance_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_llm_enhance_enabled) else '_llm_enhance_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_llm_enhance_off_when_env_zero(monkeypatch):
    monkeypatch.setattr('jarvis.config.UNCENSORED', True)
    monkeypatch.setenv('JARVIS_IMAGE_LLM_ENHANCE', '0')
    @py_assert1 = _llm_enhance_enabled()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(_llm_enhance_enabled) if '_llm_enhance_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_llm_enhance_enabled) else '_llm_enhance_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_prompt_model_ignores_standard_qwen_override_in_uncensored(monkeypatch):
    monkeypatch.setattr('jarvis.config.is_uncensored', (lambda : True))
    monkeypatch.setenv('JARVIS_IMAGE_PROMPT_MODEL', 'qwen2.5:7b')
    monkeypatch.delenv('JARVIS_IMAGE_PROMPT_MODEL_UNCENSORED', raising = False)
    monkeypatch.setattr('jarvis.model_store.get_models', (lambda : {
'general': 'dolphin-mistral:latest' }))
    @py_assert1 = _prompt_model()
    @py_assert4 = 'dolphin-mistral:latest'
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(_prompt_model) if '_prompt_model' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_prompt_model) else '_prompt_model',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_prompt_model_uncensored_env_override(monkeypatch):
    monkeypatch.setattr('jarvis.config.is_uncensored', (lambda : True))
    monkeypatch.setenv('JARVIS_IMAGE_PROMPT_MODEL_UNCENSORED', 'custom-uncensored:latest')
    @py_assert1 = _prompt_model()
    @py_assert4 = 'custom-uncensored:latest'
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(_prompt_model) if '_prompt_model' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_prompt_model) else '_prompt_model',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None

