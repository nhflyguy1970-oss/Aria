# Source Generated with Decompyle++
# File: test_animatediff.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''AnimateDiff integration and Ken Burns fallback.'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
from unittest.mock import patch
import pytest
from jarvis import comfyui_animatediff as ad
from jarvis import video_settings as vs
video_env = (lambda tmp_path, monkeypatch: pass# WARNING: Decompyle incomplete
)()

def test_resolve_checkpoint_prefers_sd15(video_env):
    @py_assert1 = ad.resolve_checkpoint
    @py_assert3 = @py_assert1()
    @py_assert6 = 'Realistic_Vision_V6.0_NV_B1_fp16.safetensors'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.resolve_checkpoint\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(ad) if 'ad' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ad) else 'ad',
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


def test_animatediff_workflow_builds(video_env):
    wf = ad._animatediff_workflow('a cat walking', negative_prompt = 'blurry', width = 512, height = 512, frames = 16, fps = 8, checkpoint = 'Realistic_Vision_V6.0_NV_B1_fp16.safetensors', motion = 'mm_sd_v15_v2.ckpt')
    @py_assert2 = None
    @py_assert1 = wf is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (wf, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(wf) if 'wf' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(wf) else 'wf',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = wf['7']['inputs']['model']
    @py_assert3 = [
        '10',
        0]
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
    @py_assert0 = wf['10']['class_type']
    @py_assert3 = 'ADE_UseEvolvedSampling'
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
    @py_assert0 = wf['4']['inputs']['text']
    @py_assert3 = 'a cat walking'
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


def test_readiness_lists_missing_nodes(tmp_path, monkeypatch):
    monkeypatch.setattr(ad, 'COMFY_ROOT', tmp_path)
    monkeypatch.setattr(ad, 'custom_nodes_installed', (lambda : False))
    monkeypatch.setattr(ad, 'motion_module_path', (lambda : pass))
    monkeypatch.setattr(ad, 'resolve_checkpoint', (lambda : pass))
    monkeypatch.setattr(ad.comfyui, 'is_available', (lambda : False))
    status = ad.readiness()
    @py_assert0 = status['ready']
    @py_assert2 = not @py_assert0
    if not @py_assert2:
        @py_format3 = 'assert not %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = status['missing']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None


def test_auto_engine_skips_when_not_ready(video_env, monkeypatch):
    monkeypatch.setattr(vs, 'effective_engine', (lambda : 'auto'))
    monkeypatch.setattr(ad, 'is_ready', (lambda : False))
    @py_assert1 = vs.should_try_animatediff
    @py_assert3 = 'auto'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = False
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.should_try_animatediff\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(vs) if 'vs' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(vs) else 'vs',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert8 = None


def test_generate_motion_clip_fallback_on_animatediff_error(video_env, monkeypatch):
    cv = comfyui_video
    import jarvis
    monkeypatch.setattr(vs, 'effective_engine', (lambda : 'auto'))
    monkeypatch.setattr('jarvis.comfyui_animatediff.is_ready', (lambda : True))
    monkeypatch.setattr('jarvis.comfyui_animatediff.generate', (lambda : ('ERROR: GPU OOM', '')))
    monkeypatch.setattr(cv, 'generate_ken_burns_clip', (lambda : ('/tmp/out.mp4', '/tmp/key.png')))
    monkeypatch.setattr(vs, 'effective_duration', (lambda : 4))
    monkeypatch.setattr(vs, 'effective_fps', (lambda : 8))
    monkeypatch.setattr(vs, 'effective_size', (lambda : (768, 768)))
    monkeypatch.setattr(vs, 'effective_animatediff_frames', (lambda d, f: 16))
    monkeypatch.setattr(vs, 'effective_animatediff_size', (lambda : (512, 512)))
    (path, key, method) = cv.generate_motion_clip('test prompt')
    @py_assert2 = '/tmp/out.mp4'
    @py_assert1 = path == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (path, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(path) if 'path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(path) else 'path',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert2 = 'ken_burns'
    @py_assert1 = method == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (method, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(method) if 'method' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(method) else 'method',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert1 = cv.last_fallback_reason
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.last_fallback_reason\n}()\n}' % {
            'py0': @pytest_ar._saferepr(cv) if 'cv' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cv) else 'cv',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None

