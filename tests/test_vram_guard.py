# Source Generated with Decompyle++
# File: test_vram_guard.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for VRAM guard coordination.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
from unittest.mock import patch
import _pytest.assertion.rewrite, assertion
from jarvis.gpu import _parse_vram_used_mb
from jarvis.vram_guard import free_vram, prepare_for_comfyui, recommendations, vram_guard_enabled

def test_parse_rocm_total_used_vram():
    out = 'GPU[0]\t\t: VRAM Total Used Memory (B): 1208811520'
    @py_assert2 = _parse_vram_used_mb(out)
    @py_assert5 = 1153
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(_parse_vram_used_mb) if '_parse_vram_used_mb' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_parse_vram_used_mb) else '_parse_vram_used_mb',
            'py1': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None


def test_vram_guard_enabled_default():
    @py_assert1 = vram_guard_enabled()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(vram_guard_enabled) if 'vram_guard_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(vram_guard_enabled) else 'vram_guard_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None

test_prepare_for_comfyui = (lambda mock_free, mock_release, mock_unload: out = prepare_for_comfyui(required_mb = 7800)@py_assert0 = out['ok']@py_assert3 = True@py_assert2 = @py_assert0 is @py_assert3if not @py_assert2:
@py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py4': @pytest_ar._saferepr(@py_assert3) }@py_format7 = 'assert %(py6)s' % {
'py6': @py_format5 }raise AssertionError(@pytest_ar._format_explanation(@py_format7))@py_assert0 = None@py_assert2 = None@py_assert3 = Nonemock_unload.assert_called_once()mock_release.assert_called_once()@py_assert0 = out['free_vram_mb']@py_assert3 = 9000@py_assert2 = @py_assert0 == @py_assert3if not @py_assert2:
@py_format5 = @pytest_ar._call_reprcompare(('==',), (@py_assert2,), ('%(py1)s == %(py4)s',), (@py_assert0, @py_assert3)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py4': @pytest_ar._saferepr(@py_assert3) }@py_format7 = 'assert %(py6)s' % {
'py6': @py_format5 }raise AssertionError(@pytest_ar._format_explanation(@py_format7))@py_assert0 = None@py_assert2 = None@py_assert3 = None)()()()
test_ensure_vram_for_comfyui_insufficient = (lambda mock_prep, monkeypatch: ensure_vram_for_comfyui = ensure_vram_for_comfyuiimport jarvis.vram_guardmonkeypatch.setattr('jarvis.vram_guard._comfyui_warm', (lambda : False))
    monkeypatch.setattr('jarvis.vram_guard.required_vram_for_checkpoint', (lambda ck, warm = (None, False): if not warm:
7800))
    monkeypatch.setattr('jarvis.comfyui_settings.checkpoint_label', (lambda : 'Flux Schnell'))
    out = ensure_vram_for_comfyui('flux')
    @py_assert0 = out['ok']
    @py_assert3 = False
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
    @py_assert0 = 'Not enough VRAM'
    @py_assert3 = out['error']
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
)()
test_ensure_vram_for_comfyui_ok = (lambda mock_prep, monkeypatch: ensure_vram_for_comfyui = ensure_vram_for_comfyuiimport jarvis.vram_guardmonkeypatch.setattr('jarvis.vram_guard._comfyui_warm', (lambda : False))
    monkeypatch.setattr('jarvis.vram_guard.required_vram_for_checkpoint', (lambda ck, warm = (None, False): if not warm:
7800))
    out = ensure_vram_for_comfyui('flux')
    @py_assert0 = out['ok']
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
)()
test_ensure_vram_for_comfyui_warm_comfyui = (lambda mock_prep, monkeypatch: ensure_vram_for_comfyui = ensure_vram_for_comfyuiimport jarvis.vram_guardmonkeypatch.setattr('jarvis.vram_guard._comfyui_warm', (lambda : True))
    monkeypatch.setattr('jarvis.vram_guard.required_vram_for_checkpoint', (lambda ck, warm = (None, False): if not warm:
7800))
    out = ensure_vram_for_comfyui('flux')
    @py_assert0 = out['ok']
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
    @py_assert0 = out['comfyui_warm']
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
)()
test_recommendations_low_vram = (lambda mock_low, mock_gpu: tips = recommendations()@py_assert1 = tips()@py_assert3 = any(@py_assert1)if not @py_assert3:
@py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
'py2': @pytest_ar._saferepr(@py_assert1),
'py4': @pytest_ar._saferepr(@py_assert3) }raise AssertionError(@pytest_ar._format_explanation(@py_format5))@py_assert1 = None@py_assert3 = None)()()
test_free_vram = (lambda mock_gpu, mock_release, mock_unload: out = free_vram()@py_assert0 = out['ok']@py_assert3 = True@py_assert2 = @py_assert0 is @py_assert3if not @py_assert2:
@py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py4': @pytest_ar._saferepr(@py_assert3) }@py_format7 = 'assert %(py6)s' % {
'py6': @py_format5 }raise AssertionError(@pytest_ar._format_explanation(@py_format7))@py_assert0 = None@py_assert2 = None@py_assert3 = None@py_assert0 = out['released_torch']@py_assert3 = True@py_assert2 = @py_assert0 is @py_assert3if not @py_assert2:
@py_format5 = @pytest_ar._call_reprcompare(('is',), (@py_assert2,), ('%(py1)s is %(py4)s',), (@py_assert0, @py_assert3)) % {
'py1': @pytest_ar._saferepr(@py_assert0),
'py4': @pytest_ar._saferepr(@py_assert3) }@py_format7 = 'assert %(py6)s' % {
'py6': @py_format5 }raise AssertionError(@pytest_ar._format_explanation(@py_format7))@py_assert0 = None@py_assert2 = None@py_assert3 = None)()()()
