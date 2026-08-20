"""Live certification: a deliberate refusal must not look like a crash.

Live memory declines test/cert payloads on purpose. The create route caught
ValueError but not ProductionIsolationError, so that refusal reached the user
as a bare 500 "Server error" with the reason hidden.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from jarvis.production_guard import ProductionIsolationError


@pytest.fixture
def memory_app(data_dir):
    from jarvis.extensions.memory.api import register_routes

    assistant = MagicMock()
    app = FastAPI()
    register_routes(app, assistant)
    return app, assistant


def test_a_refused_payload_is_a_bad_request_not_a_server_error(memory_app):
    app, assistant = memory_app
    assistant.memory.add.side_effect = ProductionIsolationError(
        "ACM authoritative: legacy MemoryStore write refused"
    )
    client = TestClient(app, raise_server_exceptions=False)

    r = client.post("/api/memory", json={"content": "cert probe", "type": "fact"})

    assert r.status_code == 400, f"a refusal became {r.status_code}"
    body = r.json()
    assert body["ok"] is False
    assert "refused" in body["error"], body
    assert body["refused"] == "production_isolation"


def test_a_validation_error_is_still_a_bad_request(memory_app):
    app, assistant = memory_app
    assistant.memory.add.side_effect = ValueError("Empty memory content")
    client = TestClient(app, raise_server_exceptions=False)

    r = client.post("/api/memory", json={"content": "x", "type": "fact"})
    assert r.status_code == 400
    assert "Empty memory content" in r.json()["error"]


def test_empty_content_is_rejected_before_any_write(memory_app):
    app, assistant = memory_app
    client = TestClient(app, raise_server_exceptions=False)

    r = client.post("/api/memory", json={"content": "   "})
    assert r.status_code == 400
    assistant.memory.add.assert_not_called()


def test_the_store_raises_a_refusal_not_a_bare_runtime_error(data_dir, monkeypatch):
    """The store re-raised a plain RuntimeError with the real class name only in
    the message text, so a route could not tell a refusal from a malfunction."""
    import inspect

    from jarvis.modules import memory as legacy_memory
    from jarvis.modules import memory_sqlite

    for module in (memory_sqlite.SqliteMemoryStore, legacy_memory.JsonMemoryStore):
        src = inspect.getsource(module.add)
        assert "ProductionIsolationError(" in src, f"{module.__name__} still raises a bare error"
        assert 'raise RuntimeError(\n                        f"ACM authoritative' not in src


def test_a_refusal_is_still_a_runtime_error_for_existing_callers():
    """Callers that catch RuntimeError must keep working."""
    assert issubclass(ProductionIsolationError, RuntimeError)
