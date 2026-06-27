"""Server shutdown request."""

from jarvis.server_shutdown import consume_shutdown_request, request_shutdown


def test_request_shutdown_requires_tray_or_exits(monkeypatch, tmp_path):
    import jarvis.server_shutdown as ss

    monkeypatch.setattr(ss, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ss, "SHUTDOWN_FLAG", tmp_path / "shutdown_jarvis.request")
    monkeypatch.delenv("JARVIS_SERVICES_MANAGED", raising=False)
    monkeypatch.setattr(ss, "_exit_serve_process", lambda delay=0.35: None)
    out = request_shutdown()
    assert out["ok"] is True


def test_request_shutdown_signals_tray(monkeypatch, tmp_path):
    import jarvis.server_shutdown as ss

    monkeypatch.setattr(ss, "DATA_DIR", tmp_path)
    flag = tmp_path / "shutdown_jarvis.request"
    monkeypatch.setattr(ss, "SHUTDOWN_FLAG", flag)
    monkeypatch.setenv("JARVIS_SERVICES_MANAGED", "1")
    monkeypatch.setattr(ss, "_signal_tray_shutdown", lambda: True)
    out = request_shutdown()
    assert out["ok"] is True
    assert not flag.is_file()


def test_request_shutdown_flag_fallback(monkeypatch, tmp_path):
    import jarvis.server_shutdown as ss

    monkeypatch.setattr(ss, "DATA_DIR", tmp_path)
    flag = tmp_path / "shutdown_jarvis.request"
    monkeypatch.setattr(ss, "SHUTDOWN_FLAG", flag)
    monkeypatch.setenv("JARVIS_SERVICES_MANAGED", "1")
    monkeypatch.setattr(ss, "_signal_tray_shutdown", lambda: False)
    out = request_shutdown()
    assert out["ok"] is True
    assert flag.is_file()
    assert consume_shutdown_request() is True
