# Source Generated with Decompyle++
# File: test_ha_docker.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for Home Assistant Docker autostart.'''
import builtins as @py_builtins

rewrite
from unittest.mock import patch
import _pytest.assertion.rewrite, assertion
from jarvis.ha_docker import container_running, ensure_homeassistant, ha_config_dir, should_autostart_ha

def test_should_autostart_default_off(monkeypatch):
    monkeypatch.delenv('JARVIS_HA_AUTOSTART', raising = False)
    monkeypatch.setattr('jarvis.ha_docker.shutil.which', (lambda _: '/usr/bin/docker'))
    @py_assert1 = should_autostart_ha()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(should_autostart_ha) if 'should_autostart_ha' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(should_autostart_ha) else 'should_autostart_ha',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_should_autostart_respects_off(monkeypatch):
    monkeypatch.setenv('JARVIS_HA_AUTOSTART', '0')
    monkeypatch.setattr('jarvis.ha_docker.shutil.which', (lambda _: '/usr/bin/docker'))
    @py_assert1 = should_autostart_ha()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(should_autostart_ha) if 'should_autostart_ha' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(should_autostart_ha) else 'should_autostart_ha',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py5': @pytest_ar._saferepr(@py_assert4) }
        @py_format8 = 'assert %(py7)s' % {
            'py7': @py_format6 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert4 = None


def test_ha_config_dir_default(monkeypatch):
    monkeypatch.delenv('JARVIS_HA_CONFIG', raising = False)
    @py_assert1 = ha_config_dir()
    @py_assert3 = @py_assert1.name
    @py_assert6 = 'homeassistant'
    @py_assert5 = @py_assert3 == @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s()\n}.name\n} == %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(ha_config_dir) if 'ha_config_dir' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ha_config_dir) else 'ha_config_dir',
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


def test_ha_api_healthy_uses_token(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_ensure_skips_when_autostart_off(monkeypatch):
    monkeypatch.setenv('JARVIS_HA_AUTOSTART', '0')
    patch('jarvis.ha_docker.ha_api_healthy', return_value = False)
    patch('jarvis.ha_docker.container_running', return_value = False)
    run = patch('jarvis.ha_docker.subprocess.run')
    @py_assert1 = ensure_homeassistant()
    @py_assert4 = False
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(ensure_homeassistant) if 'ensure_homeassistant' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ensure_homeassistant) else 'ensure_homeassistant',
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
    monkeypatch.setenv('JARVIS_HA_AUTOSTART', '1')
    patch('jarvis.ha_docker.ha_api_healthy', return_value = False)
    patch('jarvis.ha_docker.container_running', return_value = False)
    patch('jarvis.ha_docker.container_exists', return_value = True)
    run = patch('jarvis.ha_docker.subprocess.run')
    @py_assert1 = ensure_homeassistant()
    @py_assert4 = True
    @py_assert3 = @py_assert1 is @py_assert4
    if not @py_assert3:
        @py_format6 = @pytest_ar._call_reprcompare(('is',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} is %(py5)s',), (@py_assert1, @py_assert4)) % {
            'py0': @pytest_ar._saferepr(ensure_homeassistant) if 'ensure_homeassistant' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(ensure_homeassistant) else 'ensure_homeassistant',
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

