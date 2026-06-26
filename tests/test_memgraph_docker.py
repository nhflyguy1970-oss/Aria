# Source Generated with Decompyle++
# File: test_memgraph_docker.cpython-312-pytest-9.0.3.pyc (Python 3.12)

'''Tests for Memgraph Docker autostart.'''
import builtins as @py_builtins

rewrite
from unittest.mock import patch
import _pytest.assertion.rewrite, assertion
from jarvis.memgraph_docker import ensure_memgraph, memgraph_bolt_healthy, should_autostart_memgraph

def test_should_autostart_default_off(monkeypatch):
    monkeypatch.setattr('jarvis.memgraph_docker.load_jarvis_env', (lambda : pass))
    monkeypatch.setenv('JARVIS_GRAPH_BACKEND', 'sqlite')
    monkeypatch.delenv('JARVIS_MEMGRAPH_AUTOSTART', raising = False)
    @py_assert1 = should_autostart_memgraph()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(should_autostart_memgraph) if 'should_autostart_memgraph' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(should_autostart_memgraph) else 'should_autostart_memgraph',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_should_autostart_on_when_graph_backend_memgraph(monkeypatch):
    monkeypatch.setattr('jarvis.memgraph_docker.load_jarvis_env', (lambda : pass))
    monkeypatch.setenv('JARVIS_GRAPH_BACKEND', 'memgraph')
    monkeypatch.delenv('JARVIS_MEMGRAPH_AUTOSTART', raising = False)
    monkeypatch.setattr('jarvis.memgraph_docker.docker_available', (lambda : True))
    @py_assert1 = should_autostart_memgraph()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(should_autostart_memgraph) if 'should_autostart_memgraph' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(should_autostart_memgraph) else 'should_autostart_memgraph',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_should_autostart_respects_explicit_off(monkeypatch):
    monkeypatch.setattr('jarvis.memgraph_docker.load_jarvis_env', (lambda : pass))
    monkeypatch.setenv('JARVIS_GRAPH_BACKEND', 'memgraph')
    monkeypatch.setenv('JARVIS_MEMGRAPH_AUTOSTART', '0')
    monkeypatch.setattr('jarvis.memgraph_docker.docker_available', (lambda : True))
    @py_assert1 = should_autostart_memgraph()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(should_autostart_memgraph) if 'should_autostart_memgraph' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(should_autostart_memgraph) else 'should_autostart_memgraph',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_ensure_skips_when_autostart_off(monkeypatch):
    monkeypatch.setenv('JARVIS_MEMGRAPH_AUTOSTART', '0')
    patch('jarvis.memgraph_docker.memgraph_bolt_healthy', return_value = False)
    patch('jarvis.memgraph_docker.container_running', return_value = False)
    run = patch('jarvis.memgraph_docker.subprocess.run')
    @py_assert1 = ensure_memgraph()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(ensure_memgraph) if 'ensure_memgraph' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ensure_memgraph) else 'ensure_memgraph',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    run.assert_not_called()
    None(None, None)
    None(None, None)
    None(None, None)
    return None
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass


def test_ensure_starts_existing_container(monkeypatch):
    monkeypatch.setenv('JARVIS_GRAPH_BACKEND', 'memgraph')
    monkeypatch.delenv('JARVIS_MEMGRAPH_AUTOSTART', raising = False)
    patch('jarvis.memgraph_docker.should_autostart_memgraph', return_value = True)
    patch('jarvis.memgraph_docker.memgraph_bolt_healthy', return_value = False)
    patch('jarvis.memgraph_docker.container_running', return_value = False)
    patch('jarvis.memgraph_docker.container_exists', return_value = True)
    run = patch('jarvis.memgraph_docker.subprocess.run')
    @py_assert1 = ensure_memgraph()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(ensure_memgraph) if 'ensure_memgraph' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ensure_memgraph) else 'ensure_memgraph',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    run.assert_called_once()
    @py_assert0 = run.call_args.args[0][:2]
    @py_assert3 = [
        'docker',
        'start']
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
    None(None, None)
    None(None, None)
    None(None, None)
    None(None, None)
    None(None, None)
    return None
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass


def test_ensure_creates_container_with_restart_policy(monkeypatch):
    monkeypatch.setenv('JARVIS_GRAPH_BACKEND', 'memgraph')
    patch('jarvis.memgraph_docker.should_autostart_memgraph', return_value = True)
    patch('jarvis.memgraph_docker.memgraph_bolt_healthy', return_value = False)
    patch('jarvis.memgraph_docker.container_running', return_value = False)
    patch('jarvis.memgraph_docker.container_exists', return_value = False)
    run = patch('jarvis.memgraph_docker.subprocess.run')
    @py_assert1 = ensure_memgraph()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(ensure_memgraph) if 'ensure_memgraph' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ensure_memgraph) else 'ensure_memgraph',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    args = run.call_args.args[0]
    @py_assert0 = args[:2]
    @py_assert3 = [
        'docker',
        'run']
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
    @py_assert0 = '--restart=unless-stopped'
    @py_assert2 = @py_assert0 in args
    if not @py_assert2:
        @py_format4 = @pytest_ar._call_reprcompare(('in',), (@py_assert2,), ('%(py1)s in %(py3)s',), (@py_assert0, args)) % {
            'py1': @pytest_ar._saferepr(@py_assert0),
            'py3': @pytest_ar._saferepr(args) if 'args' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(args) else 'args' }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert0 = None
    @py_assert2 = None
    None(None, None)
    None(None, None)
    None(None, None)
    None(None, None)
    None(None, None)
    return None
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass
    continue
    with None:
        if not None:
            pass


def test_memgraph_bolt_healthy_socket(monkeypatch):
    
    class FakeSock:
        
        def __enter__(self):
            return self

        
        def __exit__(self, *args):
            return False


    patch('jarvis.memgraph_docker.socket.create_connection', return_value = FakeSock())
    @py_assert1 = memgraph_bolt_healthy()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(memgraph_bolt_healthy) if 'memgraph_bolt_healthy' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(memgraph_bolt_healthy) else 'memgraph_bolt_healthy',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None
    None(None, None)
    return None
    with None:
        if not None:
            pass

