"""Tests for uncensored mode password gate."""

import pytest

from jarvis import uncensored_auth as auth


@pytest.fixture
def auth_file(tmp_path, monkeypatch):
    path = tmp_path / "uncensored_auth.json"
    monkeypatch.setattr(auth, "AUTH_FILE", path)
    monkeypatch.setattr(auth, "_sessions", {})
    return path


def test_set_and_verify_password(auth_file):
    auth.set_password("secret123")
    assert auth.is_configured()
    assert auth.verify_password("secret123")
    assert not auth.verify_password("wrong")


def test_try_enable_first_time_setup(auth_file):
    token, err = auth.try_enable("mypass", confirm="mypass")
    assert err is None
    assert token
    assert auth.validate_session(token)


def test_try_enable_wrong_password(auth_file):
    auth.set_password("correct")
    token, err = auth.try_enable("bad", confirm="")
    assert token is None
    assert err == "Wrong password"


def test_session_reuse(auth_file):
    auth.set_password("pass")
    token, _ = auth.try_enable("pass")
    token2, err = auth.try_enable("", session_token=token)
    assert err is None
    assert token2 == token


def test_clear_password(auth_file):
    auth.set_password("old1")
    assert auth.is_configured()
    auth.clear_password()
    assert not auth.is_configured()
    assert not auth.verify_password("old1")


def test_try_enable_strips_whitespace(auth_file):
    token, err = auth.try_enable("  mypass  ", confirm="  mypass  ")
    assert err is None
    assert token
    assert auth.verify_password("mypass")


def test_enforce_env_unlock_bootstrap(auth_file, monkeypatch):
    monkeypatch.setenv("JARVIS_UNCENSORED_PASSWORD", "fromenv")
    assert auth.enforce_env_unlock() is True
    assert auth.is_configured()
    assert auth.verify_password("fromenv")
