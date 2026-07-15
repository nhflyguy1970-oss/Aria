"""Shared fixtures for Jarvis chat tests (isolated data dir, mocked Ollama)."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_PLATFORM_ROOT = Path(__file__).resolve().parents[2] / "AI-Platform"
if _PLATFORM_ROOT.is_dir() and str(_PLATFORM_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLATFORM_ROOT))


def _install_aiplatform_stub() -> None:
    """Allow Mission Control unit tests to patch aiplatform on runners without the private repo."""
    if importlib.util.find_spec("aiplatform") is not None:
        return
    aggregator = types.ModuleType("aiplatform.mission_control.aggregator")
    activity = types.ModuleType("aiplatform.mission_control.activity")
    mission_control = types.ModuleType("aiplatform.mission_control")
    aiplatform = types.ModuleType("aiplatform")
    mission_control.aggregator = aggregator
    mission_control.activity = activity
    aiplatform.mission_control = mission_control
    for name, mod in (
        ("aiplatform", aiplatform),
        ("aiplatform.mission_control", mission_control),
        ("aiplatform.mission_control.aggregator", aggregator),
        ("aiplatform.mission_control.activity", activity),
    ):
        sys.modules[name] = mod


_install_aiplatform_stub()

# Tests import jarvis.llm which pulls ollama at import time.
if "ollama" not in sys.modules:
    _ollama = MagicMock()
    _ollama.chat = MagicMock(return_value={"message": {"content": ""}})
    _ollama.embed = MagicMock(return_value={"embeddings": [[0.0]]})
    _ollama.generate = MagicMock(return_value={"response": ""})
    sys.modules["ollama"] = _ollama


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "network: requires outbound network access")
    config.addinivalue_line("markers", "workstation: requires local workstation services")
    config.addinivalue_line("markers", "integration: integration tests (optional services)")
    config.addinivalue_line("markers", "gpu: requires GPU/CUDA")
    config.addinivalue_line("markers", "m0: Aria ACM integration milestone M0 (vendoring)")
    config.addinivalue_line("markers", "m1: Aria ACM integration milestone M1 (shadow)")
    config.addinivalue_line("markers", "m2: Aria ACM integration milestone M2 (harvest)")
    config.addinivalue_line("markers", "m3: Aria ACM integration milestone M3 (primary)")
    config.addinivalue_line("markers", "m4: Aria ACM integration milestone M4 (retire legacy)")


@pytest.fixture(autouse=True)
def _live_data_guard():
    from jarvis.live_data_guard import disable_test_guard, enable_test_guard

    enable_test_guard()
    yield
    disable_test_guard()


@pytest.fixture(autouse=True)
def _no_api_key_in_tests(monkeypatch: pytest.MonkeyPatch):
    """Tests must not inherit JARVIS_API_KEY from the user's jarvis.env."""
    monkeypatch.setenv("JARVIS_API_KEY", "")
    monkeypatch.setattr("jarvis.env_loader.load_jarvis_env", lambda *a, **k: None)
    try:
        import jarvis.gui.server as gui_server

        monkeypatch.setattr(gui_server, "load_jarvis_env", lambda *a, **k: None)
    except Exception:
        pass


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point Jarvis data files at a temp directory."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    journal_dir = tmp_path / "journal"
    journal_dir.mkdir(exist_ok=True)
    patches = {
        "jarvis.config.DATA_DIR": tmp_path,
        "jarvis.config.JOURNAL_DIR": journal_dir,
        "jarvis.fs.DATA_DIR": tmp_path,
        "jarvis.config.MEMORY_FILE": tmp_path / "memory.json",
        "jarvis.config.MEMORY_DB_FILE": tmp_path / "memory.db",
        "jarvis.config.CHAT_SETTINGS_FILE": tmp_path / "chat_settings.json",
        "jarvis.branches.DATA_DIR": tmp_path,
        "jarvis.branches.BRANCHES_FILE": tmp_path / "chat_branches.json",
        "jarvis.modules.memory.DATA_DIR": tmp_path,
        "jarvis.modules.memory.jarvis_config.MEMORY_FILE": tmp_path / "memory.json",
        "jarvis.modules.memory.jarvis_config.MEMORY_DB_FILE": tmp_path / "memory.db",
        "jarvis.modules.journal.JOURNAL_DIR": journal_dir,
        "jarvis.modules.journal.JOURNAL_FILE": journal_dir / "bullet_journal.json",
        "jarvis.modules.journal.JOURNAL_PHOTOS_DIR": journal_dir / "photos",
        "jarvis.coding_tasks.TASKS_FILE": tmp_path / "coding_tasks.json",
        "jarvis.proposal_store.PROPOSALS_FILE": tmp_path / "pending_proposals.json",
        "jarvis.action_log.LOG_FILE": tmp_path / "action_log.json",
        "jarvis.assistant.DATA_DIR": tmp_path,
        "jarvis.assistant.UPLOAD_DIR": tmp_path / "uploads",
    }
    for target, value in patches.items():
        monkeypatch.setattr(target, value)
    (tmp_path / "uploads").mkdir(exist_ok=True)
    return tmp_path


@pytest.fixture
def mock_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "jarvis.ollama_health.check_ollama",
        lambda: {"running": True, "models": ["qwen2.5:14b", "nomic-embed-text"]},
    )


@pytest.fixture
def mock_proposals(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("jarvis.proposal_store.load", lambda: {})


@pytest.fixture
def mock_router_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip tool router + JSON router LLM calls in tests."""
    monkeypatch.setattr("jarvis.llm.route_with_tools", lambda *a, **k: None)
    monkeypatch.setattr(
        "jarvis.llm.ask",
        lambda *a, **k: '{"action": "chat", "params": {}}',
    )


@pytest.fixture
def assistant(data_dir: Path, mock_ollama, mock_proposals, mock_router_llm):
    from jarvis.assistant import JarvisAssistant

    return JarvisAssistant()


@pytest.fixture
def chat_app(assistant, data_dir, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from jarvis.gui import extra_routes

    monkeypatch.setattr("jarvis.gui.extra_routes.DATA_DIR", data_dir)

    app = FastAPI()
    extra_routes.register_routes(app, assistant)

    @app.get("/api/jobs")
    def _jobs_center():
        from jarvis.jobs_center import snapshot

        return snapshot()

    @app.get("/api/debug/bundle")
    def _debug_bundle():
        from jarvis.debug_bundle import collect

        return collect()

    @app.get("/api/registry/actions")
    def _actions_registry():
        from jarvis.handlers import ensure_handlers_loaded
        from jarvis.handlers.registry import all_actions

        ensure_handlers_loaded()
        return {"ok": True, "actions": all_actions()}

    @app.get("/api/registry/router/rules")
    def _router_rules():
        from jarvis.router_table import list_rules

        return {"ok": True, "rules": list_rules()}

    client = TestClient(app)
    client.assistant = assistant
    return client
