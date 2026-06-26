# Source Generated with Decompyle++
# File: test_server_shutdown.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Server shutdown request.'''
import builtins as @py_builtins

rewrite
from jarvis.server_shutdown import consume_shutdown_request, request_shutdown
request_shutdown = request_shutdown
import _pytest.assertion.rewrite, assertion

def test_request_shutdown_requires_tray_or_exits(monkeypatch, tmp_path):
    ss = server_shutdown
    import jarvis.server_shutdown
    monkeypatch.setattr(ss, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(ss, 'SHUTDOWN_FLAG', tmp_path / 'shutdown_jarvis.request')
    monkeypatch.delenv('JARVIS_SERVICES_MANAGED', raising = False)
    monkeypatch.setattr(ss, '_exit_serve_process', (lambda delay = (0.35,): pass))
    out = request_shutdown()
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


def test_request_shutdown_signals_tray(monkeypatch, tmp_path):
    ss = server_shutdown
    import jarvis.server_shutdown
    monkeypatch.setattr(ss, 'DATA_DIR', tmp_path)
    flag = tmp_path / 'shutdown_jarvis.request'
    monkeypatch.setattr(ss, 'SHUTDOWN_FLAG', flag)
    monkeypatch.setenv('JARVIS_SERVICES_MANAGED', '1')
    monkeypatch.setattr(ss, '_signal_tray_shutdown', (lambda : True))
    out = request_shutdown()
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
    @py_assert1 = flag.is_file
    @py_assert3 = @py_assert1()
    @py_assert5 = not @py_assert3
    if not @py_assert5:
        @py_format6 = 'assert not %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(flag) if 'flag' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(flag) else 'flag',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_request_shutdown_flag_fallback(monkeypatch, tmp_path):
    ss = server_shutdown
    import jarvis.server_shutdown
    monkeypatch.setattr(ss, 'DATA_DIR', tmp_path)
    flag = tmp_path / 'shutdown_jarvis.request'
    monkeypatch.setattr(ss, 'SHUTDOWN_FLAG', flag)
    monkeypatch.setenv('JARVIS_SERVICES_MANAGED', '1')
    monkeypatch.setattr(ss, '_signal_tray_shutdown', (lambda : False))
    out = request_shutdown()
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
    @py_assert1 = flag.is_file
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_file\n}()\n}' % {
            'py0': @pytest_ar._saferepr(flag) if 'flag' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(flag) else 'flag',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert1 = consume_shutdown_request()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(consume_shutdown_request) if 'consume_shutdown_request' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(consume_shutdown_request) else 'consume_shutdown_request',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None

