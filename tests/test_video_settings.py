# Source Generated with Decompyle++
# File: test_video_settings.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Video keyframe checkpoint settings (uncensored parity with image).'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
import pytest
from jarvis import video_settings as vs
video_settings = (lambda tmp_path, monkeypatch: cs = comfyui_settingsimport jarvismonkeypatch.setattr(vs, 'SETTINGS_FILE', tmp_path / 'video_settings.json')monkeypatch.setattr(vs, 'DATA_DIR', tmp_path)ckpt_dir = tmp_path / 'checkpoints'ckpt_dir.mkdir()monkeypatch.setattr(cs, 'CKPT_DIR', ckpt_dir)monkeypatch.setattr(vs, 'CKPT_DIR', ckpt_dir)(ckpt_dir / 'sd_xl_base_1.0.safetensors').write_bytes(b'x')(ckpt_dir / 'RealVisXL_V5.0_fp16.safetensors').write_bytes(b'x')vs)()

def test_resolve_keyframe_preset(video_settings):
    vs.save_keyframe_preset('quality')
    @py_assert1 = vs.resolve_keyframe_checkpoint
    @py_assert3 = @py_assert1()
    @py_assert6 = 'sd_xl_base_1.0.safetensors'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.resolve_keyframe_checkpoint\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(vs) if 'vs' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(vs) else 'vs',
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


def test_apply_uncensored_defaults(video_settings):
    vs.apply_uncensored_defaults()
    data = vs.get_settings()
    @py_assert0 = data['keyframe_checkpoint']
    @py_assert3 = 'RealVisXL_V5.0_fp16.safetensors'
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
    @py_assert0 = data['uncensored_auto_applied']
    @py_assert3 = True
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


def test_clear_uncensored_auto(video_settings):
    vs.apply_uncensored_defaults()
    vs.clear_uncensored_auto()
    data = vs.get_settings()
    @py_assert1 = data.get
    @py_assert3 = 'keyframe_checkpoint'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert1 = data.get
    @py_assert3 = 'uncensored_auto_applied'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(data) if 'data' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(data) else 'data',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None

