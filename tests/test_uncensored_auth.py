# Source Generated with Decompyle++
# File: test_uncensored_auth.cpython-312-pytest-9.1.0.pyc (Python 3.12)

'''Tests for uncensored mode password gate.'''
import builtins as @py_builtins

rewrite
import pytest = import _pytest.assertion.rewrite, assertion
from jarvis import uncensored_auth as auth
auth_file = (lambda tmp_path, monkeypatch: path = tmp_path / 'uncensored_auth.json'monkeypatch.setattr(auth, 'AUTH_FILE', path)monkeypatch.setattr(auth, '_sessions', { })path)()

def test_set_and_verify_password(auth_file):
    auth.set_password('secret123')
    @py_assert1 = auth.is_configured
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_configured\n}()\n}' % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert1 = auth.verify_password
    @py_assert3 = 'secret123'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.verify_password\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = auth.verify_password
    @py_assert3 = 'wrong'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.verify_password\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_try_enable_first_time_setup(auth_file):
    (token, err) = auth.try_enable('mypass', confirm = 'mypass')
    @py_assert2 = None
    @py_assert1 = err is @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is',), (@py_assert1,), ('%(py0)s is %(py3)s',), (err, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(err) if 'err' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(err) else 'err',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    if not token:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(token) if 'token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token) else 'token' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    @py_assert1 = auth.validate_session
    @py_assert4 = @py_assert1(token)
    if not @py_assert4:
        @py_format6 = 'assert %(py5)s\n{%(py5)s = %(py2)s\n{%(py2)s = %(py0)s.validate_session\n}(%(py3)s)\n}' % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py3': @pytest_ar._saferepr(token) if 'token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token) else 'token',
            'py5': @pytest_ar._saferepr(@py_assert4) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert4 = None


def test_try_enable_wrong_password(auth_file):
    auth.set_password('correct')
    (token, err) = auth.try_enable('bad', confirm = '')
    @py_assert2 = None
    @py_assert1 = token is @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is',), (@py_assert1,), ('%(py0)s is %(py3)s',), (token, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(token) if 'token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token) else 'token',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert2 = 'Wrong password'
    @py_assert1 = err == @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py3)s',), (err, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(err) if 'err' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(err) else 'err',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None


def test_session_reuse(auth_file):
    auth.set_password('pass')
    (token, _) = auth.try_enable('pass')
    (token2, err) = auth.try_enable('', session_token = token)
    @py_assert2 = None
    @py_assert1 = err is @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is',), (@py_assert1,), ('%(py0)s is %(py3)s',), (err, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(err) if 'err' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(err) else 'err',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    @py_assert1 = token2 == token
    if not @py_assert1:
        @py_format3 = @pytest_ar._call_reprcompare(('==',), (@py_assert1,), ('%(py0)s == %(py2)s',), (token2, token)) % {
            'py0': @pytest_ar._saferepr(token2) if 'token2' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token2) else 'token2',
            'py2': @pytest_ar._saferepr(token) if 'token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token) else 'token' }
        @py_format5 = 'assert %(py4)s' % {
            'py4': @py_format3 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None


def test_clear_password(auth_file):
    auth.set_password('old1')
    @py_assert1 = auth.is_configured
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_configured\n}()\n}' % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    auth.clear_password()
    @py_assert1 = auth.is_configured
    @py_assert3 = @py_assert1()
    @py_assert5 = not @py_assert3
    if not @py_assert5:
        @py_format6 = 'assert not %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_configured\n}()\n}' % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert1 = auth.verify_password
    @py_assert3 = 'old1'
    @py_assert5 = @py_assert1(@py_assert3)
    @py_assert7 = not @py_assert5
    if not @py_assert7:
        @py_format8 = 'assert not %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.verify_password\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format8))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None
    @py_assert7 = None


def test_try_enable_strips_whitespace(auth_file):
    (token, err) = auth.try_enable('  mypass  ', confirm = '  mypass  ')
    @py_assert2 = None
    @py_assert1 = err is @py_assert2
    if not @py_assert1:
        @py_format4 = @pytest_ar._call_reprcompare(('is',), (@py_assert1,), ('%(py0)s is %(py3)s',), (err, @py_assert2)) % {
            'py0': @pytest_ar._saferepr(err) if 'err' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(err) else 'err',
            'py3': @pytest_ar._saferepr(@py_assert2) }
        @py_format6 = 'assert %(py5)s' % {
            'py5': @py_format4 }
        raise AssertionError(@pytest_ar._format_explanation(@py_format6))
    @py_assert1 = None
    @py_assert2 = None
    if not token:
        @py_format1 = 'assert %(py0)s' % {
            'py0': @pytest_ar._saferepr(token) if 'token' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(token) else 'token' }
        raise AssertionError(@pytest_ar._format_explanation(@py_format1))
    @py_assert1 = auth.verify_password
    @py_assert3 = 'mypass'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.verify_password\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None


def test_enforce_env_unlock_bootstrap(auth_file, monkeypatch):
    monkeypatch.setenv('JARVIS_UNCENSORED_PASSWORD', 'fromenv')
    @py_assert1 = auth.enforce_env_unlock
    @py_assert3 = @py_assert1()
    @py_assert6 = True
    @py_assert5 = @py_assert3 is @py_assert6
    if not @py_assert5:
        @py_format8 = @pytest_ar._call_reprcompare(('is',), (@py_assert5,), ('%(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.enforce_env_unlock\n}()\n} is %(py7)s',), (@py_assert3, @py_assert6)) % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
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
    @py_assert1 = auth.is_configured
    @py_assert3 = @py_assert1()
    if not @py_assert3:
        @py_format5 = 'assert %(py4)s\n{%(py4)s = %(py2)s\n{%(py2)s = %(py0)s.is_configured\n}()\n}' % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format5))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert1 = auth.verify_password
    @py_assert3 = 'fromenv'
    @py_assert5 = @py_assert1(@py_assert3)
    if not @py_assert5:
        @py_format7 = 'assert %(py6)s\n{%(py6)s = %(py2)s\n{%(py2)s = %(py0)s.verify_password\n}(%(py4)s)\n}' % {
            'py0': @pytest_ar._saferepr(auth) if 'auth' in @py_builtins.locals() or @pytest_ar._should_repr_global_name(auth) else 'auth',
            'py2': @pytest_ar._saferepr(@py_assert1),
            'py4': @pytest_ar._saferepr(@py_assert3),
            'py6': @pytest_ar._saferepr(@py_assert5) }
        raise AssertionError(@pytest_ar._format_explanation(@py_format7))
    @py_assert1 = None
    @py_assert3 = None
    @py_assert5 = None

