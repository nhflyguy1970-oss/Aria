"""Aria host production-readiness certifications (permanent).

Locks fail-closed PRIMARY memory writes, LAN auth policy, PinLock registration,
and auto-memory provenance stamping.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def primary_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("ARIA_ACM_PRIMARY", "1")
    monkeypatch.setenv("ARIA_ACM_ROLLBACK", "0")
    monkeypatch.setenv("ARIA_ACM_AUTO_PERSIST", "0")
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "cog.db"))
    monkeypatch.setenv("ARIA_TEACHING_DEBUG", "0")
    from aria_core import acm_bridge, memory_manager

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
    yield
    acm_bridge.reset_for_tests()
    memory_manager.reset_for_tests()


def test_primary_memory_add_fail_closed_on_redirect_error(primary_env, monkeypatch, tmp_path):
    from jarvis.modules.memory import MemoryStore

    def boom(*_a, **_k):
        raise RuntimeError("encode_down")

    monkeypatch.setattr(
        "aria_core.acm_bridge.redirect_legacy_write_to_acm",
        boom,
    )
    store = MemoryStore(tmp_path / "legacy.json")
    with pytest.raises(RuntimeError, match="legacy MemoryStore write refused"):
        store.add("fact", "My favorite color is blue.")
    assert len(store._data.get("entries") or []) == 0


def test_auto_memory_uses_statement_provenance(primary_env):
    from aria_acm.acm.provenance import MessageRole
    from aria_core import acm_bridge

    host = acm_bridge.primary_remember(
        "User often drinks tea at dawn.",
        entry_type="auto",
        tags=["auto-extracted"],
    )
    assert host.get("encoded") or host.get("id")
    eng = acm_bridge.get_engine()
    roles = [p.message_role for p in eng.store.provenance.values()]
    assert MessageRole.USER_STATEMENT in roles or any(
        getattr(r, "value", r) == "user_statement" for r in roles
    )


def test_pin_lock_middleware_registered_in_server_source():
    src = (Path(__file__).resolve().parents[1] / "jarvis" / "gui" / "server.py").read_text(
        encoding="utf-8"
    )
    assert "PinLockMiddleware" in src
    assert "app.add_middleware(PinLockMiddleware)" in src


def test_lan_bind_requires_api_key(monkeypatch):
    monkeypatch.delenv("JARVIS_API_KEY", raising=False)
    monkeypatch.delenv("JARVIS_ALLOW_INSECURE_LAN", raising=False)
    from jarvis.lan import require_api_key_for_lan_bind

    with pytest.raises(SystemExit, match="JARVIS_API_KEY"):
        require_api_key_for_lan_bind("0.0.0.0")
    # loopback is fine without key
    require_api_key_for_lan_bind("127.0.0.1")
