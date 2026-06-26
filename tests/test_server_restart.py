"""Server restart request flag."""

from jarvis.server_restart import consume_restart_request, request_restart


def test_request_restart_requires_tray(monkeypatch, tmp_path):
    import jarvis.server_restart as sr

    monkeypatch.setattr(sr, "DATA_DIR", tmp_path)
    monkeypatch.setattr(sr, "RESTART_FLAG", tmp_path / "restart_server.request")
    monkeypatch.delenv("JARVIS_SERVICES_MANAGED", raising=False)
    out = request_restart()
    assert out["ok"] is False


def test_request_restart_signals_tray(monkeypatch, tmp_path):
    import jarvis.server_restart as sr

    monkeypatch.setattr(sr, "DATA_DIR", tmp_path)
    flag = tmp_path / "restart_server.request"
    monkeypatch.setattr(sr, "RESTART_FLAG", flag)
    monkeypatch.setenv("JARVIS_SERVICES_MANAGED", "1")
    monkeypatch.setattr(sr, "_signal_tray_restart", lambda: True)
    out = request_restart()
    assert out["ok"] is True
    assert not flag.is_file()


def test_request_restart_flag_fallback(monkeypatch, tmp_path):
    import jarvis.server_restart as sr

    monkeypatch.setattr(sr, "DATA_DIR", tmp_path)
    flag = tmp_path / "restart_server.request"
    monkeypatch.setattr(sr, "RESTART_FLAG", flag)
    monkeypatch.setenv("JARVIS_SERVICES_MANAGED", "1")
    monkeypatch.setattr(sr, "_signal_tray_restart", lambda: False)
    out = request_restart()
    assert out["ok"] is True
    assert flag.is_file()
    assert consume_restart_request() is True
