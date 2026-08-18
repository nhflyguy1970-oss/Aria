"""Shared fixtures for Jarvis chat tests (isolated data dir, mocked Ollama)."""

from __future__ import annotations

import importlib.util
import os
import shutil
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

# --- Storage isolation, established BEFORE any jarvis.config import ----------
# jarvis.config binds DATA_DIR from the environment at import time
# (DATA_DIR = Path(os.getenv("JARVIS_DATA_DIR", PROJECT_ROOT / "data"))) and
# every storage path derives from it at import time too: JOURNAL_DIR,
# MEMORY_FILE, MEMORY_DB_FILE, MEMORY_VECTORS_FILE, CHAT_SETTINGS_FILE, and the
# copies other modules take (jarvis.fs, jarvis.branches, jarvis.automation.paths,
# jarvis.assistant, ...). A monkeypatch applied later cannot move a path another
# module already copied, so the redirect has to happen here — before the first
# `import jarvis.config` anywhere in the session.
#
# Assignment, not setdefault: a production JARVIS_DATA_DIR inherited from the
# launching shell or from systemd must be overridden, never honoured.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_TEST_DATA_ROOT = (_PROJECT_ROOT / "scratch" / "aria-data").resolve()

_TEST_DATA_SUBDIRS = (
    "activity",
    "journal",
    "journal/photos",
    "uploads",
    "automation_product/workflow_dags",
    "automation_product/exports",
    "platform_data/automation",
    "platform_applications",
)


# jarvis.nlu.benchmark writes its report to DATA_DIR.parent / "docs" and falls
# back to the real repository's docs/ when that directory is missing — which is
# how a test run rewrote the tracked docs/NLU_CLASSIFIER_BENCHMARK.md. This is a
# sibling of the data root, not a subdirectory of it, so it needs creating
# explicitly for the fallback never to fire.
_TEST_SIBLING_DIRS = ("docs",)


def _ensure_test_data_tree() -> None:
    _TEST_DATA_ROOT.mkdir(parents=True, exist_ok=True)
    for _sub in _TEST_DATA_SUBDIRS:
        (_TEST_DATA_ROOT / _sub).mkdir(parents=True, exist_ok=True)
    for _sib in _TEST_SIBLING_DIRS:
        (_TEST_DATA_ROOT.parent / _sib).mkdir(parents=True, exist_ok=True)


def _reset_test_data_tree() -> None:
    """Empty the isolated root so each test starts clean, as tmp_path used to.

    The root is fixed for the session (the bindings are import-time), so the
    per-test freshness has to come from clearing its contents instead.
    """
    # Never let this delete anything but the scratch root it created.
    expected = (_PROJECT_ROOT / "scratch" / "aria-data").resolve()
    assert _TEST_DATA_ROOT == expected, f"refusing to clear {_TEST_DATA_ROOT}"

    if _TEST_DATA_ROOT.is_dir():
        for entry in _TEST_DATA_ROOT.iterdir():
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                entry.unlink(missing_ok=True)
    _ensure_test_data_tree()


os.environ["JARVIS_DATA_DIR"] = str(_TEST_DATA_ROOT)

# The AI-Platform package put on sys.path above resolves its own storage roots
# from these, independently of JARVIS_DATA_DIR — aiplatform.workstation.paths
# builds automation_dir() from config "data.root", which is how tests reached
# the live /media/jeff/AI/Data/automation/timeline.jsonl. Confine those roots
# here too, for the same reason and at the same point: before first import.
os.environ["DATA_ROOT"] = str(_TEST_DATA_ROOT / "platform_data")
os.environ["APPLICATIONS_ROOT"] = str(_TEST_DATA_ROOT / "platform_applications")

_ensure_test_data_tree()

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
    config.addinivalue_line("markers", "m0a: Aria ACM promotion M0A (Memory Authority v0.15.0)")
    config.addinivalue_line(
        "markers", "m0b: Aria ACM promotion M0B (Cognitive Intent Classification v0.16.0)"
    )
    config.addinivalue_line(
        "markers", "m0c: Aria ACM promotion M0C (Cognitive Dispatch v0.17.0)"
    )
    config.addinivalue_line(
        "markers",
        "m0d: Aria ACM promotion M0D (Identity Pipeline v0.18.1 / D041+D042)",
    )
    config.addinivalue_line(
        "markers",
        "m0e: Aria ACM promotion M0E (Identity Rendering Isolation v0.18.3 / D043+D044)",
    )
    config.addinivalue_line(
        "markers",
        "m0f: Aria ACM promotion M0F (Preference Reconstruction Fix v0.18.4 / D045)",
    )
    config.addinivalue_line(
        "markers",
        "m0g: Aria ACM promotion M0G (Trusted Memory Ingestion v0.19.0 / D046)",
    )
    config.addinivalue_line(
        "markers",
        "m0h: Aria ACM promotion M0H (Legacy Memory Cleanup v0.20.0 / D047)",
    )
    config.addinivalue_line(
        "markers",
        "m0i: Aria ACM promotion M0I (Preference Certification v0.21.0)",
    )
    config.addinivalue_line(
        "markers",
        "m0j: Aria ACM promotion M0J (Teaching Recognition v0.22.0)",
    )
    config.addinivalue_line(
        "markers",
        "m0k: Aria ACM promotion M0K (multi-domain preference + evidence v0.23.0)",
    )
    config.addinivalue_line(
        "markers",
        "m0l: Aria ACM promotion M0L (memory explanation + personal summary v0.24.0+)",
    )
    config.addinivalue_line(
        "markers",
        "m1ep: Aria ACM promotion episodic autobiographical memory v0.26.0",
    )
    config.addinivalue_line("markers", "m1: Aria ACM integration milestone M1 (shadow)")
    config.addinivalue_line("markers", "m2: Aria ACM integration milestone M2 (harvest)")
    config.addinivalue_line("markers", "m3: Aria ACM integration milestone M3 (primary)")
    config.addinivalue_line("markers", "m4: Aria ACM integration milestone M4 (retire legacy)")
    config.addinivalue_line(
        "markers", "cic: Cognitive infrastructure conversion (ACM sole brain)"
    )


def _within(path: Path, root: Path) -> bool:
    resolved = Path(path).resolve()
    return resolved == root or root in resolved.parents


# Bindings that must resolve inside the isolated test root. MEMORY_VECTORS_FILE
# is the one the old per-path monkeypatch list never covered, which is how the
# vector store reached live data/memory_vectors.db during tests.
_CONFINED_BINDINGS = (
    "DATA_DIR",
    "MEMORY_VECTORS_FILE",
    "MEMORY_DB_FILE",
    "MEMORY_FILE",
    "JOURNAL_DIR",
    "CHAT_SETTINGS_FILE",
)


def _assert_storage_bindings_confined() -> None:
    """Fail closed unless jarvis.config storage bindings live under the test root.

    assert_live_write_allowed() only protects writers that call it. Checking the
    bindings themselves protects every writer, including the ones that never do.
    """
    from jarvis import config as jarvis_config
    from jarvis.live_data_guard import _LIVE_DATA_ROOT

    escaped = []
    for name in _CONFINED_BINDINGS:
        value = getattr(jarvis_config, name, None)
        if value is None:
            escaped.append(f"{name}=<missing>")
        elif not _within(Path(value), _TEST_DATA_ROOT):
            escaped.append(f"{name}={value}")

    # Sweep every other public Path binding so a newly added storage path
    # cannot silently reintroduce a live-data escape.
    for name, value in vars(jarvis_config).items():
        if name.startswith("_") or name in _CONFINED_BINDINGS:
            continue
        if isinstance(value, Path) and _within(value, _LIVE_DATA_ROOT):
            escaped.append(f"{name}={value}")

    if escaped:
        raise AssertionError(
            "Jarvis storage bindings escaped the isolated test root "
            f"{_TEST_DATA_ROOT}: " + ", ".join(sorted(escaped))
        )


@pytest.fixture(autouse=True)
def _live_data_guard():
    from jarvis.live_data_guard import disable_test_guard, enable_test_guard

    _assert_storage_bindings_confined()
    enable_test_guard()
    yield
    disable_test_guard()


@pytest.fixture(autouse=True)
def _no_api_key_in_tests(monkeypatch: pytest.MonkeyPatch):
    """Tests must not inherit live-house secrets or launch env."""
    monkeypatch.setenv("JARVIS_API_KEY", "")
    monkeypatch.delenv("JARVIS_CLOUD_LIVE_PROVIDER", raising=False)
    monkeypatch.delenv("JARVIS_CLOUD_LIVE_VOICE", raising=False)
    monkeypatch.delenv("JARVIS_BROWSER_VLM_MODEL", raising=False)
    monkeypatch.delenv("JARVIS_GRAPH_BACKEND", raising=False)
    monkeypatch.delenv("JARVIS_MEMGRAPH_AUTOSTART", raising=False)
    monkeypatch.setattr("jarvis.env_loader.load_jarvis_env", lambda *a, **k: None)
    try:
        import jarvis.gui.server as gui_server

        monkeypatch.setattr(gui_server, "load_jarvis_env", lambda *a, **k: None)
    except Exception:
        pass


@pytest.fixture(autouse=True)
def data_dir() -> Path:
    """The isolated data root every Jarvis storage binding already points at.

    JARVIS_DATA_DIR is set above at import time, so jarvis.config — and every
    module that copied a DATA_DIR-derived path at its own import — is already
    confined. The per-path monkeypatch list this fixture used to carry is
    redundant: it could only reach the bindings someone remembered to list, and
    it could not reach copies taken before it ran.
    """
    _reset_test_data_tree()
    return _TEST_DATA_ROOT


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
