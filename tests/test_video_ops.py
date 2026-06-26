# Source Generated with Decompyle++
# File: test_video_ops.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for video_ops helpers.'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
from unittest.mock import patch
import pytest
from jarvis import video_ops
from jarvis.video_ops import probe, resolve_storyboard_image, resolve_storyboard_images, safe_video_name, trim

def test_safe_video_name():
    @py_assert1 = '../../evil.mp4'
    @py_assert3 = safe_video_name(@py_assert1)
    @py_assert6 = 'evil.mp4'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(safe_video_name) if 'safe_video_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(safe_video_name) else 'safe_video_name',
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
    @py_assert0 = '/'
    @py_assert4 = 'foo/bar clip.mp4'
    @py_assert6 = safe_video_name(@py_assert4)
    @py_assert2 = @py_assert0 not in @py_assert6
    if not @py_assert2:
        @py_format8 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py7)s\n{%(py7)s = %(py3)s(%(py5)s)\n}',), (@py_assert0, @py_assert6)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(safe_video_name) if 'safe_video_name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(safe_video_name) else 'safe_video_name',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None


def test_resolve_storyboard_image_memes_subdir(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    meme = data_dir / 'generated' / 'memes' / 'meme_preview_test.png'
    meme.parent.mkdir(parents = True)
    meme.write_bytes(b'\x89PNG\r\n\x1a\n')
    monkeypatch.setattr(video_ops, 'DATA_DIR', data_dir)
    @py_assert1 = 'memes/meme_preview_test.png'
    @py_assert3 = resolve_storyboard_image(@py_assert1)
    @py_assert5 = @py_assert3 == meme
    if not @py_assert5:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py6)s',), (@py_assert3, meme)) % {
            'py0': @pytest_ar._saferepr(resolve_storyboard_image) if 'resolve_storyboard_image' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_storyboard_image) else 'resolve_storyboard_image',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(meme) if 'meme' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(meme) else 'meme' }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = 'meme_preview_test.png'
    @py_assert3 = resolve_storyboard_image(@py_assert1)
    @py_assert5 = @py_assert3 == meme
    if not @py_assert5:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py6)s',), (@py_assert3, meme)) % {
            'py0': @pytest_ar._saferepr(resolve_storyboard_image) if 'resolve_storyboard_image' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_storyboard_image) else 'resolve_storyboard_image',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(meme) if 'meme' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(meme) else 'meme' }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert3 = str(meme)
    @py_assert5 = resolve_storyboard_image(@py_assert3)
    @py_assert7 = @py_assert5 == meme
    if not @py_assert7:
        @py_format9 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py4)s\n{%(py4)s = %(py1)s(%(py2)s)\n})\n} == %(py8)s',), (@py_assert5, meme)) % {
            'py0': @pytest_ar._saferepr(resolve_storyboard_image) if 'resolve_storyboard_image' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_storyboard_image) else 'resolve_storyboard_image',
            'py1': @pytest_ar._saferepr(str) if 'str' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(str) else 'str',
            'py2': @pytest_ar._saferepr(meme) if 'meme' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(meme) else 'meme',
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(meme) if 'meme' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(meme) else 'meme' }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_resolve_storyboard_image_data_prefix(tmp_path, monkeypatch):
    data_dir = tmp_path / 'data'
    img = data_dir / 'generated' / 'slide.png'
    img.parent.mkdir(parents = True)
    img.write_bytes(b'\x89PNG\r\n\x1a\n')
    monkeypatch.setattr(video_ops, 'DATA_DIR', data_dir)
    monkeypatch.setattr('jarvis.config.DATA_DIR', data_dir)
    monkeypatch.setattr('jarvis.config.PROJECT_ROOT', tmp_path)
    @py_assert1 = 'data/generated/slide.png'
    @py_assert3 = resolve_storyboard_image(@py_assert1)
    @py_assert5 = @py_assert3 == img
    if not @py_assert5:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py6)s',), (@py_assert3, img)) % {
            'py0': @pytest_ar._saferepr(resolve_storyboard_image) if 'resolve_storyboard_image' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_storyboard_image) else 'resolve_storyboard_image',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(img) if 'img' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(img) else 'img' }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = [
        'slide.png',
        'missing.png']
    @py_assert3 = resolve_storyboard_images(@py_assert1)
    @py_assert6 = [
        str(img)]
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(resolve_storyboard_images) if 'resolve_storyboard_images' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_storyboard_images) else 'resolve_storyboard_images',
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


def test_probe_missing_file():
    out = probe('/no/such/video.mp4')
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

test_probe_parses_json = (lambda mock_ffprobe, tmp_path: pass# WARNING: Decompyle incomplete
)()
test_trim_writes_output = (lambda mock_ffmpeg, tmp_path, monkeypatch: pass# WARNING: Decompyle incomplete
)()
