"""Browser launch helper."""

from jarvis.browser_util import browser_candidates, open_url, resolve_browser


def test_browser_candidates_prefers_env(monkeypatch):
    monkeypatch.setenv("JARVIS_BROWSER", "google-chrome")
    names = browser_candidates()
    assert names[0] == "google-chrome"


def test_open_url_uses_configured_browser(monkeypatch):
    monkeypatch.setenv("JARVIS_BROWSER", "echo")
    monkeypatch.setenv("JARVIS_BROWSER_ALLOW_XDG", "0")
    monkeypatch.delenv("JARVIS_BROWSER_PATH", raising=False)
    monkeypatch.setattr("jarvis.browser_util.shutil.which", lambda name: "/bin/echo" if name == "echo" else None)
    calls = []
    monkeypatch.setattr(
        "jarvis.browser_util.subprocess.Popen",
        lambda cmd, **kw: calls.append(cmd) or type("P", (), {"poll": lambda: 0})(),
    )
    monkeypatch.setattr("jarvis.browser_util._notify_browser_missing", lambda url: None)
    assert open_url("http://127.0.0.1:8765") is True
    assert calls[0][0] == "/bin/echo"


def test_open_url_skips_xdg_by_default(monkeypatch):
    monkeypatch.delenv("JARVIS_BROWSER_PATH", raising=False)
    monkeypatch.setattr("jarvis.browser_util.resolve_browser", lambda: None)
    notified = []
    monkeypatch.setattr(
        "jarvis.browser_util._notify_browser_missing",
        lambda url: notified.append(url),
    )
    assert open_url("http://127.0.0.1:8765") is False
    assert notified == ["http://127.0.0.1:8765"]


def test_resolve_browser_finds_flatpak_export(monkeypatch, tmp_path):
    monkeypatch.delenv("JARVIS_BROWSER_PATH", raising=False)
    monkeypatch.setattr("jarvis.browser_util.shutil.which", lambda name: None)
    fake = tmp_path / "com.google.Chrome"
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.setattr(
        "jarvis.browser_util.CHROME_PATHS",
        (str(fake),),
    )
    assert resolve_browser() == str(fake)


def test_open_url_uses_flatpak_run(monkeypatch):
    monkeypatch.setattr("jarvis.browser_util.resolve_browser", lambda: "flatpak:com.google.Chrome")
    calls = []
    monkeypatch.setattr(
        "jarvis.browser_util.subprocess.Popen",
        lambda cmd, **kw: calls.append(cmd) or type("P", (), {"poll": lambda: 0})(),
    )
    assert open_url("http://127.0.0.1:8765") is True
    assert calls[0] == ["flatpak", "run", "com.google.Chrome", "http://127.0.0.1:8765"]
