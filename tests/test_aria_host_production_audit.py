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


def test_ssrf_guard_blocks_private_and_metadata():
    from jarvis.security.url_guard import is_safe_fetch_url

    assert is_safe_fetch_url("http://127.0.0.1/secret")[0] is False
    assert is_safe_fetch_url("http://10.0.0.1/")[0] is False
    assert is_safe_fetch_url("http://169.254.169.254/latest/meta-data")[0] is False
    assert is_safe_fetch_url("file:///etc/passwd")[0] is False
    assert is_safe_fetch_url("https://example.com/feed.ics")[0] is True


def test_audio_document_image_paths_confined():
    from jarvis.security.path_confine import (
        resolve_audio_library_path,
        resolve_document_library_path,
        resolve_image_library_path,
    )

    assert resolve_audio_library_path("/etc/passwd") is None
    assert resolve_document_library_path("/etc/passwd") is None
    assert resolve_image_library_path("/etc/passwd") is None


def test_browser_blocks_file_and_private_even_with_allow_risky():
    from jarvis.browser_agent import _check_url_safe

    assert _check_url_safe("file:///etc/passwd", allow_risky=True)[0] is False
    assert _check_url_safe("http://192.168.0.1/", allow_risky=False)[0] is False
    assert _check_url_safe("javascript:alert(1)", allow_risky=True)[0] is False


def test_pin_verify_uses_compare_digest():
    src = (Path(__file__).resolve().parents[1] / "jarvis" / "security" / "pin_lock.py").read_text(
        encoding="utf-8"
    )
    assert "compare_digest" in src


def test_uncensored_password_min_length_12():
    from jarvis.uncensored_auth import set_password

    try:
        set_password("short")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "12" in str(exc)


def test_acm_stats_and_export_under_primary(primary_env, tmp_path, monkeypatch):
    monkeypatch.setenv("ARIA_ACM_PERSIST_PATH", str(tmp_path / "cog.db"))
    from aria_core import acm_bridge
    from aria_core.acm_store_facade import acm_export_data, acm_stats

    acm_bridge.reset_for_tests()
    stats = acm_stats()
    assert stats is not None
    assert stats.get("backend") == "acm"
    assert "acm" in stats
    exp = acm_export_data()
    assert exp is not None
    assert exp.get("source") == "acm"
    assert "entries" in exp


def test_cognitive_reset_script_clean_check_allows_agent_schema_name():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "scripts" / "acm_cognitive_memory_reset.py"
    spec = importlib.util.spec_from_file_location("acm_cognitive_memory_reset", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod._is_clean(
        {
            "experiences": 0,
            "goals": 0,
            "associations": 0,
            "adaptations": 0,
            "concepts": 3,
            "identity_agent_attrs": [{"key": "name", "value": "aria", "active": True}],
            "identity_user_attrs": [],
            "identity_project_attrs": [],
        }
    )
    assert not mod._is_clean(
        {
            "experiences": 0,
            "goals": 0,
            "associations": 0,
            "adaptations": 0,
            "concepts": 3,
            "identity_agent_attrs": [],
            "identity_user_attrs": [{"key": "name", "value": "Jeff", "active": True}],
            "identity_project_attrs": [],
        }
    )
