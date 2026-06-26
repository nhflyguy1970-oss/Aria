# Source Generated with Decompyle++
# File: test_self_upgrade.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Self-upgrade pipeline tests.'''
import builtins as @py_builtins

rewrite
from pathlib import Path
import _pytest.assertion.rewrite, assertion
import pytest
from jarvis.self_upgrade import branch_name_for_task, is_merge_command, is_self_upgrade_task, merge_pipeline, parse_self_upgrade_task, run_pipeline

def test_parse_self_upgrade_task():
    @py_assert0 = 'ping'
    @py_assert4 = 'self upgrade: add /api/ping'
    @py_assert6 = parse_self_upgrade_task(@py_assert4)
    @py_assert8 = @py_assert6.lower
    @py_assert10 = @py_assert8()
    @py_assert2 = @py_assert0 in @py_assert10
    if not @py_assert2:
        @py_format12 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py11)s\n{%(py11)s = %(py9)s\n{%(py9)s = %(py7)s\n{%(py7)s = %(py3)s(%(py5)s)\n}.lower\n}()\n}',), (@py_assert0, @py_assert10)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(parse_self_upgrade_task) if 'parse_self_upgrade_task' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(parse_self_upgrade_task) else 'parse_self_upgrade_task',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None
    @py_assert1 = 'run self upgrade: fix router'
    @py_assert3 = is_self_upgrade_task(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_self_upgrade_task) if 'is_self_upgrade_task' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_self_upgrade_task) else 'is_self_upgrade_task',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None


def test_branch_name():
    name = branch_name_for_task('add health route')
    @py_assert1 = name.startswith
    @py_assert3 = 'aria/upgrade-'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.startswith\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(name) if 'name' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(name) else 'name',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_run_pipeline_no_git(assistant, monkeypatch):
    monkeypatch.setattr('jarvis.git_util.is_repo', (lambda path = (None,): False))
    result = run_pipeline(assistant, 'add ping')
    @py_assert0 = result['ok']
    @py_assert2 = not @py_assert0
    if not @py_assert2:
        @py_format3 = 'assert not %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'git'
    @py_assert3 = result['message']
    @py_assert5 = @py_assert3.lower
    @py_assert7 = @py_assert5()
    @py_assert2 = @py_assert0 in @py_assert7
    if not @py_assert2:
        @py_format9 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py8)s\n{%(py8)s = %(py6)s\n{%(py6)s = %(py4)s.lower\n}()\n}',), (@py_assert0, @py_assert7)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_run_pipeline_dirty_tree(assistant = None, monkeypatch = None, tmp_path = None):
    monkeypatch.setattr('jarvis.git_util.is_repo', (lambda path = (None,): True))
    monkeypatch.setattr('jarvis.git_util.has_local_changes', (lambda path = (None,): True))
    result = run_pipeline(assistant, 'add ping')
    @py_assert0 = result['ok']
    @py_assert2 = not @py_assert0
    if not @py_assert2:
        @py_format3 = 'assert not %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert0 = 'uncommitted'
    @py_assert3 = result['message']
    @py_assert5 = @py_assert3.lower
    @py_assert7 = @py_assert5()
    @py_assert2 = @py_assert0 in @py_assert7
    if not @py_assert2:
        @py_format9 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py8)s\n{%(py8)s = %(py6)s\n{%(py6)s = %(py4)s.lower\n}()\n}',), (@py_assert0, @py_assert7)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_run_pipeline_success(assistant = None, monkeypatch = None, tmp_path = None):
    monkeypatch.setattr('jarvis.git_util.is_repo', (lambda path = (None,): True))
    monkeypatch.setattr('jarvis.git_util.has_local_changes', (lambda path = (None,): False))
    monkeypatch.setattr('jarvis.git_util.create_branch', (lambda name, path = (None,): f'''Created `{name}`'''))
    monkeypatch.setattr('jarvis.git_util.commit', (lambda msg, path, files = (None, None): '[main abc123] upgrade'))
    monkeypatch.setattr('jarvis.self_upgrade.verify_proposal', (lambda p, base = (None,): (True, 'pytest ok')))
    monkeypatch.setattr('jarvis.git_util.current_branch', (lambda path = (None,): 'main'))
    
    assistant._upgrade_wizard = lambda params, msg: {
'ok': True,
'proposal_id': 'p1',
'message': 'proposed' }
    
    assistant._upgrade_verify = lambda params, msg: {
'ok': True,
'message': 'verified' }
    
    assistant._upgrade_apply = lambda params, msg: {
'ok': True,
'message': 'applied',
'snapshot_id': 'snap1' }
    
    assistant._upgrade_proposal = lambda pid = (None,): {
'files': [
{
'path': 'jarvis/ping.py',
'code': 'def ping(): return 1\n' }],
'verified': True }
    assistant.session.last_proposal_id = 'p1'
    assistant.pending_proposals = {
        'p1': {
            'files': [
                {
                    'path': 'jarvis/ping.py',
                    'code': 'def ping(): return 1\n' }] } }
    result = run_pipeline(assistant, 'add ping route')
    @py_assert0 = result['ok']
    if not @py_assert0:
        @py_format2 = 'assert %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format2))
    @py_assert0 = None
    @py_assert1 = result.get
    @py_assert3 = 'awaiting_merge'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.get\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert0 = 'aria/upgrade'
    @py_assert4 = result.get
    @py_assert6 = 'branch'
    @py_assert8 = ''
    @py_assert10 = @py_assert4(@py_assert6, @py_assert8)
    @py_assert2 = @py_assert0 in @py_assert10
    if not @py_assert2:
        @py_format12 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py11)s\n{%(py11)s = %(py5)s\n{%(py5)s = %(py3)s.get\n}(%(py7)s, %(py9)s)\n}',), (@py_assert0, @py_assert10)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(result) if 'result' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(result) else 'result',
            'py5': @pytest_ar._saferepr(@py_assert4),
            'py7': @pytest_ar._saferepr(@py_assert6),
            'py9': @pytest_ar._saferepr(@py_assert8),
            'py11': @pytest_ar._saferepr(@py_assert10) }
        @py_format14 = 'assert %(py13)s' % {
            'py13': @py_format12 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format14))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert4 = None
    @py_assert6 = None
    @py_assert8 = None
    @py_assert10 = None


def test_merge_requires_session(assistant, monkeypatch):
    monkeypatch.setattr('jarvis.self_upgrade.get_session', (lambda : pass))
    result = merge_pipeline(assistant)
    @py_assert0 = result['ok']
    @py_assert2 = not @py_assert0
    if not @py_assert2:
        @py_format3 = 'assert not %(py1)s' % {
            'py1': @pytest_ar._saferepr(@py_assert0) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format3))
    @py_assert0 = None
    @py_assert2 = None


def test_router_self_upgrade():
    route = route
    import jarvis.router
    SessionContext = SessionContext
    import jarvis.session
    intent = route('self upgrade: add health endpoint', SessionContext())
    @py_assert0 = intent['action']
    @py_assert3 = 'self_upgrade_run'
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
    @py_assert0 = 'health'
    @py_assert3 = intent['params']['task']
    @py_assert5 = @py_assert3.lower
    @py_assert7 = @py_assert5()
    @py_assert2 = @py_assert0 in @py_assert7
    if not @py_assert2:
        @py_format9 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py8)s\n{%(py8)s = %(py6)s\n{%(py6)s = %(py4)s.lower\n}()\n}',), (@py_assert0, @py_assert7)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5),
            'py8': @pytest_ar._saferepr(@py_assert7) }
        @py_format11 = 'assert %(py10)s' % {
            'py10': @py_format9 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format11))
    @py_assert0 = None
    @py_assert2 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None
    intent2 = route('merge upgrade', SessionContext())
    @py_assert0 = intent2['action']
    @py_assert3 = 'self_upgrade_merge'
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
    @py_assert1 = 'approve merge'
    @py_assert3 = is_merge_command(@py_assert1)
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py0)s(%(py2)s)\n}' % {
            'py0': @pytest_ar._saferepr(is_merge_command) if 'is_merge_command' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(is_merge_command) else 'is_merge_command',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None

