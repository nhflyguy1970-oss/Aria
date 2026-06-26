# Source Generated with Decompyle++
# File: test_p2_projects.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''P2 projects, device router, scene presets tests.'''
from __future__ import annotations
import builtins as @py_builtins

rewrite
import json = import _pytest.assertion.rewrite, assertion

def test_project_registry(tmp_path, monkeypatch):
    root = tmp_path / 'projects'
    monkeypatch.setattr('jarvis.project_registry.PROJECTS_ROOT', root)
    monkeypatch.setattr('jarvis.active_project.ACTIVE_FILE', tmp_path / 'active.json')
    pr = project_registry
    import jarvis.project_registry
    ap = active_project
    import jarvis.active_project
    meta = pr.create_project('Lab Bench')
    @py_assert0 = meta['slug']
    @py_assert3 = 'lab-bench'
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
    @py_assert1 = 'lab-bench'
    @py_assert3 = root / @py_assert1
    @py_assert4 = 'cad'
    @py_assert6 = @py_assert3 / @py_assert4
    @py_assert7 = @py_assert6.is_dir
    @py_assert9 = @py_assert7()
    if not @py_assert9:
        @py_format11 = 'assert %(py10)s\n{%(py10)s = %(py8)s\n{%(py8)s = ((%(py0)s / %(py2)s) / %(py5)s).is_dir\n}()\n}' % {
            'py0': @pytest_ar._saferepr(root) if 'root' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(root) else 'root',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py8': @pytest_ar._saferepr(@py_assert7),
            'py10': @pytest_ar._saferepr(@py_assert9) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert7 = None
    @py_assert9 = None
    ap.set_active_slug(meta['slug'])
    @py_assert1 = ap.get_active_slug
    @py_assert3 = @py_assert1()
    @py_assert6 = 'lab-bench'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.get_active_slug\n}()\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(ap) if 'ap' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ap) else 'ap',
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
    listed = pr.list_projects()
    @py_assert1 = listed()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_scene_presets(tmp_path, monkeypatch):
    presets = tmp_path / 'scene_presets.json'
    presets.write_text(json.dumps({
        'test mode': {
            'label': 'Test',
            'devices': [] } }), encoding = 'utf-8')
    monkeypatch.setattr('jarvis.scene_presets.PRESETS_FILE', presets)
    activate_preset = activate_preset
    list_presets = list_presets
    import jarvis.scene_presets
    @py_assert2 = list_presets()
    @py_assert4 = len(@py_assert2)
    @py_assert7 = 1
    @py_assert6 = @py_assert4 >= @py_assert7
    if not @py_assert6:
        @py_format9 = @pytest_ar._call_reprcompare(('>=',), (@py_assert6,), ('%(py5)s\n{%(py5)s = %(py0)s(%(py3)s\n{%(py3)s = %(py1)s()\n})\n} >= %(py8)s',), (@py_assert4, @py_assert7)) % {
            'py0': @pytest_ar._saferepr(len) if 'len' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(len) else 'len',
            'py1': @pytest_ar._saferepr(list_presets) if 'list_presets' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(list_presets) else 'list_presets',
            'py3': @pytest_ar._saferepr(@py_assert2),
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert7 = None
    (ok, msg) = activate_preset('test mode')
    if not ok:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(ok) if 'ok' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ok) else 'ok' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))


def test_scene_preset_reports_failures(tmp_path, monkeypatch):
    presets = tmp_path / 'scene_presets.json'
    presets.write_text(json.dumps({
        'broken mode': {
            'label': 'Broken',
            'devices': [
                {
                    'target': 'light.missing',
                    'action': 'on' }] } }), encoding = 'utf-8')
    monkeypatch.setattr('jarvis.scene_presets.PRESETS_FILE', presets)
    monkeypatch.setattr('jarvis.p2_flags.scene_presets_enabled', (lambda : True))
    monkeypatch.setattr('jarvis.home_assistant.ha_enabled', (lambda : False))
    monkeypatch.setattr('jarvis.p2_flags.kasa_enabled', (lambda : False))
    
    def fail_control(target, action, **kwargs):
        return (False, f'''no match for {target}''', 'ha')

    monkeypatch.setattr('jarvis.device_router.control_device', fail_control)
    activate_preset = activate_preset
    import jarvis.scene_presets
    (ok, msg) = activate_preset('broken mode')
    @py_assert2 = False
    @py_assert1 = ok is @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is',), (@py_assert1,), ('%(py0)s is %(py3)s',), (ok, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(ok) if 'ok' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ok) else 'ok',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert0 = 'failed'
    @py_assert4 = msg.lower
    @py_assert6 = @py_assert4()
    @py_assert2 = @py_assert0 in @py_assert6
    if not @py_assert2:
        @py_format8 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py7)s\n{%(py7)s = %(py5)s\n{%(py5)s = %(py3)s.lower\n}()\n}',), (@py_assert0, @py_assert6)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(msg) if 'msg' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(msg) else 'msg',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert0 = 'no device steps configured'
    @py_assert4 = msg.lower
    @py_assert6 = @py_assert4()
    @py_assert2 = @py_assert0 not in @py_assert6
    if not @py_assert2:
        @py_format8 = @pytest_ar._call_reprcompare(('not in',), (@py_assert2,), ('%(py1)s not in %(py7)s\n{%(py7)s = %(py5)s\n{%(py5)s = %(py3)s.lower\n}()\n}',), (@py_assert0, @py_assert6)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(msg) if 'msg' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(msg) else 'msg',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None


def test_device_router_ha_fallback(monkeypatch):
    monkeypatch.setattr('jarvis.p2_flags.device_router_enabled', (lambda : True))
    monkeypatch.setattr('jarvis.p2_flags.kasa_enabled', (lambda : False))
    monkeypatch.setattr('jarvis.home_assistant.ha_enabled', (lambda : True))
    
    def fake_control(target, action):
        return (True, f'''HA {target} {action}''')

    monkeypatch.setattr('jarvis.home_assistant.control_entity', fake_control)
    control_device = control_device
    import jarvis.device_router
    (ok, msg, backend) = control_device('office lights', 'on')
    @py_assert1 = []
    @py_assert0 = ok
    if ok:
        @py_assert6 = 'ha'
        @py_assert5 = backend == @py_assert6
        @py_assert0 = @py_assert5
# WARNING: Decompyle incomplete


def test_shopping_parse():
    parse_shopping_query = parse_shopping_query
    import jarvis.web_browse
    spec = parse_shopping_query('find standing desk under $200 on amazon')
    @py_assert1 = []
    @py_assert0 = spec
    if spec:
        @py_assert4 = spec['max_price']
        @py_assert7 = 200
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_vlm_json_parse():
    _parse_vlm_json = _parse_vlm_json
    import jarvis.browser_vlm
    raw = 'Here: {"action":"click","x":100,"y":200,"reason":"button"}'
    plan = _parse_vlm_json(raw)
    @py_assert1 = []
    @py_assert0 = plan
    if plan:
        @py_assert4 = plan['action']
        @py_assert7 = 'click'
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
        if @py_assert6:
            @py_assert12 = plan['x']
            @py_assert15 = 100
            @py_assert14 = @py_assert12 == @py_assert15
            @py_assert0 = @py_assert14
# WARNING: Decompyle incomplete


def test_dom_action_parse():
    _parse_action = _parse_action
    import jarvis.browser_dom_agent
    raw = '```json\n{"action":"click","selector":"#login"}\n```'
    act = _parse_action(raw)
    @py_assert1 = []
    @py_assert0 = act
    if act:
        @py_assert4 = act['selector']
        @py_assert7 = '#login'
        @py_assert6 = @py_assert4 == @py_assert7
        @py_assert0 = @py_assert6
# WARNING: Decompyle incomplete


def test_dom_execute_done():
    execute_dom_action = execute_dom_action
    import jarvis.browser_dom_agent
    r = execute_dom_action({
        'action': 'done',
        'summary': 'Finished' })
    @py_assert1 = r.get
    @py_assert3 = 'done'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert8 = True
    @py_assert7 = @py_assert5 is @py_assert8
    if not @py_assert7:
        @py_format10 = @pytest_ar._call_reprcompare(('is',), (@py_assert7,), ('%(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n} is %(py9)s',), (@py_assert5, @py_assert8)) % {
            'py0': @pytest_ar._saferepr(r) if 'r' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(r) else 'r',
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


def test_project_journal_actions_scoped(tmp_path, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_resolve_namespace_respects_active_slug(tmp_path, monkeypatch):
    root = tmp_path / 'projects'
    monkeypatch.setattr('jarvis.project_registry.PROJECTS_ROOT', root)
    monkeypatch.setattr('jarvis.active_project.ACTIVE_FILE', tmp_path / 'active.json')
    ap = active_project
    import jarvis.active_project
    pr = project_registry
    import jarvis.project_registry
    resolve_project_namespace = resolve_project_namespace
    import jarvis.memory_context
    meta = pr.create_project('Lab Namespace')
    ap.set_active_slug(meta['slug'])
    @py_assert1 = resolve_project_namespace()
    @py_assert4 = meta['slug']
    @py_assert3 = @py_assert1 == @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(resolve_project_namespace) if 'resolve_project_namespace' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_project_namespace) else 'resolve_project_namespace',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_sync_project_namespace_prefers_active(tmp_path, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_coding_root_wired_on_switch(tmp_path, monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_code_index_search_uses_per_project_index(tmp_path, monkeypatch):
    monkeypatch.setattr('jarvis.code_index.CODE_INDEX', tmp_path / 'global_code_index.json')
    monkeypatch.setattr('jarvis.project_registry.PROJECTS_ROOT', tmp_path / 'projects')
    monkeypatch.setattr('jarvis.active_project.ACTIVE_FILE', tmp_path / 'active.json')
    monkeypatch.setattr('jarvis.llm.embed_text', (lambda t: if t:
[
1,
0]))
    ap = active_project
    import jarvis.active_project
    ci = code_index
    import jarvis.code_index
    pr = project_registry
    import jarvis.project_registry
    repo = tmp_path / 'indexed-repo'
    repo.mkdir()
    (repo / 'marker.py').write_text('UNIQUE_MARKER_TOKEN = 42\n', encoding = 'utf-8')
    meta = pr.create_project('Indexed', git_path = str(repo))
    slug = meta['slug']
    idx = pr.project_dir(slug) / 'code_index.json'
    ci.build_index(repo, index_path = idx)
    ap.set_active_slug(slug)
    ci.invalidate_cache()
    hits = ci.search('UNIQUE_MARKER_TOKEN')
    if not hits:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(hits) if 'hits' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(hits) else 'hits' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    @py_assert1 = hits()
    @py_assert3 = any(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(any) if 'any' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(any) else 'any',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_journal_slugs_provision_workspace(tmp_path, monkeypatch):
    journal_dir = tmp_path / 'journal' / 'projects'
    journal_dir.mkdir(parents = True)
    (journal_dir / 'audit-proj.json').write_text(json.dumps({
        'slug': 'audit-proj',
        'title': 'Audit Proj',
        'daily_log': { } }), encoding = 'utf-8')
    monkeypatch.setattr('jarvis.project_journal.PROJECTS_DIR', journal_dir)
    monkeypatch.setattr('jarvis.project_journal.INDEX_FILE', journal_dir / 'index.json')
    monkeypatch.setattr('jarvis.project_registry.PROJECTS_ROOT', tmp_path / 'projects')
    pr = project_registry
    import jarvis.project_registry
# WARNING: Decompyle incomplete

