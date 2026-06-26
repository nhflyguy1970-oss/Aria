# Source Generated with Decompyle++
# File: test_vision_features.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for extended vision features.'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
import pytest
from jarvis.router import route
from jarvis.session import SessionContext
from jarvis.vision_media import REGION_PRESETS, build_visual_diff, parse_region, parse_video_second
from PIL import Image
session = (lambda : SessionContext())()

def _png(path = None, color = None):
    path.parent.mkdir(parents = True, exist_ok = True)
    Image.new('RGB', (32, 32), color).save(path)


def test_structured_ocr_route(session):
    att = {
        'path': '/tmp/x.png',
        'kind': 'image' }
    intent = route('Structured OCR — extract tables as markdown', session, att)
    @py_assert0 = intent['action']
    @py_assert3 = 'ocr_structured_image'
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


def test_image_to_code_route(session):
    att = {
        'path': '/tmp/ui.png',
        'kind': 'image' }
    intent = route('Convert this UI screenshot to HTML', session, att)
    @py_assert0 = intent['action']
    @py_assert3 = 'image_to_code'
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


def test_region_route(session):
    att = {
        'path': '/tmp/x.png',
        'kind': 'image' }
    intent = route("What's in the top-left region?", session, att)
    @py_assert0 = intent['action']
    @py_assert3 = 'analyze_region'
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
    @py_assert0 = intent['params']['crop']
    @py_assert3 = REGION_PRESETS['top left']
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


def test_remember_image_route(session):
    att = {
        'path': '/tmp/x.png',
        'kind': 'image' }
    intent = route('Remember what this screenshot says', session, att)
    @py_assert0 = intent['action']
    @py_assert3 = 'remember_image'
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


def test_batch_vision_route(session):
    intent = route('analyze all images in data/uploads', session)
    @py_assert0 = intent['action']
    @py_assert3 = 'batch_vision'
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


def test_parse_video_second():
    @py_assert1 = 'analyze at 1:30'
    @py_assert3 = parse_video_second(@py_assert1)
    @py_assert6 = 90
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(parse_video_second) if 'parse_video_second' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_video_second) else 'parse_video_second',
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
    @py_assert1 = ''
    @py_assert3 = 12.5
    @py_assert5 = parse_video_second(@py_assert1, explicit = @py_assert3)
    @py_assert8 = 12.5
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py0)s(%(py2)s, explicit=%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(parse_video_second) if 'parse_video_second' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_video_second) else 'parse_video_second',
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


def test_parse_region_bbox():
    crop = parse_region('check region 10,20,30,40')
    @py_assert2 = {
        'x': 0.1,
        'y': 0.2,
        'w': 0.3,
        'h': 0.4 }
    @py_assert1 = crop == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (crop, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(crop) if 'crop' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(crop) else 'crop',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_build_visual_diff(data_dir):
    a = data_dir / 'uploads' / 'da.png'
    b = data_dir / 'uploads' / 'db.png'
    _png(a, 'red')
    _png(b, 'blue')
    out = build_visual_diff(a, b, data_dir / 'uploads')
    @py_assert2 = None
    @py_assert1 = out is not @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is not',), (@py_assert1,), ('%(py0)s is not %(py3)s',), (out, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert1 = out.exists
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.exists\n}()\n}' % {
            'py0': @pytest_ar._saferepr(out) if 'out' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(out) else 'out',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_vision_model_for_task(monkeypatch):
    llm = llm
    import jarvis
    monkeypatch.setattr(llm, 'model_for', (lambda role: 'moondream:latest'))
    monkeypatch.setattr('jarvis.config.load_vision_quality', (lambda : 'fast'))
    @py_assert1 = llm.vision_model_for_task
    @py_assert3 = 'describe'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'moondream:latest'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.vision_model_for_task\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(llm) if 'llm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(llm) else 'llm',
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
    @py_assert1 = llm.vision_model_for_task
    @py_assert3 = 'ocr'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'moondream:latest'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.vision_model_for_task\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(llm) if 'llm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(llm) else 'llm',
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
    monkeypatch.setattr('jarvis.config.load_vision_quality', (lambda : 'quality'))
    monkeypatch.setattr('jarvis.model_store._installed', (lambda : [
'llama3.2-vision:11b',
'moondream:latest']))
    monkeypatch.setattr('jarvis.gpu.is_low_vram', (lambda : True))
    monkeypatch.setattr('jarvis.ollama_health.supports_mllama', (lambda refresh = (False,): True))
    @py_assert0 = 'llama3.2-vision'
    @py_assert4 = llm.vision_model_for_task
    @py_assert6 = 'ocr'
    @py_assert8 = @py_assert4(@py_assert6)
    @py_assert2 = @py_assert0 in @py_assert8
    if not @py_assert2:
        @py_format10 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py9)s\n{%(py9)s = %(py5)s\n{%(py5)s = %(py3)s.vision_model_for_task\n}(%(py7)s)\n}',), (@py_assert0, @py_assert8)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(llm) if 'llm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(llm) else 'llm',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8) }
        @py_format12 = 'assert %(py11)s' % {
            'py11': @py_format10 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format12))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    monkeypatch.setattr('jarvis.config.load_vision_quality', (lambda : 'custom'))
    monkeypatch.setattr('jarvis.model_store._installed', (lambda : [
'moondream:latest',
'llava:13b']))
    @py_assert1 = llm.vision_model_for_task
    @py_assert3 = 'describe'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'moondream:latest'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.vision_model_for_task\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(llm) if 'llm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(llm) else 'llm',
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
    @py_assert1 = llm.vision_model_for_task
    @py_assert3 = 'identify'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'llava:13b'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.vision_model_for_task\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(llm) if 'llm' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(llm) else 'llm',
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


def test_vision_task_for_species_question():
    build_vision_prompt = build_vision_prompt
    vision_task_for_question = vision_task_for_question
    import jarvis.vision_media
    q = 'what species is this'
    @py_assert2 = vision_task_for_question(q)
    @py_assert5 = 'identify'
    @py_assert4 = @py_assert2 == @py_assert5
    if not @py_assert4:
        @py_format7 = @pytest_ar._call_reprcompare(('==',), (@py_assert4,), ('%(py3)s\n{%(py3)s = %(py0)s(%(py1)s)\n} == %(py6)s',), (@py_assert2, @py_assert5)) % {
            'py0': @pytest_ar._saferepr(vision_task_for_question) if 'vision_task_for_question' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(vision_task_for_question) else 'vision_task_for_question',
            'py1': @pytest_ar._saferepr(q) if 'q' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(q) else 'q',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        @py_format9 = 'assert %(py8)s' % {
            'py8': @py_format7 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format9))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert5 = None
    @py_assert0 = 'scientific name'
    @py_assert5 = 'identify'
    @py_assert7 = build_vision_prompt(q, @py_assert5)
    @py_assert9 = @py_assert7.lower
    @py_assert11 = @py_assert9()
    @py_assert2 = @py_assert0 in @py_assert11
    if not @py_assert2:
        @py_format13 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py12)s\n{%(py12)s = %(py10)s\n{%(py10)s = %(py8)s\n{%(py8)s = %(py3)s(%(py4)s, %(py6)s)\n}.lower\n}()\n}',), (@py_assert0, @py_assert11)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(build_vision_prompt) if 'build_vision_prompt' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(build_vision_prompt) else 'build_vision_prompt',
            'py4': @pytest_ar._saferepr(q) if 'q' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(q) else 'q',
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9),
            'py12': @pytest_ar._saferepr(@py_assert11) }
        @py_format15 = 'assert %(py14)s' % {
            'py14': @py_format13 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format15))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None
    @py_assert11 = None

