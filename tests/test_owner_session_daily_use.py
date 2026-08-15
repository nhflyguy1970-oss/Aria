"""Daily-use Owner Session: no automatic idle lock; explicit lock still revokes.

Isolated: JARVIS_DATA_DIR + OwnerSecurityService(data_dir=tmp_path).
Never writes the live workspace data/.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

MASTER = "TestMaster-Passphrase-Daily-Use-42!"


@pytest.fixture
def isol(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("JARVIS_OWNER_IDLE_SECONDS", raising=False)
    monkeypatch.delenv("JARVIS_LOCK_IDLE", raising=False)
    monkeypatch.delenv("JARVIS_LOCK_IDLE_SEC", raising=False)
    monkeypatch.setattr("jarvis.security.pin_lock.PIN_FILE", tmp_path / "pin.json")
    monkeypatch.setattr("jarvis.security.pin_lock.SESSIONS_FILE", tmp_path / "pin_sessions.json")
    from jarvis.security.owner import get_owner_security

    svc = get_owner_security(data_dir=tmp_path)
    live = Path("/media/jeff/AI/jarvis/data")
    assert Path(svc.paths["dir"]).resolve() != (live / "security" / "owner").resolve()
    return svc


def _backdate_session(svc, seconds: float) -> None:
    path = svc.sessions.path
    data = json.loads(path.read_text(encoding="utf-8"))
    for row in (data.get("sessions") or {}).values():
        row["last_active"] = time.time() - seconds
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_default_idle_is_off(isol, monkeypatch):
    from jarvis.p4_flags import lock_idle_seconds

    assert lock_idle_seconds() == 0
    st = isol.sessions.status()
    assert st["idle_seconds"] == 0
    assert st["auto_idle_lock"] is False


def test_pin_era_lock_idle_sec_does_not_enable_owner_idle(monkeypatch):
    """Live jarvis.env may still export JARVIS_LOCK_IDLE_SEC=900 from PIN-era. Ignore it."""
    monkeypatch.delenv("JARVIS_OWNER_IDLE_SECONDS", raising=False)
    monkeypatch.setenv("JARVIS_LOCK_IDLE_SEC", "900")
    monkeypatch.setenv("JARVIS_LOCK_IDLE", "900")
    from jarvis.p4_flags import lock_idle_seconds

    assert lock_idle_seconds() == 0


def test_unlocked_session_survives_elapsed_time_when_idle_off(isol):
    isol.setup(MASTER)
    isol.acknowledge_recovery(stored=True)
    token = isol.unlock(MASTER)["session_token"]
    _backdate_session(isol, 10_000)
    assert isol.sessions.session_valid(token) is True
    assert isol.sessions.touch(token) is True
    house = isol.house_lock_status()
    assert house["locked"] is False
    assert house["owner_unlocked"] is True
    assert house["auto_idle_lock"] is False


def test_opt_in_idle_still_expires_when_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("JARVIS_OWNER_IDLE_SECONDS", "2")
    from jarvis.security.owner.session import OwnerSessionManager

    mgr = OwnerSessionManager(tmp_path / "sessions.json", idle_seconds=2)
    token = mgr.mark_unlocked()
    assert mgr.session_valid(token) is True
    data = json.loads(mgr.path.read_text(encoding="utf-8"))
    for row in data["sessions"].values():
        row["last_active"] = time.time() - 30
    mgr.path.write_text(json.dumps(data), encoding="utf-8")
    assert mgr.session_valid(token) is False


def test_explicit_hard_lock_revokes_vault_and_capabilities(isol):
    isol.setup(MASTER)
    isol.acknowledge_recovery(stored=True)
    isol.step_up(master_password=MASTER)
    auth = isol.authorize("journal.export", room="journal")
    handle = auth.get("capability_handle")
    assert isol.vault.is_unlocked() is True

    t0 = time.perf_counter()
    out = isol.lock(hard=True)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert out["ok"] is True
    assert out["mode"] == "hard"
    assert isol.vault.is_unlocked() is False
    assert isol.status()["owner_unlocked"] is False
    assert isol.house_lock_status()["locked"] is True
    if handle:
        assert isol.sessions.handles.valid(handle, capability="journal.export") is False
    denied = isol.authorize("vault.secret.use", room="integrations")
    assert denied.get("ok") is False
    assert elapsed_ms < 2000


def test_new_process_starts_locked(isol):
    isol.setup(MASTER)
    isol.acknowledge_recovery(stored=True)
    from jarvis.security.owner.service import OwnerSecurityService

    restarted = OwnerSecurityService(isol.paths["dir"].parent.parent)
    assert restarted.vault.exists() is True
    assert restarted.vault.is_unlocked() is False
    assert restarted.status()["owner_unlocked"] is False
    assert restarted.house_lock_status()["locked"] is True


def test_frontend_has_no_default_900s_idle_and_has_lock_control():
    root = Path("/media/jeff/AI/jarvis/jarvis/gui/static")
    lock_js = (root / "lock_screen.js").read_text(encoding="utf-8")
    door_js = (root / "workspace" / "front_door.js").read_text(encoding="utf-8")
    assert "idle_seconds || 900" not in lock_js
    assert "function idleSecondsFromStatus" in lock_js
    assert "window.jarvisLockHouse" in lock_js
    assert "Aria is locked. Enter your Aria Master Password to unlock the house." in lock_js
    assert 'id="fdLockAria"' in door_js
    assert "Lock Aria" in door_js
