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


def test_primary_import_routes_via_add_arg_order(primary_env, tmp_path):
    """Regression: import_data must call add(entry_type, content), not swapped kwargs."""
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(tmp_path / "imp.json")
    n = store.import_data(
        {
            "entries": [
                {"type": "fact", "content": "My favorite zerotrust marker is aurora."},
            ]
        }
    )
    assert n == 1
    assert len(store._data.get("entries") or []) == 0  # no legacy SoT under PRIMARY


def test_primary_prune_and_clear_are_noops(primary_env, tmp_path):
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(tmp_path / "p.json")
    store._data["entries"] = [
        {
            "id": "x1",
            "type": "auto",
            "content": "stale",
            "tags": [],
            "namespace": "default",
            "timestamp": "2000-01-01T00:00:00+00:00",
            "access_count": 0,
            "relevance": 0.01,
        }
    ]
    assert store.prune(max_age_days=1, min_score=0.9) == 0
    assert len(store._data["entries"]) == 1
    assert store.clear() == 0
    assert len(store._data["entries"]) == 1


def test_skill_exec_defaults_to_no_shell():
    src = (Path(__file__).resolve().parents[1] / "jarvis" / "skill_database.py").read_text(
        encoding="utf-8"
    )
    assert "JARVIS_SKILL_SHELL" in src
    assert "shell=False" in src


def test_claude_dangerous_requires_env_opt_in():
    src = (Path(__file__).resolve().parents[1] / "jarvis" / "tools" / "runner.py").read_text(
        encoding="utf-8"
    )
    assert "JARVIS_ALLOW_DANGEROUS_TOOLS" in src
    assert "--dangerously-skip-permissions" in src


def test_video_paths_are_confined():
    from jarvis.video_ops import resolve_storyboard_image, resolve_video_path

    assert resolve_video_path("/etc/passwd") is None
    assert resolve_storyboard_image("/etc/passwd") is None


def test_automation_secret_rejects_query_only(monkeypatch):
    monkeypatch.setenv("JARVIS_AUTOMATION_SECRET", "test-secret-value-xyz")
    from jarvis.home_assistant import verify_automation_secret

    assert verify_automation_secret(None, "test-secret-value-xyz") is False
    assert verify_automation_secret("test-secret-value-xyz", None) is True
    assert verify_automation_secret("wrong", None) is False


def test_tools_cwd_must_be_under_project_or_data(tmp_path, monkeypatch):
    from jarvis.config import PROJECT_ROOT
    from jarvis.tools.runner import build_command

    monkeypatch.setattr("shutil.which", lambda _n: "/usr/bin/claude")
    outside = tmp_path / "outside"
    outside.mkdir()
    built = build_command(
        "claude_code",
        {"task": "hi", "cwd": str(outside)},
    )
    assert built is None
    built_ok = build_command(
        "claude_code",
        {"task": "hi", "cwd": str(PROJECT_ROOT)},
    )
    assert built_ok is not None


def test_upsert_checkpoint_primary_does_not_delete_legacy(primary_env, tmp_path):
    from jarvis.modules.memory import MemoryStore

    store = MemoryStore(tmp_path / "cp.json")
    store._data["entries"] = [
        {
            "id": "legacy-cp",
            "type": "project",
            "content": "old checkpoint",
            "tags": ["checkpoint", "project-state"],
            "namespace": "default",
            "timestamp": "2000-01-01T00:00:00+00:00",
            "access_count": 0,
            "relevance": 1.0,
        }
    ]
    store.upsert_checkpoint("new checkpoint state")
    assert any(e["id"] == "legacy-cp" for e in store._data["entries"])
