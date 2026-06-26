# Source Generated with Decompyle++
# File: test_resource_router.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Resource-aware routing tests.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from jarvis.resource_router import check_media_enqueue, preflight, record_media_outcome, routing_enabled, suggested_for_action

def test_routing_enabled_default():
    @py_assert1 = routing_enabled()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(routing_enabled) if 'routing_enabled' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(routing_enabled) else 'routing_enabled',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_preflight_low_vram(monkeypatch):
    monkeypatch.setattr('jarvis.resource_router.detect_gpu', (lambda : {
'vram_mb': 8176,
'ollama_using_gpu': True }))
    monkeypatch.setattr('jarvis.resource_router.is_low_vram', (lambda threshold_mb = (10240,): True))
    monkeypatch.setattr('jarvis.resource_router.ollama_loaded_models', (lambda : [
{
'name': 'qwen2.5:14b' }]))
    monkeypatch.setattr('jarvis.resource_router.snapshot', (lambda : {
'low_vram': True,
'vram_mb': 8176,
'ollama_models_loaded': 1,
'media_queue': {
'busy': False,
'pending': 0,
'queue_depth': 0 },
'ram_available_gb': 32 }))
    monkeypatch.setattr('jarvis.vram_guard.recommendations', (lambda : [
'Use 7B models']))
    pf = preflight('generate_video')
    @py_assert0 = pf['allow']
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
    @py_assert1 = pf['warnings']()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert0 = pf['adjustments']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None


def test_check_media_enqueue_blocked_when_strict(monkeypatch):
    monkeypatch.setattr('jarvis.resource_router.strict_queue', (lambda : True))
    monkeypatch.setattr('jarvis.resource_router.max_media_queue', (lambda : 2))
    monkeypatch.setattr('jarvis.resource_router.preflight', (lambda action: {
'allow': False,
'blocked': True,
'warnings': [
'Queue full'],
'adjustments': [],
'resources': {
'media_queue': {
'busy': True,
'pending': 2,
'queue_depth': 3,
'label': 'Video' },
'low_vram': True } }))
    check = check_media_enqueue('generate_image')
    @py_assert0 = check['allowed']
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
    @py_assert0 = check['blocked']
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


def test_record_and_suggest_settings(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.resource_router._SETTINGS_FILE', data_dir / 'resource_settings.json')
    monkeypatch.setattr('jarvis.resource_router.detect_gpu', (lambda : {
'vram_mb': 8176 }))
    monkeypatch.setattr('jarvis.resource_router.is_low_vram', (lambda threshold_mb = (10240,): True))
    record_media_outcome('generate_video', ok = True, method = 'ken_burns', detail = 'ok')
    last = suggested_for_action('generate_video')
    @py_assert1 = last.get
    @py_assert3 = 'method'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = 'ken_burns'
    @py_assert7 = @py_assert5 == @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('==',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} == %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(last) if 'last' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(last) else 'last',
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


def test_prepare_for_media_job_deferred_image(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.resource_router.routing_enabled', (lambda : True))
    prepare_for_media_job = prepare_for_media_job
    import jarvis.resource_router
    result = prepare_for_media_job('generate_image')
    @py_assert1 = result.get
    @py_assert3 = 'deferred'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
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
    @py_assert1 = result.get
    @py_assert3 = 'prepared'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is not @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is not',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is not %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
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


def test_prepare_for_media_job(data_dir, monkeypatch):
    monkeypatch.setattr('jarvis.resource_router.routing_enabled', (lambda : True))
    monkeypatch.setattr('jarvis.resource_router.is_low_vram', (lambda threshold_mb = (10240,): True))
    monkeypatch.setattr('jarvis.vram_guard.vram_guard_enabled', (lambda : True))
    monkeypatch.setattr('jarvis.vram_guard.prepare_for_comfyui', (lambda : {
'ok': True,
'unloaded_ollama': [
'm'] }))
    prepare_for_media_job = prepare_for_media_job
    import jarvis.resource_router
    result = prepare_for_media_job('generate_video')
    @py_assert1 = result.get
    @py_assert3 = 'prepared'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
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

