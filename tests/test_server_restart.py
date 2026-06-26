# Source Generated with Decompyle++
# File: test_server_restart.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Server restart request flag.'''
import builtins as @py_builtins

rewrite
from jarvis.server_restart import consume_restart_request, request_restart
request_restart = request_restart
import _pytest.assertion.rewrite, assertion

def test_request_restart_requires_tray(monkeypatch, tmp_path):
    sr = server_restart
    import jarvis.server_restart
    monkeypatch.setattr(sr, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(sr, 'RESTART_FLAG', tmp_path / 'restart_server.request')
    monkeypatch.delenv('JARVIS_SERVICES_MANAGED', raising = False)
    out = request_restart()
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


def test_request_restart_signals_tray(monkeypatch, tmp_path):
    sr = server_restart
    import jarvis.server_restart
    monkeypatch.setattr(sr, 'DATA_DIR', tmp_path)
    flag = tmp_path / 'restart_server.request'
    monkeypatch.setattr(sr, 'RESTART_FLAG', flag)
    monkeypatch.setenv('JARVIS_SERVICES_MANAGED', '1')
    monkeypatch.setattr(sr, '_signal_tray_restart', (lambda : True))
    out = request_restart()
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


def test_request_restart_flag_fallback(monkeypatch, tmp_path):
    sr = server_restart
    import jarvis.server_restart
    monkeypatch.setattr(sr, 'DATA_DIR', tmp_path)
    flag = tmp_path / 'restart_server.request'
    monkeypatch.setattr(sr, 'RESTART_FLAG', flag)
    monkeypatch.setenv('JARVIS_SERVICES_MANAGED', '1')
    monkeypatch.setattr(sr, '_signal_tray_restart', (lambda : False))
    out = request_restart()
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
    @py_assert1 = consume_restart_request()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(consume_restart_request) if 'consume_restart_request' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(consume_restart_request) else 'consume_restart_request',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None

