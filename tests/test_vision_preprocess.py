# Source Generated with Decompyle++
# File: test_vision_preprocess.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for vision image preprocessing.'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
from jarvis.modules.vision import MAX_VISION_PIXELS, _prepare_image_b64
from PIL import Image

def test_large_image_is_downscaled(tmp_path = None):
    img = tmp_path / 'big.png'
    Image.new('RGB', (4000, 2000), 'blue').save(img)
    cache = { }
    _prepare_image_b64(img, cache)
    @py_assert2 = len(cache)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(cache) if 'cache' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(cache) else 'cache',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    import base64
    import io
    raw = base64.b64decode(next(iter(cache.values())))
    out = Image.open(io.BytesIO(raw))
    @py_assert2 = out.size
    @py_assert4 = max(@py_assert2)
    @py_assert6 = @py_assert4 <= MAX_VISION_PIXELS
    if not @py_assert6:
        @py_format8 = @pytest_ar._call_reprcompare(('<=',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s.size\n})\n} <= %(py7)s',), (@py_assert4, MAX_VISION_PIXELS)) % {
            'py0': @pytest_ar._saferepr(max) if 'max' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(max) else 'max',
            'py1': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(MAX_VISION_PIXELS) if 'MAX_VISION_PIXELS' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(MAX_VISION_PIXELS) else 'MAX_VISION_PIXELS' }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    None(None, None)
    return None
    with None:
        if not None:
            pass

