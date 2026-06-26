# Source Generated with Decompyle++
# File: test_meme_ops.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for meme text overlay.'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
import pytest
from jarvis.meme_ops import compose_meme, list_memes, solid_background
meme_dir = (lambda tmp_path, monkeypatch: monkeypatch.setattr('jarvis.meme_ops.MEME_DIR', tmp_path)tmp_path)()

def test_overlay_meme_text(meme_dir):
    bg = meme_dir / 'bg.png'
    solid_background(400, 300).save(bg)
    out = compose_meme(bg, top = 'WHEN TESTS', bottom = 'PASS', output = meme_dir / 'meme.png')
    @py_assert2 = Path(out)
    @py_assert4 = @py_assert2.is_file
    @py_assert6 = @py_assert4()
    if not @py_assert6:
        @py_format8 = 'assert %(py7)s\n{%(py7)s = %(py5)s\n{%(py5)s = %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}.is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(Path) if 'Path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(Path) else 'Path',
            'py1': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert2 = Path(out)
    @py_assert4 = @py_assert2.stat
    @py_assert6 = @py_assert4()
    @py_assert8 = @py_assert6.st_size
    @py_assert11 = 1000
    @py_assert10 = @py_assert8 > @py_assert11
    if not @py_assert10:
        @py_format13 = @pytest_ar._call_reprcompare(('>',), (@py_assert10,), ('%(py9)s\n{%(py9)s = %(py7)s\n{%(py7)s = %(py5)s\n{%(py5)s = %(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n}.stat\n}()\n}.st_size\n} > %(py12)s',), (@py_assert8, @py_assert11)) % {
            'py0': @pytest_ar._saferepr(Path) if 'Path' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(Path) else 'Path',
            'py1': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8),
            'py12': @pytest_ar._saferepr(@py_assert11) }
        @py_format15 = 'assert %(py14)s' % {
            'py14': @py_format13 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format15))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None
    @py_assert11 = None


def test_list_memes_empty(meme_dir):
    @py_assert1 = list_memes()
    @py_assert4 = []
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(list_memes) if 'list_memes' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_memes) else 'list_memes',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None

