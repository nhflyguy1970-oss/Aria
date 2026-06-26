# Source Generated with Decompyle++
# File: test_hardware_tune.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for 8GB hardware tuning helpers.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
from jarvis.hardware_tune import ENV_8GB_DEFAULTS, patch_env_file
patch_env_file = patch_env_file
import _pytest.assertion.rewrite, assertion

def test_patch_env_file_updates_and_appends(tmp_path):
    env = tmp_path / 'jarvis.env'
    env.write_text('export JARVIS_WHISPER_MODEL="base"\n', encoding = 'utf-8')
    changed = patch_env_file(env, {
        'JARVIS_WHISPER_MODEL': 'small',
        'JARVIS_VRAM_GUARD': '1' })
    text = env.read_text(encoding = 'utf-8')
    @py_assert0 = 'JARVIS_WHISPER_MODEL="small"'
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
    @py_assert0 = 'JARVIS_VRAM_GUARD="1"'
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
    @py_assert0 = 'JARVIS_WHISPER_MODEL'
    @py_assert2 = @py_assert0 in changed
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, changed)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(changed) if 'changed' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(changed) else 'changed' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_env_defaults_keys():
    @py_assert0 = ENV_8GB_DEFAULTS['JARVIS_WHISPER_MODEL']
    @py_assert3 = 'small'
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
    @py_assert0 = ENV_8GB_DEFAULTS['JARVIS_VRAM_GUARD']
    @py_assert3 = '1'
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

