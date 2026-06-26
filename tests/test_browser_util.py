# Source Generated with Decompyle++
# File: test_browser_util.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Browser launch helper.'''
import builtins as @py_builtins

rewrite
from jarvis.browser_util import browser_candidates, open_url, resolve_browser
open_url = open_url
resolve_browser = resolve_browser
import _pytest.assertion.rewrite, assertion

def test_browser_candidates_prefers_env(monkeypatch):
    monkeypatch.setenv('JARVIS_BROWSER', 'google-chrome')
    names = browser_candidates()
    @py_assert0 = names[0]
    @py_assert3 = 'google-chrome'
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


def test_open_url_uses_configured_browser(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_open_url_skips_xdg_by_default(monkeypatch):
    pass
# WARNING: Decompyle incomplete


def test_resolve_browser_finds_flatpak_export(monkeypatch, tmp_path):
    monkeypatch.delenv('JARVIS_BROWSER_PATH', raising = False)
    monkeypatch.setattr('jarvis.browser_util.shutil.which', (lambda name: pass))
    fake = tmp_path / 'com.google.Chrome'
    fake.write_text('#!/bin/sh\n')
    fake.chmod(493)
    monkeypatch.setattr('jarvis.browser_util.CHROME_PATHS', (str(fake),))
    @py_assert1 = resolve_browser()
    @py_assert6 = str(fake)
    @py_assert3 = @py_assert1 == @py_assert6
    if not @py_assert3:
        @py_format8 = @pytest_ar._call_reprcompare(('==',), (@py_assert3,), ('%(py2)s\n{%(py2)s = %(py0)s()\n} == %(py7)s\n{%(py7)s = %(py4)s(%(py5)s)\n}',), (@py_assert1, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(resolve_browser) if 'resolve_browser' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(resolve_browser) else 'resolve_browser',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(str) if 'str' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(str) else 'str',
            'py5': @pytest_ar._saferepr(fake) if 'fake' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(fake) else 'fake',
            'py7': @pytest_ar._saferepr(@py_assert6) }
        @py_format10 = 'assert %(py9)s' % {
            'py9': @py_format8 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format10))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert6 = None


def test_open_url_app_uses_isolated_profile(monkeypatch, tmp_path):
    pass
# WARNING: Decompyle incomplete


def test_open_url_uses_flatpak_run(monkeypatch):
    pass
# WARNING: Decompyle incomplete

