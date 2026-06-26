# Source Generated with Decompyle++
# File: test_vision_resolve.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for vision image path resolution.'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
from jarvis.modules.vision import _resolve_image_path
from PIL import Image

def test_resolve_upload_by_basename(data_dir = None, monkeypatch = None):
    monkeypatch.setattr('jarvis.modules.vision.DATA_DIR', data_dir)
    monkeypatch.setattr('jarvis.fs.DATA_DIR', data_dir)
    img = data_dir / 'uploads' / 'clip.png'
    Image.new('RGB', (4, 4), 'blue').save(img)
    resolved = _resolve_image_path('clip.png')
    @py_assert3 = img.resolve
    @py_assert5 = @py_assert3()
    @py_assert1 = resolved == @py_assert5
    if not @py_assert1:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py6)s\n{%(py6)s = %(py4)s\n{%(py4)s = %(py2)s.resolve\n}()\n}',), (resolved, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(resolved) if 'resolved' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolved) else 'resolved',
            'py2': @pytest_ar._saferepr(img) if 'img' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img) else 'img',
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_resolve_distinct_upload_paths(data_dir = None, monkeypatch = None):
    monkeypatch.setattr('jarvis.modules.vision.DATA_DIR', data_dir)
    monkeypatch.setattr('jarvis.fs.DATA_DIR', data_dir)
    img1 = data_dir / 'uploads' / 'shot.png'
    img2 = data_dir / 'uploads' / 'shot_2.png'
    Image.new('RGB', (4, 4), 'red').save(img1)
    Image.new('RGB', (4, 4), 'blue').save(img2)
    @py_assert3 = str(img1)
    @py_assert5 = _resolve_image_path(@py_assert3)
    @py_assert9 = img1.resolve
    @py_assert11 = @py_assert9()
    @py_assert7 = @py_assert5 == @py_assert11
    if not @py_assert7:
        @py_format13 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py4)s\n{%(py4)s = %(py1)s(%(py2)s)\n})\n} == %(py12)s\n{%(py12)s = %(py10)s\n{%(py10)s = %(py8)s.resolve\n}()\n}',), (@py_assert5, @py_assert11)) % {
            'py0': @pytest_ar._saferepr(_resolve_image_path) if '_resolve_image_path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_resolve_image_path) else '_resolve_image_path',
            'py1': @pytest_ar._saferepr(str) if 'str' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(str) else 'str',
            'py2': @pytest_ar._saferepr(img1) if 'img1' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img1) else 'img1',
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(img1) if 'img1' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img1) else 'img1',
            'py10': @pytest_ar._saferepr(@py_assert9),
            'py12': @pytest_ar._saferepr(@py_assert11) }
        @py_format15 = 'assert %(py14)s' % {
            'py14': @py_format13 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format15))
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert11 = None
    @py_assert3 = str(img2)
    @py_assert5 = _resolve_image_path(@py_assert3)
    @py_assert9 = img2.resolve
    @py_assert11 = @py_assert9()
    @py_assert7 = @py_assert5 == @py_assert11
    if not @py_assert7:
        @py_format13 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py4)s\n{%(py4)s = %(py1)s(%(py2)s)\n})\n} == %(py12)s\n{%(py12)s = %(py10)s\n{%(py10)s = %(py8)s.resolve\n}()\n}',), (@py_assert5, @py_assert11)) % {
            'py0': @pytest_ar._saferepr(_resolve_image_path) if '_resolve_image_path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_resolve_image_path) else '_resolve_image_path',
            'py1': @pytest_ar._saferepr(str) if 'str' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(str) else 'str',
            'py2': @pytest_ar._saferepr(img2) if 'img2' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img2) else 'img2',
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(img2) if 'img2' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img2) else 'img2',
            'py10': @pytest_ar._saferepr(@py_assert9),
            'py12': @pytest_ar._saferepr(@py_assert11) }
        @py_format15 = 'assert %(py14)s' % {
            'py14': @py_format13 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format15))
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert11 = None
    @py_assert3 = str(img1)
    @py_assert5 = _resolve_image_path(@py_assert3)
    @py_assert11 = str(img2)
    @py_assert13 = _resolve_image_path(@py_assert11)
    @py_assert7 = @py_assert5 != @py_assert13
    if not @py_assert7:
        @py_format15 = @pytest_ar._call_reprcompare(('!=',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py4)s\n{%(py4)s = %(py1)s(%(py2)s)\n})\n} != %(py14)s\n{%(py14)s = %(py8)s(%(py12)s\n{%(py12)s = %(py9)s(%(py10)s)\n})\n}',), (@py_assert5, @py_assert13)) % {
            'py0': @pytest_ar._saferepr(_resolve_image_path) if '_resolve_image_path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_resolve_image_path) else '_resolve_image_path',
            'py1': @pytest_ar._saferepr(str) if 'str' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(str) else 'str',
            'py2': @pytest_ar._saferepr(img1) if 'img1' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img1) else 'img1',
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(_resolve_image_path) if '_resolve_image_path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(_resolve_image_path) else '_resolve_image_path',
            'py9': @pytest_ar._saferepr(str) if 'str' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(str) else 'str',
            'py10': @pytest_ar._saferepr(img2) if 'img2' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img2) else 'img2',
            'py12': @pytest_ar._saferepr(@py_assert11),
            'py14': @pytest_ar._saferepr(@py_assert13) }
        @py_format17 = 'assert %(py16)s' % {
            'py16': @py_format15 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format17))
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert11 = None
    @py_assert13 = None

