# Source Generated with Decompyle++
# File: test_flytying_media.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Fly tying media and knowledge tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
from jarvis.flytying import media
import _pytest.assertion.rewrite, assertion
from jarvis.flytying.knowledge import context_for_main_chat, sync_status

def test_youtube_id_from_hero():
    ids = media.youtube_id_from_text('https://img.youtube.com/vi/mxC1XCc7XaM/maxresdefault.jpg')
    @py_assert2 = [
        'mxC1XCc7XaM']
    @py_assert1 = ids == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (ids, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(ids) if 'ids' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ids) else 'ids',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_recipe_videos_youtube():
    recipe = {
        'name': 'Test fly',
        'hero_image': 'https://img.youtube.com/vi/abcdEFG1234/maxresdefault.jpg' }
    vids = media.recipe_videos(recipe)
    @py_assert2 = len(vids)
    @py_assert5 = 1
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(vids) if 'vids' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(vids) else 'vids',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = vids[0]['provider']
    @py_assert3 = 'youtube'
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
    @py_assert0 = vids[0]['video_id']
    @py_assert3 = 'abcdEFG1234'
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


def test_recipe_videos_vimeo():
    recipe = {
        'name': 'Vimeo fly',
        'output': 'Watch at https://player.vimeo.com/video/12345' }
    vids = media.recipe_videos(recipe)
    @py_assert1 = vids()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_recipe_videos_flyfishfood():
    recipe = {
        'name': 'Foam minnow',
        'source_url': 'https://www.flyfishfood.com/blogs/streamer-tutorials/test' }
    vids = media.recipe_videos(recipe)
    @py_assert1 = vids()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_context_for_main_chat_skips_unrelated():
    (ctx, _) = context_for_main_chat('what is the weather tomorrow')
    @py_assert2 = ''
    @py_assert1 = ctx == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (ctx, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(ctx) if 'ctx' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ctx) else 'ctx',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_context_for_main_chat_fly_question(monkeypatch):
    monkeypatch.setattr('jarvis.flytying.bridge.search_recipes', (lambda q: [
{
'name': 'Adams',
'recipe_id': 'x' }]))
    monkeypatch.setattr('jarvis.flytying.bridge.get_recipe', (lambda name: {
'formatted': '**Adams** dry fly',
'recipe': { } }))
    monkeypatch.setattr('jarvis.flytying.bridge.available', (lambda : True))
    (ctx, _) = context_for_main_chat('how do I tie a dry fly parachute')
    @py_assert0 = 'Adams'
    @py_assert2 = @py_assert0 in ctx
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, ctx)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(ctx) if 'ctx' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ctx) else 'ctx' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None


def test_sync_status_shape():
    st = sync_status()
    @py_assert0 = 'gold_exists'
    @py_assert2 = @py_assert0 in st
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, st)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(st) if 'st' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(st) else 'st' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'docs_dir'
    @py_assert2 = @py_assert0 in st
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, st)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(st) if 'st' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(st) else 'st' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None

