"""Tray right-click menu, its actions, single-instance lock and login autostart."""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
import threading
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from jarvis import tray_actions as actions

REPO = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ fake pystray


class _Item:
    def __init__(self, text, action=None, default=False, enabled=True, **_):
        self._text, self.action, self.default, self._enabled = text, action, default, enabled

    @property
    def text(self):
        return self._text(self) if callable(self._text) else self._text

    @property
    def enabled(self):
        return self._enabled(self) if callable(self._enabled) else self._enabled

    @property
    def submenu(self):
        return self.action if isinstance(self.action, _Menu) else None


class _Menu:
    SEPARATOR = _Item("-")

    def __init__(self, *items):
        self.items = items


class _Icon:
    last = None

    def __init__(self, name, image, title, menu):
        self.menu, self.notes, self.stopped = menu, [], False
        _Icon.last = self

    def notify(self, message, title=None):
        self.notes.append(message)

    def update_menu(self):
        pass

    def run(self):
        pass

    def stop(self):
        self.stopped = True


@pytest.fixture
def tray(monkeypatch):
    fake = types.ModuleType("pystray")
    fake.Menu, fake.MenuItem, fake.Icon = _Menu, _Item, _Icon
    monkeypatch.setitem(sys.modules, "pystray", fake)
    from jarvis import tray as tray_mod

    monkeypatch.setattr(tray_mod, "enable_system_gi", lambda: False)
    monkeypatch.setattr(tray_mod, "_create_icon_image", lambda: None)
    monkeypatch.setattr(actions, "snapshot", lambda url: actions.Snapshot(server=True, backend=True))
    return tray_mod


def _items(menu):
    return [i for i in menu.items if i.text != "-"]


def _find(menu, text):
    return next(i for i in _items(menu) if i.text == text)


def _run_action(item):
    before = set(threading.enumerate())
    item.action(_Icon.last, item)
    for t in set(threading.enumerate()) - before:
        t.join(timeout=10)


def test_menu_has_every_requested_entry(tray):
    tray.run_tray_app("http://127.0.0.1:8765")
    texts = [i.text for i in _items(_Icon.last.menu)]
    for expected in ("Open ARIA", "Status: running", "Start ARIA", "Stop ARIA", "Restart ARIA",
                     "Restart AI Backend", "Logs", "Settings", "Quit Tray"):
        assert expected in texts, texts
    logs = [i.text for i in _find(_Icon.last.menu, "Logs").submenu.items]
    assert logs == ["Open logs folder", "Server log (recent)", "Tray log"]


def test_start_disabled_while_running_and_stop_enabled(tray):
    tray.run_tray_app("http://127.0.0.1:8765")
    menu = _Icon.last.menu
    assert not _find(menu, "Start ARIA").enabled
    assert _find(menu, "Stop ARIA").enabled and _find(menu, "Restart ARIA").enabled


def test_stop_fences_watchdog_before_stopping_server(tray):
    calls: list[str] = []
    with patch("jarvis.tray_actions.stop_aria", lambda: (calls.append("stop"), (True, "stopped"))[1]):
        tray.run_tray_app("http://127.0.0.1:8765", on_stop=lambda: calls.append("watchdog-off"),
                          on_start=lambda: calls.append("watchdog-on"))
        _run_action(_find(_Icon.last.menu, "Stop ARIA"))
    assert calls == ["watchdog-off", "stop"]


def test_failed_stop_turns_watchdog_back_on(tray):
    calls: list[str] = []
    with patch("jarvis.tray_actions.stop_aria", lambda: (False, "systemctl stop failed")):
        tray.run_tray_app("http://127.0.0.1:8765", on_stop=lambda: calls.append("off"),
                          on_start=lambda: calls.append("on"))
        _run_action(_find(_Icon.last.menu, "Stop ARIA"))
    assert calls == ["off", "on"]
    assert "systemctl stop failed" in _Icon.last.notes


def test_quit_tray_is_not_a_complete_quit(tray):
    seen = {}
    tray.run_tray_app("http://127.0.0.1:8765", on_quit=lambda complete: seen.update(complete=complete))
    _run_action(_find(_Icon.last.menu, "Quit Tray"))
    assert seen == {"complete": False} and _Icon.last.stopped


# ------------------------------------------------------------------ actions


@pytest.mark.parametrize("sched,expected", [
    (None, ""),
    ({"shared_active": 0, "heavy_active": None, "waiting": 0}, ""),
    ({"shared_active": 1}, "a reply is being generated"),
    ({"heavy_active": "jarvis_edit"}, "GPU job running (jarvis_edit)"),
    ({"waiting": 2}, "jobs are queued for the GPU"),
])
def test_busy_reason(sched, expected):
    assert actions.busy_reason(sched) == expected


def test_backend_restart_refuses_while_busy():
    with patch.object(actions, "_get_json", return_value={"shared_active": 1}), \
         patch.object(actions, "_run") as run:
        ok, message = actions.restart_ai_backend("http://x")
    assert not ok and "reply is being generated" in message
    run.assert_not_called()


def test_backend_restart_touches_only_aria_units():
    ran: list[list[str]] = []

    def fake_run(cmd, timeout):
        ran.append(cmd)
        out = "active\n" if cmd[-2:] == ["is-active", "aria-vulkan-helper.service"] else ""
        return subprocess.CompletedProcess(cmd, 0, out, "")

    with patch.object(actions, "_get_json", return_value={"shared_active": 0}), \
         patch.object(actions, "_run", fake_run), patch.object(actions, "_wait_backend", return_value=True):
        ok, message = actions.restart_ai_backend("http://x")
    assert ok, message
    assert ["systemctl", "restart", "ollama.service"] in ran
    assert ["systemctl", "--user", "restart", "aria-vulkan-helper.service"] in ran
    flat = " ".join(" ".join(c) for c in ran)
    assert "ftr-" not in flat and "11435" not in flat and "11436" not in flat


def test_backend_restart_reports_cancelled_authorization():
    def fake_run(cmd, timeout):
        return subprocess.CompletedProcess(cmd, 1, "", "Failed to restart ollama.service: Access denied")

    with patch.object(actions, "_get_json", return_value=None), patch.object(actions, "_run", fake_run):
        ok, message = actions.restart_ai_backend("http://x")
    assert not ok and "Access denied" in message


def test_snapshot_labels():
    assert actions.Snapshot().label == "Status: stopped"
    assert actions.Snapshot(server=True).label == "Status: running — AI backend offline"
    assert actions.Snapshot(server=True, backend=True, busy="x").label == "Status: running — x"


# ------------------------------------------------------------------ single instance


def test_second_tray_cannot_take_the_lock(tmp_path):
    script = textwrap.dedent(f"""
        import os, sys
        sys.path.insert(0, {str(REPO)!r})
        os.environ["JARVIS_DATA_DIR"] = {str(tmp_path)!r}
        from jarvis import daemon
        print(daemon._acquire_tray_lock(), flush=True)
        sys.stdin.readline()
    """)
    env = {**os.environ, "JARVIS_DATA_DIR": str(tmp_path)}
    first = subprocess.Popen([sys.executable, "-c", script], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, text=True, env=env)
    try:
        assert first.stdout.readline().strip() == "True"
        second = subprocess.run([sys.executable, "-c", script], input="\n", capture_output=True,
                                text=True, env=env, timeout=120)
        assert second.stdout.strip() == "False", second.stderr[-400:]
    finally:
        first.communicate("\n", timeout=60)


# ------------------------------------------------------------------ login autostart


def test_autostart_unit(tmp_path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "systemctl.log"
    (bindir / "systemctl").write_text(f"#!/bin/sh\necho \"$@\" >> {log}\n")
    (bindir / "systemctl").chmod(0o755)
    env = {**os.environ, "HOME": str(tmp_path), "PATH": f"{bindir}:{os.environ['PATH']}"}
    subprocess.run(["bash", str(REPO / "scripts/install-tray-autostart.sh")], env=env, check=True,
                   capture_output=True, timeout=30)
    unit = (tmp_path / ".config/systemd/user/aria-tray.service").read_text()
    assert "WantedBy=graphical-session.target" in unit
    assert "PartOf=graphical-session.target" in unit
    assert "Restart=on-failure" in unit  # Quit exits 0 and stays quit
    assert "Wants=jarvis.service" in unit and "Requires=" not in unit and "BindsTo=" not in unit
    assert f"ExecStart={REPO}/scripts/aria-tray.sh" in unit
    assert "enable aria-tray.service" in log.read_text()


def test_launch_lib_starts_tray_unit_when_installed(tmp_path):
    unit_dir = tmp_path / ".config/systemd/user"
    unit_dir.mkdir(parents=True)
    (unit_dir / "aria-tray.service").write_text("[Unit]\n")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "systemctl.log"
    (bindir / "systemctl").write_text(f"#!/bin/sh\necho \"$@\" >> {log}\n")
    (bindir / "systemctl").chmod(0o755)
    (bindir / "pgrep").write_text("#!/bin/sh\nexit 1\n")
    (bindir / "pgrep").chmod(0o755)
    script = (f'source "{REPO}/scripts/_jarvis-launch-lib.sh"; jarvis_tray_available() {{ return 0; }}; '
              f'LOG_FILE={tmp_path}/l.log; jarvis_start_tray_background')
    env = {**os.environ, "HOME": str(tmp_path), "PATH": f"{bindir}:{os.environ['PATH']}",
           "JARVIS_ROOT": str(REPO)}
    subprocess.run(["bash", "-c", script], env=env, check=True, capture_output=True, timeout=30)
    assert "--user start aria-tray.service" in log.read_text()
