# Source Generated with Decompyle++
# File: test_image_uncensored.cpython-312-pytest-9.1.0.pyc (Python 3.12)

import builtins as @py_builtins

rewrite
from jarvis.modules import image
import _pytest.assertion.rewrite, assertion

def test_prompt_model_uses_general_in_uncensored(monkeypatch):
    monkeypatch.setenv('JARVIS_IMAGE_PROMPT_MODEL', '')
    monkeypatch.delenv('JARVIS_IMAGE_PROMPT_MODEL_UNCENSORED', raising = False)
    monkeypatch.setattr('jarvis.config.is_uncensored', (lambda : True))
    monkeypatch.setattr('jarvis.model_store.get_models', (lambda : {
'general': 'dolphin3:latest' }))
    @py_assert1 = img.prompt_model_name
    @py_assert3 = @py_assert1()
    @py_assert6 = 'dolphin3:latest'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.prompt_model_name\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(img) if 'img' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img) else 'img',
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


def test_prompt_model_standard_env_not_used_in_uncensored(monkeypatch):
    monkeypatch.setenv('JARVIS_IMAGE_PROMPT_MODEL', 'qwen2.5:7b')
    monkeypatch.setattr('jarvis.config.is_uncensored', (lambda : True))
    monkeypatch.setattr('jarvis.model_store.get_models', (lambda : {
'general': 'dolphin3:latest' }))
    @py_assert1 = img.prompt_model_name
    @py_assert3 = @py_assert1()
    @py_assert6 = 'dolphin3:latest'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.prompt_model_name\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(img) if 'img' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img) else 'img',
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


def test_prompt_model_env_override_standard_only(monkeypatch):
    monkeypatch.setenv('JARVIS_IMAGE_PROMPT_MODEL', 'custom:latest')
    monkeypatch.setattr('jarvis.config.is_uncensored', (lambda : False))
    @py_assert1 = img.prompt_model_name
    @py_assert3 = @py_assert1()
    @py_assert6 = 'custom:latest'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.prompt_model_name\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(img) if 'img' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img) else 'img',
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


def test_active_model_family_realvis(monkeypatch):
    monkeypatch.setattr('jarvis.comfyui_settings.resolve_checkpoint_name', (lambda : 'RealVisXL_V5.0_fp16.safetensors'))
    @py_assert1 = img._active_model_family
    @py_assert3 = @py_assert1()
    @py_assert6 = 'sdxl'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s._active_model_family\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(img) if 'img' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img) else 'img',
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


def test_active_model_family_realistic_vision(monkeypatch):
    monkeypatch.setattr('jarvis.comfyui_settings.resolve_checkpoint_name', (lambda : 'Realistic_Vision_V6.0_NV_B1_fp16.safetensors'))
    @py_assert1 = img._active_model_family
    @py_assert3 = @py_assert1()
    @py_assert6 = 'sd15'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s._active_model_family\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(img) if 'img' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img) else 'img',
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

