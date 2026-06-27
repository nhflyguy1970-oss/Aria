"""Tests for system audit engine storage / smartctl resilience."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from jarvis.system_audit_engine import (
    BlockDevice,
    Collector,
    P3,
    _SUDO_TIMEOUT_RC,
    _block_devices,
    _completed_on_timeout,
    _run_sudo,
    _smartctl_json,
    phase_storage,
)


def test_completed_on_timeout_returns_sentinel_rc() -> None:
    exc = subprocess.TimeoutExpired(cmd=["smartctl"], timeout=8, output="partial")
    proc = _completed_on_timeout(exc, ["smartctl", "-j", "-H", "/dev/sdf"], timeout=8)
    assert proc.returncode == _SUDO_TIMEOUT_RC
    assert "timed out" in proc.stderr.lower()


def test_run_sudo_timeout_does_not_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["sudo"], timeout=3)

    monkeypatch.setattr("jarvis.system_audit_engine._run", _boom)
    monkeypatch.setattr("os.geteuid", lambda: 1)
    proc = _run_sudo(["smartctl", "-j", "-H", "/dev/sdf"], timeout=3)
    assert proc.returncode == _SUDO_TIMEOUT_RC


def test_smartctl_json_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "jarvis.system_audit_engine._run_sudo",
        lambda *a, **k: subprocess.CompletedProcess(
            args=a[0], returncode=_SUDO_TIMEOUT_RC, stdout="", stderr="timed out"
        ),
    )
    data, err = _smartctl_json("/dev/sdf", "-H", timeout=8)
    assert data == {}
    assert err == "timeout"


def test_smartctl_json_standby(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = (
        '{"smartctl":{"exit_status":2,"messages":[{"string":"Device is in Standby mode"}]},'
        '"smart_status":{"passed":true}}'
    )
    monkeypatch.setattr(
        "jarvis.system_audit_engine._run_sudo",
        lambda *a, **k: subprocess.CompletedProcess(
            args=a[0], returncode=2, stdout=payload, stderr=""
        ),
    )
    data, err = _smartctl_json("/dev/sda", "-H")
    assert err == "standby"
    assert data["smart_status"]["passed"] is True


def test_phase_storage_continues_after_smartctl_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_smartctl(dev: str, *args: str, timeout: int = 10):
        calls.append(dev)
        if dev == "/dev/sdf":
            return {}, "timeout"
        return (
            {
                "model_name": "GoodDisk",
                "smart_status": {"passed": True},
                "smartctl": {"messages": []},
            },
            None,
        )

    monkeypatch.setattr("jarvis.system_audit_engine._have", lambda name: name == "smartctl")
    monkeypatch.setattr(
        "jarvis.system_audit_engine._block_devices",
        lambda: [
            BlockDevice("/dev/sdf", "sdf", "usb", True, True),
            BlockDevice("/dev/sda", "sda", "sata", False, True),
        ],
    )
    monkeypatch.setattr("jarvis.system_audit_engine._smartctl_json", fake_smartctl)
    monkeypatch.setattr(
        "jarvis.system_audit_engine._run",
        lambda cmd, **kw: SimpleNamespace(
            stdout="Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1  100G  10G  90G  10% /\n",
            returncode=0,
        ),
    )

    c = Collector()
    phase_storage(c, sudo_smart=True)
    pid, title = P3
    phase = c.phases[pid]
    assert calls == ["/dev/sdf", "/dev/sda", "/dev/sda"]
    timeout_msgs = [w["message"] for w in phase["warn"] if "timed out" in w["message"]]
    assert any("/dev/sdf" in m and "USB/external" in m for m in timeout_msgs)
    pass_msgs = [p["message"] for p in phase["pass"]]
    assert any("SMART /dev/sda" in m and "PASSED" in m for m in pass_msgs)


def test_block_devices_parses_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    lsblk = "sdf disk 1 1 usb 1\nsda disk 0 1 sata 0\n"
    monkeypatch.setattr(
        "jarvis.system_audit_engine._run",
        lambda cmd, **kw: SimpleNamespace(stdout=lsblk, returncode=0),
    )
    devs = _block_devices()
    assert len(devs) == 2
    assert devs[0].path == "/dev/sdf"
    assert devs[0].transport == "usb"
    assert devs[0].is_external is True
    assert devs[0].smart_timeout == 8
    assert devs[1].smart_timeout == 10
