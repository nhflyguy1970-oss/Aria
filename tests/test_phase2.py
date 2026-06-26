# Source Generated with Decompyle++
# File: test_phase2.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Phase 2 — presence & abilities tests.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion

def test_jarvis_mcp_briefing(monkeypatch, assistant):
    clear_assistant = clear_assistant
    set_assistant = set_assistant
    import jarvis.assistant_instance
    handle_jarvis_mcp_tool = handle_jarvis_mcp_tool
    import jarvis.jarvis_mcp
    clear_assistant()
    set_assistant(assistant)
    monkeypatch.setattr(assistant, '_morning_briefing', (lambda params, msg: {
'ok': True,
'message': 'Good morning',
'module': 'briefing' }))
    out = handle_jarvis_mcp_tool('jarvis_briefing', { })
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
    @py_assert0 = 'Good morning'
    @py_assert3 = out['message']
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


def test_jarvis_mcp_unknown_tool():
    handle_jarvis_mcp_tool = handle_jarvis_mcp_tool
    import jarvis.jarvis_mcp
    out = handle_jarvis_mcp_tool('jarvis_not_real', { })
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


def test_storyboard_no_images():
    storyboard_ken_burns = storyboard_ken_burns
    import jarvis.video_ops
    @py_assert1 = []
    @py_assert3 = storyboard_ken_burns(@py_assert1)
    @py_assert5 = @py_assert3.startswith
    @py_assert7 = 'ERROR:'
    @py_assert9 = @py_assert5(@py_assert7)
    if not @py_assert9:
        @py_format11 = 'assert %(py10)s\n{%(py10)s = %(py6)s\n{%(py6)s = %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}.startswith\n}(%(py8)s)\n}' % {
            'py0': @pytest_ar._saferepr(storyboard_ken_burns) if 'storyboard_ken_burns' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(storyboard_ken_burns) else 'storyboard_ken_burns',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    @py_assert9 = None


def test_storyboard_single_image(monkeypatch, tmp_path):
    pass
# WARNING: Decompyle incomplete


def test_proactive_scheduler_start_stop(monkeypatch):
    monkeypatch.setenv('JARVIS_SCHEDULER', '1')
    start = start
    stop = stop
    import jarvis.proactive_scheduler
    start()
    stop()


def test_proactive_scheduler_disabled(monkeypatch):
    monkeypatch.setenv('JARVIS_SCHEDULER', '0')
    sched = proactive_scheduler
    import jarvis
    sched._thread = None
    sched.start()
    @py_assert1 = sched._thread
    @py_assert4 = None
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s._thread\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(sched) if 'sched' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sched) else 'sched',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_reflection_day_module_variable():
    datetime = datetime
    import datetime
    sched = proactive_scheduler
    import jarvis
    @py_assert1 = sched._last_reflection_day
    @py_assert4 = ''
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s._last_reflection_day\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(sched) if 'sched' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(sched) else 'sched',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    sched._maybe_reflection(datetime.now())


def test_api_video_storyboard_bad_paths(chat_app):
    res = chat_app.post('/api/video/storyboard', data = {
        'paths': '/no/such/file.png' })
    @py_assert1 = res.status_code
    @py_assert4 = 400
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert0 = res.json()['ok']
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


def test_api_ha_scene_route(chat_app, monkeypatch):
    monkeypatch.setattr('jarvis.home_assistant.activate_scene', (lambda scene: (True, 'Activated')))
    monkeypatch.setattr('jarvis.home_assistant.ha_enabled', (lambda : True))
    res = chat_app.post('/api/homeassistant/scene', json = {
        'entity_id': 'scene.movie' })
    @py_assert1 = res.status_code
    @py_assert4 = 200
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s.status_code\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(res) if 'res' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(res) else 'res',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert0 = res.json()['ok']
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


def test_cursor_bridge_domain_mcp_tools():
    pass
# WARNING: Decompyle incomplete

