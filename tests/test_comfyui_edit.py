# Source Generated with Decompyle++
# File: test_comfyui_edit.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Img2img edit workflow and full-frame inpaint redirect.'''
import builtins as @py_builtins

rewrite
from jarvis.comfyui_edit import build_edit_workflow
import _pytest.assertion.rewrite, assertion
from jarvis.image_post import inpaint_region

def test_build_edit_workflow_uses_vae_encode_not_inpaint():
    wf = build_edit_workflow('test.png', 'make the sky orange', denoise = 0.55)
    @py_assert0 = '11'
    @py_assert2 = @py_assert0 in wf
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, wf)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(wf) if 'wf' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(wf) else 'wf' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = wf['11']['class_type']
    @py_assert3 = 'VAEEncode'
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
    @py_assert0 = wf['3']['inputs']['denoise']
    @py_assert3 = 0.55
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
    @py_assert0 = 'Inpaint'
    @py_assert5 = str(wf)
    @py_assert2 = @py_assert0 not in @py_assert5
    if not @py_assert2:
        @py_format7 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py6)s\n{%(py6)s = %(py3)s(%(py4)s)\n}',), (@py_assert0, @py_assert5)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(str) if 'str' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(str) else 'str',
            'py4': @pytest_ar._saferepr(wf) if 'wf' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(wf) else 'wf',
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert5 = None


def test_inpaint_full_frame_redirects_to_edit(monkeypatch, tmp_path):
    pass
# WARNING: Decompyle incomplete

